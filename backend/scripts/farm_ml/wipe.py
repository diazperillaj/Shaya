"""
Alcance y borrado de los datos sintéticos (plan-migraciones §6).

Todo lo sintético cuelga del caficultor marcado (`Person.observation =
SYNTHETIC_ML_DATA`). El borrado va en orden inverso de dependencia — con
`RESTRICT` en toda la cadena no hay `TRUNCATE CASCADE` posible — y en una
sola transacción: o se borra todo o no se borra nada.

Los insumos no se borran: son el catálogo global de productos comerciales
(D7) y pueden estar en uso por fincas reales.
"""

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

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
    WetProcessing,
    WetProcessingInput,
)
from app.models.farmer import Farmer
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.parchment import Parchment
from app.models.person import Person
from app.models.user import User
from scripts.farm_ml.persist import MARKER

CYCLE_LABORS = (Fertilization, PhytosanitaryApp, Irrigation, PestMonitoring, CulturalPractice, FloweringRecord)


def synthetic_scope() -> dict:
    """
    Tabla → (modelo, consulta de los ids sintéticos), de padres a hijos.

    Las consultas son subconsultas: se evalúan al usarlas, contra el estado
    de la base en ese momento.
    """
    persons = select(Person.id).where(Person.observation == MARKER)
    farmers = select(Farmer.id).where(Farmer.person_id.in_(persons))
    farms = select(Farm.id).where(Farm.farmer_id.in_(farmers))
    plots = select(Plot.id).where(Plot.farm_id.in_(farms))
    cycles = select(CropCycle.id).where(CropCycle.plot_id.in_(plots))
    harvests = select(Harvest.id).where(Harvest.crop_cycle_id.in_(cycles))
    employees = select(Employee.id).where(Employee.farm_id.in_(farms))
    wets = select(WetProcessing.id).where(WetProcessing.farm_id.in_(farms))
    dryings = select(Drying.id).where(Drying.farm_id.in_(farms))
    parchments = select(Parchment.id).where(Parchment.drying_id.in_(dryings))

    scope = {
        "persons": (Person, persons),
        "farmers": (Farmer, farmers),
        "farms": (Farm, farms),
        "alert_configs": (AlertConfig, select(AlertConfig.id).where(
            or_(AlertConfig.farm_id.in_(farms), AlertConfig.plot_id.in_(plots)))),
        "employees": (Employee, employees),
        "plots": (Plot, plots),
        "plot_events": (PlotEvent, select(PlotEvent.id).where(PlotEvent.plot_id.in_(plots))),
        "soil_analyses": (SoilAnalysis, select(SoilAnalysis.id).where(SoilAnalysis.plot_id.in_(plots))),
        "climate_records": (ClimateRecord, select(ClimateRecord.id).where(ClimateRecord.farm_id.in_(farms))),
        "crop_cycles": (CropCycle, cycles),
    }
    for model in CYCLE_LABORS:
        scope[model.__tablename__] = (model, select(model.id).where(model.crop_cycle_id.in_(cycles)))
    scope.update({
        "harvests": (Harvest, harvests),
        "harvest_works": (HarvestWork, select(HarvestWork.id).where(HarvestWork.harvest_id.in_(harvests))),
        "day_labors": (DayLabor, select(DayLabor.id).where(DayLabor.employee_id.in_(employees))),
        "wet_processings": (WetProcessing, wets),
        "wet_processing_inputs": (WetProcessingInput, select(WetProcessingInput.id).where(
            WetProcessingInput.wet_processing_id.in_(wets))),
        "dryings": (Drying, dryings),
        "drying_inputs": (DryingInput, select(DryingInput.id).where(DryingInput.drying_id.in_(dryings))),
        "drying_humidity_checks": (DryingHumidityCheck, select(DryingHumidityCheck.id).where(
            DryingHumidityCheck.drying_id.in_(dryings))),
        "quality_evals": (QualityEval, select(QualityEval.id).where(
            or_(QualityEval.harvest_id.in_(harvests), QualityEval.drying_id.in_(dryings)))),
        "inventories": (Inventory, select(Parchment.inventory_id).where(Parchment.id.in_(parchments))),
        "parchments": (Parchment, parchments),
        "inventory_movements": (InventoryMovement, select(InventoryMovement.id).where(
            InventoryMovement.parchment_id.in_(parchments))),
    })
    return scope


def count_synthetic(db: Session) -> dict[str, int]:
    """Filas sintéticas por tabla."""
    return {
        name: db.query(model).filter(model.id.in_(ids)).count()
        for name, (model, ids) in synthetic_scope().items()
    }


def wipe_synthetic(db: Session) -> dict[str, int]:
    """
    Borra todo lo sintético, de hijos a padres, en una transacción.

    Si un pergamino sintético ya se usó en un proceso o una venta, la base
    lo impide (RESTRICT) y no se borra nada.
    """
    scope = synthetic_scope()
    # Los inventarios se identifican por sus pergaminos: se fijan antes de borrarlos
    inventory_ids = [row[0] for row in db.execute(scope["inventories"][1])]
    users = select(User.id).where(User.person_id.in_(scope["persons"][1]))

    order = [
        "quality_evals", "inventory_movements", "parchments", "drying_humidity_checks", "drying_inputs",
        "dryings", "wet_processing_inputs", "wet_processings", "harvest_works", "day_labors", "harvests",
        *(model.__tablename__ for model in CYCLE_LABORS),
        "crop_cycles", "climate_records", "soil_analyses", "plot_events", "alert_configs",
    ]
    deleted: dict[str, int] = {}
    try:
        for name in order:
            model, ids = scope[name]
            deleted[name] = db.query(model).filter(model.id.in_(ids)).delete(synchronize_session=False)
        deleted["inventories"] = (
            db.query(Inventory).filter(Inventory.id.in_(inventory_ids)).delete(synchronize_session=False)
            if inventory_ids else 0
        )
        # Una renovación apunta a su lote anterior: se suelta antes de borrar los lotes
        db.execute(update(Plot).where(Plot.id.in_(scope["plots"][1])).values(renewed_from_plot_id=None))
        for name in ("plots", "employees", "farms"):
            model, ids = scope[name]
            deleted[name] = db.query(model).filter(model.id.in_(ids)).delete(synchronize_session=False)
        # Cuentas creadas para el caficultor sintético (demostraciones)
        deleted["users"] = db.query(User).filter(User.id.in_(users)).delete(synchronize_session=False)
        for name in ("farmers", "persons"):
            model, ids = scope[name]
            deleted[name] = db.query(model).filter(model.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return deleted
