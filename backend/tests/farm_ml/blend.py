"""
Un secado que mezcla dos lotes, con valores elegidos para calcular sus
features a mano (tests/farm_ml/test_features.py). También lo usan las
pruebas de la proyección.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.farm_operations.models import (
    ClimateRecord,
    CropCycle,
    CulturalPractice,
    Drying,
    DryingInput,
    Employee,
    Farm,
    Fertilization,
    FloweringRecord,
    Harvest,
    HarvestWork,
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
from app.farm_operations.services.dates import BUSINESS_TZ
from app.models.farmer import Farmer
from app.models.person import Person


def at(day: date, hour: float) -> datetime:
    return datetime(day.year, day.month, day.day, int(hour), int(hour % 1 * 60), tzinfo=BUSINESS_TZ)


def build_blend(db, farmer: Optional[Farmer] = None, name: str = "La Mezcla") -> dict:
    """
    Un secado que mezcla dos lotes: 250 kg de cereza trazada del lote A
    (Caturra) y 50 del lote B (Castillo), de dos beneficios.
    """
    if farmer is None:
        farmer = Farmer(person=Person(full_name="Caficultora"), farm_name="F", village="V", municipality="M")
    farm = Farm(farmer=farmer, name=name, village="Vereda", municipality="Pitalito", altitude=Decimal(1600))
    plot_a = Plot(farm=farm, name="A", variety="Caturra", area=Decimal("2.0"), row_spacing_m=Decimal("2.0"),
                  plant_spacing_m=Decimal("1.0"), planting_date=date(2018, 1, 1), shade_type="Libre", soil_type="Franco")
    plot_b = Plot(farm=farm, name="B", variety="Castillo", area=Decimal("1.0"), row_spacing_m=Decimal("1.5"),
                  plant_spacing_m=Decimal("1.0"), planting_date=date(2020, 6, 1), shade_type="Semisombra",
                  soil_type="Franco")
    cycle_a = CropCycle(plot=plot_a, cycle_number=1, start_date=date(2025, 1, 1))
    cycle_b = CropCycle(plot=plot_b, cycle_number=1, start_date=date(2025, 1, 1))
    urea = Supply(name=f"Urea {name}", supply_type="fertilizer", unit="kg", composition="N 46 %")
    kcl = Supply(name=f"Cloruro de potasio {name}", supply_type="fertilizer", unit="kg", composition="K 60 %")
    fungicide = Supply(name=f"Cyproconazol {name}", supply_type="phytosanitary", unit="L")
    picker = Employee(farm=farm, full_name="Recolectora")
    db.add_all([cycle_a, cycle_b, urea, kcl, fungicide, picker])
    db.flush()

    a, b = cycle_a.id, cycle_b.id
    db.add_all([
        PlotEvent(plot_id=plot_a.id, event_type="zoca", event_date=date(2022, 3, 1)),
        SoilAnalysis(plot_id=plot_a.id, analysis_date=date(2024, 5, 1), ph=Decimal("5.2"), organic_matter_pct=Decimal(8)),
        SoilAnalysis(plot_id=plot_a.id, analysis_date=date(2025, 11, 1), ph=Decimal("6.0")),   # después: no cuenta
        # Clima de la finca; el lote B tiene además su propio registro el 1 de septiembre
        ClimateRecord(farm_id=farm.id, record_date=date(2025, 9, 1), rainfall_mm=Decimal(10),
                      temp_min_c=Decimal(15), temp_max_c=Decimal(25)),
        ClimateRecord(farm_id=farm.id, record_date=date(2025, 9, 2), rainfall_mm=Decimal(20)),
        ClimateRecord(farm_id=farm.id, record_date=date(2025, 10, 2), rainfall_mm=Decimal(30),
                      temp_min_c=Decimal(14), temp_max_c=Decimal(24)),
        ClimateRecord(farm_id=farm.id, record_date=date(2025, 10, 10), rainfall_mm=Decimal(5)),
        ClimateRecord(farm_id=farm.id, plot_id=plot_b.id, record_date=date(2025, 9, 1), rainfall_mm=Decimal(40)),
        Fertilization(crop_cycle_id=a, supply_id=urea.id, application_date=date(2025, 3, 1), method="soil",
                      quantity=Decimal(100)),
        Fertilization(crop_cycle_id=a, supply_id=kcl.id, application_date=date(2025, 5, 1), method="soil",
                      quantity=Decimal(50)),
        Fertilization(crop_cycle_id=a, supply_id=urea.id, application_date=date(2025, 10, 20), method="soil",
                      quantity=Decimal(100)),   # después de la cosecha: no cuenta
        PhytosanitaryApp(crop_cycle_id=a, supply_id=fungicide.id, application_date=date(2025, 6, 1), target="Roya",
                         quantity=Decimal(1)),
        PestMonitoring(crop_cycle_id=a, monitoring_date=date(2025, 5, 1), roya_pct=Decimal(30)),  # antes del llenado
        PestMonitoring(crop_cycle_id=a, monitoring_date=date(2025, 7, 1), broca_pct=Decimal(1), roya_pct=Decimal(5)),
        PestMonitoring(crop_cycle_id=a, monitoring_date=date(2025, 9, 15), broca_pct=Decimal(3), roya_pct=Decimal(12)),
        PestMonitoring(crop_cycle_id=a, monitoring_date=date(2025, 10, 10), broca_pct=Decimal(9)),  # después
        CulturalPractice(crop_cycle_id=a, practice_date=date(2025, 2, 1), practice_type="pruning"),
        CulturalPractice(crop_cycle_id=a, practice_date=date(2025, 4, 1), practice_type="weeding"),
        CulturalPractice(crop_cycle_id=a, practice_date=date(2025, 11, 1), practice_type="weeding"),  # después
        CulturalPractice(crop_cycle_id=b, practice_date=date(2025, 5, 5), practice_type="weeding"),
        FloweringRecord(crop_cycle_id=a, flowering_date=date(2025, 2, 10), intensity="low"),
        FloweringRecord(crop_cycle_id=a, flowering_date=date(2025, 2, 20), intensity="high"),
        FloweringRecord(crop_cycle_id=b, flowering_date=date(2025, 3, 1), intensity="medium"),
    ])
    harvest_a = Harvest(crop_cycle_id=a, pass_number=1, start_date=date(2025, 10, 1), end_date=date(2025, 10, 3),
                        status="closed", total_cherry_kg=Decimal(600))
    harvest_b = Harvest(crop_cycle_id=b, pass_number=1, start_date=date(2025, 10, 2), end_date=date(2025, 10, 2),
                        status="closed", total_cherry_kg=Decimal(300))
    db.add_all([harvest_a, harvest_b])
    db.flush()
    work = dict(employee_id=picker.id, payment_type="per_kg", kg_collected=Decimal(100), rate_per_kg=Decimal(700),
                total_value=Decimal(70000))
    db.add_all([
        HarvestWork(harvest_id=harvest_a.id, work_date=date(2025, 10, day), **work) for day in (1, 2, 3)
    ] + [
        HarvestWork(harvest_id=harvest_b.id, work_date=date(2025, 10, 2), **work),
        QualityEval(stage="cherry", harvest_id=harvest_a.id, eval_date=date(2025, 10, 3), ripe_pct=Decimal(90),
                    green_pct=Decimal(5), bored_pct=Decimal(2)),
        QualityEval(stage="cherry", harvest_id=harvest_b.id, eval_date=date(2025, 10, 2), ripe_pct=Decimal(80),
                    green_pct=Decimal(10), bored_pct=Decimal(4)),
        QualityEval(stage="cherry", harvest_id=harvest_a.id, eval_date=date(2025, 11, 30),
                    bored_pct=Decimal(50)),   # posterior al cierre del secado: no cuenta
    ])
    # Beneficio 1: mezcla de las dos cosechas, despulpado el mismo día de la entrega (2 h)
    wet_1 = WetProcessing(farm_id=farm.id, status="completed", floats_kg=Decimal(10),
                          pulped_at=at(date(2025, 10, 2), 18), fermentation_start=at(date(2025, 10, 2), 18.5),
                          fermentation_end=at(date(2025, 10, 3), 10.5), fermentation_method="tank",
                          ambient_temp_c=Decimal(20), washed_kg=Decimal(180))
    wet_1.inputs = [WetProcessingInput(harvest_id=harvest_a.id, cherry_kg=Decimal(100)),
                    WetProcessingInput(harvest_id=harvest_b.id, cherry_kg=Decimal(100))]
    # Beneficio 2: solo el lote A, despulpado la mañana siguiente (15 h)
    wet_2 = WetProcessing(farm_id=farm.id, status="completed", pulped_at=at(date(2025, 10, 4), 7),
                          fermentation_start=at(date(2025, 10, 4), 8), fermentation_end=at(date(2025, 10, 5), 8),
                          fermentation_method="dry", washed_kg=Decimal(160))
    wet_2.inputs = [WetProcessingInput(harvest_id=harvest_a.id, cherry_kg=Decimal(200))]
    db.add_all([wet_1, wet_2])
    db.flush()
    drying = Drying(farm_id=farm.id, method="marquesina", start_date=date(2025, 10, 5), end_date=date(2025, 10, 15),
                    status="completed", output_kg=Decimal(100), final_humidity_pct=Decimal("11.5"),
                    destination="direct_sale")
    # La mitad del lavado del beneficio 1 y todo el del 2: 50 + 50 + 200 kg de cereza trazada
    drying.inputs = [DryingInput(wet_processing_id=wet_1.id, wet_kg=Decimal(90)),
                     DryingInput(wet_processing_id=wet_2.id, wet_kg=Decimal(160))]
    db.add(drying)
    db.flush()
    return {"farm": farm, "plot_a": plot_a, "cycle_a": cycle_a, "cycle_b": cycle_b, "drying": drying,
            "harvest_a": harvest_a, "wet_1": wet_1, "wet_2": wet_2}
