"""
Escritura del mundo simulado en la base de datos (generador-sintetico-ml §2).

Escribe vía ORM, pero los datos pasan las mismas reglas que los reales:

- Cada registro se valida con el esquema Pydantic de su endpoint (rangos,
  fechas no futuras, campos por etapa, `other_detail`…).
- Las reglas de dominio se toman de los servicios transversales: la
  numeración de ciclos y pasadas (`numbering`), el balance de masas
  (`mass_balance`) y el puente al inventario (`inventory_bridge`).

Solo se escribe lo que el caficultor **registró**: lo no registrado existe
en el mundo (y en la auditoría) pero no en la base.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.farm_operations.api.v1.alert_configs.schema import AlertConfigValues
from app.farm_operations.api.v1.climate_records.schema import ClimateRecordCreate
from app.farm_operations.api.v1.crop_cycles.schema import CycleCloseRequest, CycleCreate
from app.farm_operations.api.v1.day_labors.schema import DayLaborFields
from app.farm_operations.api.v1.dryings.schema import DryingCompleteRequest, DryingCreate, HumidityCheckCreate
from app.farm_operations.api.v1.employees.schema import EmployeeCreate
from app.farm_operations.api.v1.farms.schema import FarmCreate
from app.farm_operations.api.v1.harvests.schema import HarvestCloseRequest, HarvestCreate, HarvestWorkFields
from app.farm_operations.api.v1.labors.schema import (
    CulturalPracticeCreate,
    FertilizationCreate,
    FloweringCreate,
    IrrigationCreate,
    PestMonitoringCreate,
    PhytosanitaryCreate,
)
from app.farm_operations.api.v1.plots.schema import PlotCloseRequest, PlotCreate, PlotEventCreate
from app.farm_operations.api.v1.quality_evals.schema import QualityEvalCreate
from app.farm_operations.api.v1.soil_analyses.schema import SoilAnalysisCreate
from app.farm_operations.api.v1.supplies.schema import SupplyCreate
from app.farm_operations.api.v1.wet_processings.schema import WetCompleteRequest, WetProcessingCreate
from app.farm_operations.models import (
    AlertConfig,
    ClimateRecord,
    CropCycle,
    CulturalPractice,
    DayLabor,
    Drying,
    DryingHumidityCheck,
    DryingInput,
    Employee,
    Farm,
    Fertilization,
    FloweringRecord,
    Harvest,
    HarvestWork,
    Irrigation,
    PestMonitoring,
    PhytosanitaryApp,
    Plot,
    PlotEvent,
    QualityEval,
    SoilAnalysis,
    Supply,
    WetProcessing,
    WetProcessingInput,
)
from app.farm_operations.models.enums import (
    CycleStatusEnum,
    DryingStatusEnum,
    HarvestStatusEnum,
    PlotStatusEnum,
    WetProcessingStatusEnum,
)
from app.farm_operations.services.inventory_bridge import send_to_inventory
from app.farm_operations.services.mass_balance import check_harvest_inputs, check_harvest_total, check_wet_inputs
from app.farm_operations.services.numbering import next_cycle_number, next_pass_number
from app.models.farmer import Farmer
from app.models.inventory_movement import InventoryMovement
from app.models.person import Person
from scripts.farm_ml import catalogs
from scripts.farm_ml.world import (
    DryingSim,
    FarmSim,
    HarvestSim,
    PlotSim,
    QualitySim,
    WetSim,
    World,
    at,
)

# Marca del caficultor dueño de todo lo sintético (§2): `--wipe` borra por ella
MARKER = "SYNTHETIC_ML_DATA"
CENT = Decimal("0.01")

LABOR_KINDS = {
    "fertilization": (Fertilization, FertilizationCreate, "application_date"),
    "phytosanitary": (PhytosanitaryApp, PhytosanitaryCreate, "application_date"),
    "irrigation": (Irrigation, IrrigationCreate, "irrigation_date"),
    "pest_monitoring": (PestMonitoring, PestMonitoringCreate, "monitoring_date"),
    "cultural_practice": (CulturalPractice, CulturalPracticeCreate, "practice_date"),
    "flowering": (FloweringRecord, FloweringCreate, "flowering_date"),
}


def dec(value: Optional[float], places: int) -> Optional[Decimal]:
    if value is None:
        return None
    return Decimal(str(round(value, places)))


def stamp(obj, day: date, hour: float = 18.0):
    """Fecha de creación verosímil: el día del registro, no el de la generación."""
    obj.created_at = at(day, hour)
    return obj


@dataclass
class Persisted:
    """Objetos escritos, para la validación y la auditoría."""

    farms: dict = field(default_factory=dict)      # clave de finca → Farm
    dryings: dict = field(default_factory=dict)    # clave de secado → Drying
    harvests: dict = field(default_factory=dict)   # id(HarvestSim) → Harvest
    counts: dict = field(default_factory=dict)

    def count(self, name: str, n: int = 1) -> None:
        self.counts[name] = self.counts.get(name, 0) + n


def synthetic_farmer(db: Session) -> Optional[Farmer]:
    return (
        db.query(Farmer)
        .join(Person, Farmer.person_id == Person.id)
        .filter(Person.observation == MARKER)
        .first()
    )


class Persister:
    def __init__(self, db: Session, world: World):
        self.db = db
        self.world = world
        self.end = world.params.end_date
        self.out = Persisted()
        self.supplies: dict[str, Supply] = {}

    # ── Entrada ───────────────────────────────────────────────────────────

    def run(self, log=None) -> Persisted:
        """Escribe el mundo finca por finca; `log(mensaje)` recibe el avance."""
        log = log or (lambda message: None)
        self.farmer = self.create_farmer()
        self.load_supplies()
        total = len(self.world.farms)
        for index, farm in enumerate(self.world.farms, start=1):
            before = sum(self.out.counts.values())
            self.persist_farm(farm)
            self.db.commit()
            written = sum(self.out.counts.values()) - before
            log(f"[{index}/{total}] {farm.name}: {written:,} registros".replace(",", "."))
        return self.out

    def create_farmer(self) -> Farmer:
        person = Person(full_name="Caficultor sintético", observation=MARKER)
        farmer = Farmer(person=person, farm_name="Fincas sintéticas", village="Varias", municipality="Varios")
        self.db.add(farmer)
        self.db.flush()
        return farmer

    def load_supplies(self) -> None:
        """Catálogo global (D7): se reutiliza el insumo si ya existe con ese nombre y tipo."""
        for key, info in catalogs.SUPPLIES.items():
            SupplyCreate(name=info.name, supply_type=info.supply_type, unit=info.unit, composition=info.composition)
            supply = (
                self.db.query(Supply)
                .filter(Supply.name == info.name, Supply.supply_type == info.supply_type)
                .first()
            )
            if supply is None:
                supply = Supply(name=info.name, supply_type=info.supply_type, unit=info.unit, composition=info.composition)
                self.db.add(supply)
                self.db.flush()
                self.out.count("supplies_created")
            self.supplies[key] = supply

    # ── Finca ─────────────────────────────────────────────────────────────

    def persist_farm(self, sim: FarmSim) -> None:
        db = self.db
        payload = {
            "farmer_id": self.farmer.id, "name": sim.name, "village": sim.village,
            "municipality": sim.municipality.name, "altitude": sim.altitude, "total_area": sim.total_area,
            "latitude": sim.latitude, "longitude": sim.longitude,
            "observations": "Finca sintética para desarrollo y entrenamiento del modelo: no es una finca real.",
        }
        data = FarmCreate.model_validate(payload)
        farm = stamp(Farm(**data.model_dump()), self.world.params.window_start, 9)
        db.add(farm)
        db.flush()
        self.out.farms[sim.key] = farm
        self.out.count("farms")
        if sim.alert_config:
            values = AlertConfigValues.model_validate(sim.alert_config).model_dump()
            db.add(AlertConfig(farm_id=farm.id, **values))

        self.employees = {}
        for employee in sim.employees:
            data = EmployeeCreate(farm_id=farm.id, full_name=employee.full_name)
            self.employees[employee.key] = stamp(
                Employee(farm_id=farm.id, full_name=data.full_name, active=employee.active),
                self.world.params.window_start, 10,
            )
        db.add_all(self.employees.values())
        self.out.count("employees", len(self.employees))

        self.plots: dict[str, Plot] = {}
        self.farm_harvests: list[Harvest] = []
        for plot in sim.plots:
            self.persist_plot(farm, plot)
        self.persist_climate(farm, sim)
        self.persist_processing(farm, sim)
        self.persist_day_labors(sim)

        # El total de cada cosecha cerrada cubre lo que se benefició (mass_balance)
        for harvest in self.farm_harvests:
            if harvest.status == HarvestStatusEnum.closed:
                check_harvest_total(db, harvest, harvest.total_cherry_kg)

    # ── Lote, ciclos, labores y cosechas ──────────────────────────────────

    def persist_plot(self, farm: Farm, sim: PlotSim) -> None:
        db = self.db
        renewed_from = self.plots[sim.renewed_from.key].id if sim.renewed_from else None
        payload = {
            "farm_id": farm.id, "name": sim.name, "renewed_from_plot_id": renewed_from,
            "area": sim.area, "slope": sim.slope, "soil_type": sim.soil_type, "variety": sim.variety,
            "planting_date": sim.planting_date, "seedling_count": sim.trees,
            "row_spacing_m": sim.row_spacing, "plant_spacing_m": sim.plant_spacing,
            "shade_type": sim.shade_type, "seed_origin_place": sim.seed_origin,
        }
        data = PlotCreate.model_validate(payload).model_dump(exclude={"farm_id"})
        plot = stamp(Plot(farm_id=farm.id, **data), max(sim.planting_date, self.world.params.window_start), 11)
        if sim.closed_at is not None:
            PlotCloseRequest(closed_at=sim.closed_at)
            plot.status = PlotStatusEnum.closed
            plot.closed_at = sim.closed_at
        db.add(plot)
        db.flush()
        self.plots[sim.key] = plot
        self.out.count("plots")
        if sim.alert_config:
            values = AlertConfigValues.model_validate(sim.alert_config).model_dump()
            db.add(AlertConfig(plot_id=plot.id, **values))

        for event in sim.events:
            if event.event_type == "closure":
                db.add(stamp(PlotEvent(plot_id=plot.id, event_type="closure", event_date=event.day,
                                       description=event.description), event.day))
            else:
                data = PlotEventCreate(event_type=event.event_type, event_date=event.day, description=event.description)
                db.add(stamp(PlotEvent(plot_id=plot.id, **data.model_dump()), event.day))
            self.out.count("plot_events")

        for soil in sim.soil:
            if soil.recorded:
                data = SoilAnalysisCreate.model_validate({"plot_id": plot.id, "analysis_date": soil.day, **soil.fields})
                db.add(stamp(SoilAnalysis(**data.model_dump()), soil.day))
                self.out.count("soil_analyses")

        for cycle_sim in sim.cycles:
            CycleCreate(plot_id=plot.id, start_date=cycle_sim.start)
            cycle = stamp(CropCycle(
                plot_id=plot.id, cycle_number=next_cycle_number(db, plot.id), start_date=cycle_sim.start,
            ), cycle_sim.start)
            if cycle_sim.end is not None:
                CycleCloseRequest(end_date=cycle_sim.end)
                cycle.status = CycleStatusEnum.closed
                cycle.end_date = cycle_sim.end
            db.add(cycle)
            db.flush()
            self.out.count("cycles")
            self.persist_labors(cycle, cycle_sim)
            for harvest_sim in cycle_sim.harvests:
                self.persist_harvest(cycle, harvest_sim)

    def persist_labors(self, cycle: CropCycle, sim) -> None:
        for labor in sim.labors:
            if not labor.recorded:
                continue
            model, schema, date_field = LABOR_KINDS[labor.kind]
            payload = {"crop_cycle_id": cycle.id, date_field: labor.day, **labor.fields}
            if labor.supply:
                payload["supply_id"] = self.supplies[labor.supply].id
            schema.model_validate(payload)
            columns = {key: value for key, value in payload.items() if hasattr(model, key)}
            for key, value in columns.items():
                if isinstance(value, float):
                    columns[key] = Decimal(str(value))
            self.db.add(stamp(model(**columns), labor.day))
            self.out.count(labor.kind)

    def persist_harvest(self, cycle: CropCycle, sim: HarvestSim) -> None:
        db = self.db
        HarvestCreate(crop_cycle_id=cycle.id, start_date=sim.start,
                      rate_per_kg=dec(sim.rate_per_kg, 2), rate_per_day=dec(sim.rate_per_day, 2))
        harvest = stamp(Harvest(
            crop_cycle_id=cycle.id, pass_number=next_pass_number(db, cycle.id), start_date=sim.start,
            rate_per_kg=dec(sim.rate_per_kg, 2), rate_per_day=dec(sim.rate_per_day, 2),
        ), sim.start, 7)
        if sim.end is not None:
            HarvestCloseRequest(end_date=sim.end, total_cherry_kg=dec(sim.total_kg, 3))
            harvest.status = HarvestStatusEnum.closed
            harvest.end_date = sim.end
            harvest.total_cherry_kg = dec(sim.total_kg, 3)
        db.add(harvest)
        db.flush()
        self.out.harvests[id(sim)] = harvest
        self.farm_harvests.append(harvest)
        self.out.count("harvests")

        works = []
        for work in sim.works:
            employee = self.employees[work.employee.key]
            kg = dec(work.kg_collected, 3)
            rate = dec(work.rate_per_kg, 2)
            day_value = dec(work.day_value, 2)
            HarvestWorkFields(employee_id=employee.id, work_date=work.day, payment_type=work.payment_type,
                              kg_collected=kg, rate_per_kg=rate, day_value=day_value)
            total = (kg * rate).quantize(CENT, rounding=ROUND_HALF_UP) if work.payment_type == "per_kg" else day_value
            works.append(stamp(HarvestWork(
                harvest_id=harvest.id, employee_id=employee.id, work_date=work.day,
                payment_type=work.payment_type, kg_collected=kg, rate_per_kg=rate, day_value=day_value,
                total_value=total, paid=work.paid_at is not None, paid_at=work.paid_at,
            ), work.day, 17))
        db.add_all(works)
        self.out.count("harvest_works", len(works))

        if sim.cherry_eval is not None and sim.cherry_eval.recorded:
            self.persist_quality(sim.cherry_eval, harvest_id=harvest.id)

    def persist_quality(self, sim: QualitySim, harvest_id: Optional[int] = None, drying_id: Optional[int] = None) -> None:
        payload = {"stage": sim.stage, "eval_date": sim.day, "harvest_id": harvest_id, "drying_id": drying_id, **sim.fields}
        data = QualityEvalCreate.model_validate(payload)
        self.db.add(stamp(QualityEval(**data.model_dump()), sim.day, 15))
        self.out.count(f"quality_{sim.stage}")

    # ── Clima ─────────────────────────────────────────────────────────────

    def persist_climate(self, farm: Farm, sim: FarmSim) -> None:
        records = []
        for record in sim.climate_records:
            if not record.recorded:
                continue
            data = ClimateRecordCreate(
                farm_id=farm.id, record_date=record.day, rainfall_mm=dec(record.rainfall_mm, 1),
                temp_min_c=dec(record.temp_min, 1), temp_max_c=dec(record.temp_max, 1),
                observations=record.observations,
            )
            records.append(stamp(ClimateRecord(**data.model_dump()), record.day, 19))
        self.db.add_all(records)
        self.out.count("climate_records", len(records))

    # ── Beneficio, secado, inventario y calidad ───────────────────────────

    def persist_processing(self, farm: Farm, sim: FarmSim) -> None:
        wets: dict[str, WetProcessing] = {}
        for wet_sim in sim.wets:
            wets[wet_sim.key] = self.persist_wet(farm, wet_sim)
        self.db.flush()
        for drying_sim in sim.dryings:
            self.persist_drying(farm, drying_sim, wets)

    def persist_wet(self, farm: Farm, sim: WetSim) -> WetProcessing:
        db = self.db
        pairs = [(self.out.harvests[id(h)], dec(kg, 3)) for h, kg in sim.inputs]
        check_harvest_inputs(db, pairs)
        stages = {
            "floats_kg": dec(sim.floats_kg, 3), "floats_method": sim.floats_method,
            "pulped_at": sim.pulped_at, "fermentation_start": sim.fermentation_start,
            "fermentation_end": sim.fermentation_end, "fermentation_method": sim.fermentation_method,
            "fermentation_decided_by": sim.decided_by, "fermentation_criteria": sim.criteria,
            "ambient_temp_c": dec(sim.ambient_temp, 1), "wash_count": sim.wash_count,
            "washed_kg": dec(sim.washed_kg, 3),
        }
        data = WetProcessingCreate.model_validate({
            "farm_id": farm.id,
            "inputs": [{"harvest_id": harvest.id, "cherry_kg": kg} for harvest, kg in pairs],
            **stages,
        })
        wet = WetProcessing(farm_id=farm.id, **data.model_dump(exclude={"farm_id", "inputs", "observations"}))
        wet.inputs = [WetProcessingInput(harvest_id=harvest.id, cherry_kg=kg) for harvest, kg in pairs]
        if sim.status == "completed":
            WetCompleteRequest(washed_kg=wet.washed_kg)
            cherry = sum((kg for _, kg in pairs), Decimal(0))
            assert wet.washed_kg <= cherry, f"{sim.key}: lavado mayor que la cereza"
            wet.status = WetProcessingStatusEnum.completed
        stamp(wet, sim.day, 16 + min(sim.delay_h, 7.0))
        db.add(wet)
        self.out.count("wet_processings")
        return wet

    def persist_drying(self, farm: Farm, sim: DryingSim, wets: dict) -> None:
        db = self.db
        pairs = [(wets[wet_sim.key], dec(kg, 3)) for wet_sim, kg in sim.inputs]
        check_wet_inputs(db, pairs)
        data = DryingCreate.model_validate({
            "farm_id": farm.id, "method": sim.method, "other_detail": sim.other_detail, "start_date": sim.start,
            "inputs": [{"wet_processing_id": wet.id, "wet_kg": kg} for wet, kg in pairs],
        })
        drying = stamp(Drying(
            farm_id=farm.id, method=data.method, other_detail=data.other_detail, start_date=data.start_date,
        ), sim.start, 8)
        drying.inputs = [DryingInput(wet_processing_id=wet.id, wet_kg=kg) for wet, kg in pairs]
        for day, value in sim.humidity_checks:
            check = HumidityCheckCreate(check_date=day, humidity_pct=dec(value, 2))
            drying.humidity_checks.append(stamp(DryingHumidityCheck(**check.model_dump()), day, 12))
        db.add(drying)
        db.flush()
        self.out.dryings[sim.key] = drying
        self.out.count("dryings")
        self.out.count("humidity_checks", len(sim.humidity_checks))
        if sim.end is None:
            return

        inventory = sim.inventory
        request = DryingCompleteRequest.model_validate({
            "end_date": sim.end, "final_humidity_pct": dec(sim.final_humidity, 2), "output_kg": dec(sim.output_kg, 3),
            "packaging": sim.packaging, "sack_count": sim.sack_count, "packed_at": sim.packed_at,
            "storage_place": sim.storage_place, "destination": sim.destination,
            "inventory_data": {"full_price": dec(inventory[0], 2), "purchase_date": inventory[1]} if inventory else None,
        })
        wet_total = sum((kg for _, kg in pairs), Decimal(0))
        assert request.output_kg <= wet_total, f"{sim.key}: pergamino mayor que el lavado"
        drying.status = DryingStatusEnum.completed
        drying.end_date = request.end_date
        for name in ("final_humidity_pct", "output_kg", "packaging", "sack_count", "packed_at", "storage_place", "destination"):
            setattr(drying, name, getattr(request, name))
        db.flush()

        if inventory is not None:
            self.to_inventory(drying, *inventory)
        elif sim.later_inventory is not None:
            # Guardado en la finca que pasa después al inventario (`/dryings/{id}/to-inventory`)
            drying.destination = "inventory"
            self.to_inventory(drying, *sim.later_inventory)

        if sim.quality is not None and sim.quality.recorded:
            self.persist_quality(sim.quality, drying_id=drying.id)

    def to_inventory(self, drying: Drying, full_price: float, purchase_date: date) -> None:
        """Puente al inventario; el inventario fecha con la hora actual, se lleva a la del ingreso."""
        parchment = send_to_inventory(self.db, drying, dec(full_price, 2), purchase_date)
        moment = at(purchase_date, 10)
        parchment.inventory.date = moment
        for movement in self.db.query(InventoryMovement).filter(InventoryMovement.parchment_id == parchment.id):
            movement.movement_date = moment
        self.out.count("parchments")

    # ── Jornales ──────────────────────────────────────────────────────────

    def persist_day_labors(self, sim: FarmSim) -> None:
        labors = []
        for labor in sim.day_labors:
            employee = self.employees[labor.employee.key]
            plot_id = self.plots[labor.plot.key].id if labor.plot else None
            data = DayLaborFields(
                employee_id=employee.id, labor_date=labor.day, activity_type=labor.activity,
                other_detail=labor.other_detail, plot_id=plot_id, daily_value=dec(labor.daily_value, 2),
            )
            labors.append(stamp(DayLabor(
                **data.model_dump(exclude={"observations"}), paid=labor.paid_at is not None, paid_at=labor.paid_at,
            ), labor.day, 17))
        self.db.add_all(labors)
        self.out.count("day_labors", len(labors))
