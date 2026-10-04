"""
Dashboard y alertas del módulo de cultivo (dashboards-alertas, bloque 6).

Cada tipo de alerta tiene un caso que la dispara y otro que no; las fechas
son relativas a un «hoy» fijo, para que las pruebas no dependan del día en
que corren.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from app.farm_operations.models import (
    AlertConfig,
    ClimateRecord,
    CropCycle,
    CulturalPractice,
    DayLabor,
    Drying,
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
    QualityEval,
    Supply,
    WetProcessing,
    WetProcessingInput,
)
from app.farm_operations.services.alerts import compute_alerts
from app.farm_operations.services.dates import BUSINESS_TZ
from app.farm_operations.services.seasons import HarvestSpan, group_seasons
from app.models.farmer import Farmer
from app.models.person import Person
from tests.farm_operations.payloads import API

TODAY = date(2026, 6, 15)
NOW = datetime(2026, 6, 15, 12, 0, tzinfo=BUSINESS_TZ)


def ago(days: int) -> date:
    return TODAY - timedelta(days=days)


def moment(days: float) -> datetime:
    return NOW - timedelta(days=days)


class Farmyard:
    """Una finca con un lote y su ciclo activo, y atajos para crear registros."""

    def __init__(self, db, name="La Esperanza", farmer=None):
        self.db = db
        if farmer is None:
            farmer = Farmer(person=Person(full_name="Caficultor"), farm_name="F", village="V", municipality="M")
        self.farm = Farm(farmer=farmer, name=name, village="Vereda", municipality="Pitalito")
        self.plot = Plot(farm=self.farm, name="El Alto", variety="Castillo", planting_date=date(2018, 1, 1))
        self.cycle = CropCycle(plot=self.plot, cycle_number=2, start_date=ago(20))
        self.supply = Supply(name=f"Insumo {name}", supply_type="fertilizer", unit="kg")
        self.employee = Employee(farm=self.farm, full_name="Pedro Recolector")
        # La cereza de los beneficios de prueba sale de una cosecha del ciclo anterior
        old_cycle = CropCycle(plot=self.plot, cycle_number=1, start_date=ago(500), end_date=ago(380), status="closed")
        self.source = Harvest(crop_cycle=old_cycle, pass_number=1, start_date=ago(400), end_date=ago(395),
                              status="closed", total_cherry_kg=Decimal(100000))
        db.add_all([self.cycle, self.supply, self.employee, self.source])
        db.flush()

    def add(self, *objects):
        self.db.add_all(objects)
        self.db.flush()
        return objects[0] if len(objects) == 1 else objects

    def harvest(self, start: date, end=None, number=1, total="500", cycle=None):
        return self.add(Harvest(
            crop_cycle_id=(cycle or self.cycle).id, pass_number=number, start_date=start, end_date=end,
            status="closed" if end else "open", total_cherry_kg=Decimal(total) if end else None,
        ))

    def wet(self, cherry="100", washed="44", status="completed", start=None, end=None, harvest=None):
        harvest = harvest or self.source
        wet = WetProcessing(
            farm_id=self.farm.id, status=status, washed_kg=Decimal(washed) if washed else None,
            fermentation_start=start, fermentation_end=end,
        )
        wet.inputs = [WetProcessingInput(harvest_id=harvest.id, cherry_kg=Decimal(cherry))]
        return self.add(wet)

    def drying(self, start: date, end=None, output=None, humidity="11", wet=None, wet_kg="44", destination="direct_sale"):
        wet = wet or self.wet()
        drying = Drying(
            farm_id=self.farm.id, method="marquesina", start_date=start, end_date=end,
            status="completed" if end else "in_progress",
            output_kg=Decimal(output) if end else None, final_humidity_pct=Decimal(humidity) if end else None,
            destination=destination if end else None,
        )
        drying.inputs = [DryingInput(wet_processing_id=wet.id, wet_kg=Decimal(wet_kg))]
        return self.add(drying)

    def config(self, plot=False, **values):
        return self.add(AlertConfig(plot_id=self.plot.id, **values) if plot else AlertConfig(farm_id=self.farm.id, **values))


@pytest.fixture
def yard(db_session):
    return Farmyard(db_session)


def alerts_of(db, yard, type_):
    return [a for a in compute_alerts(db, [yard.farm.id], today=TODAY, now=NOW) if a.type == type_]


# ═══════════════════════════════════════════════════════════════════════════
# Recordatorios (info)
# ═══════════════════════════════════════════════════════════════════════════


def test_fertilization_reminder(db_session, yard):
    yard.cycle.start_date = ago(200)
    yard.add(Fertilization(crop_cycle_id=yard.cycle.id, supply_id=yard.supply.id, application_date=ago(121),
                           method="soil", quantity=Decimal(50)))
    [alert] = alerts_of(db_session, yard, "fertilization_due")
    assert alert.value == 121 and alert.threshold == 120 and alert.entity["crop_cycle_id"] == yard.cycle.id

    yard.add(Fertilization(crop_cycle_id=yard.cycle.id, supply_id=yard.supply.id, application_date=ago(100),
                           method="soil", quantity=Decimal(50)))
    assert alerts_of(db_session, yard, "fertilization_due") == []


def test_reminder_counts_from_the_cycle_start_without_records(db_session, yard):
    yard.cycle.start_date = ago(130)
    yard.db.flush()
    [alert] = alerts_of(db_session, yard, "fertilization_due")
    assert alert.since == ago(130) and "en el ciclo" in alert.message


def test_phytosanitary_reminder_counts_monitoring_or_control(db_session, yard):
    yard.cycle.start_date = ago(200)
    yard.add(PestMonitoring(crop_cycle_id=yard.cycle.id, monitoring_date=ago(31), broca_pct=Decimal("0.5")))
    assert len(alerts_of(db_session, yard, "phytosanitary_due")) == 1

    yard.add(PhytosanitaryApp(crop_cycle_id=yard.cycle.id, supply_id=yard.supply.id, application_date=ago(5),
                              target="Roya", quantity=Decimal(1)))
    assert alerts_of(db_session, yard, "phytosanitary_due") == []


def test_weeding_reminder_only_counts_weedings(db_session, yard):
    yard.cycle.start_date = ago(200)
    yard.add(CulturalPractice(crop_cycle_id=yard.cycle.id, practice_type="pruning", practice_date=ago(3)))
    assert len(alerts_of(db_session, yard, "weeding_due")) == 1

    yard.add(CulturalPractice(crop_cycle_id=yard.cycle.id, practice_type="weeding", practice_date=ago(10)))
    assert alerts_of(db_session, yard, "weeding_due") == []


def test_irrigation_reminder_is_off_until_configured(db_session, yard):
    yard.cycle.start_date = ago(200)
    yard.add(Irrigation(crop_cycle_id=yard.cycle.id, irrigation_date=ago(11)))
    assert alerts_of(db_session, yard, "irrigation_due") == []

    yard.config(irrigation_reminder_days=10)
    [alert] = alerts_of(db_session, yard, "irrigation_due")
    assert alert.threshold == 10


def test_next_pass_reminder(db_session, yard):
    yard.harvest(ago(25), ago(16))
    [alert] = alerts_of(db_session, yard, "harvest_pass_due")
    assert "pasada 1 terminó hace 16 días" in alert.message

    yard.harvest(ago(2), number=2)
    assert alerts_of(db_session, yard, "harvest_pass_due") == []


def test_harvest_estimated_by_the_main_flowering(db_session, yard):
    yard.cycle.start_date = ago(300)
    yard.add(FloweringRecord(crop_cycle_id=yard.cycle.id, flowering_date=ago(230), intensity="high"),
             FloweringRecord(crop_cycle_id=yard.cycle.id, flowering_date=ago(200), intensity="low"))
    [alert] = alerts_of(db_session, yard, "harvest_pass_due")
    assert alert.since == ago(230) + timedelta(days=224)

    yard.db.query(FloweringRecord).filter(FloweringRecord.intensity == "high").delete()
    assert alerts_of(db_session, yard, "harvest_pass_due") == []   # la principal ahora es la de hace 200 días


# ═══════════════════════════════════════════════════════════════════════════
# Desvíos (medium)
# ═══════════════════════════════════════════════════════════════════════════


def test_inactive_cycle(db_session, yard):
    yard.cycle.start_date = ago(100)
    yard.add(PestMonitoring(crop_cycle_id=yard.cycle.id, monitoring_date=ago(50), broca_pct=Decimal(1)))
    [alert] = alerts_of(db_session, yard, "cycle_inactive")
    assert alert.value == 50 and alert.threshold == 45

    # El clima de la finca cuenta como actividad de todos sus lotes
    yard.add(ClimateRecord(farm_id=yard.farm.id, record_date=ago(3), rainfall_mm=Decimal(4)))
    assert alerts_of(db_session, yard, "cycle_inactive") == []


def test_humidity_out_of_range_only_for_recent_dryings(db_session, yard):
    yard.drying(ago(15), ago(5), output="20", humidity="12.6")
    yard.drying(ago(50), ago(40), output="20", humidity="13.5")   # fuera de la ventana de 30 días
    yard.drying(ago(14), ago(4), output="20", humidity="11.2")
    [alert] = alerts_of(db_session, yard, "humidity_out_of_range")
    assert alert.value == 12.6 and alert.threshold == 12


def test_fermentation_out_of_range_follows_the_farm_config(db_session, yard):
    yard.wet(start=moment(3), end=moment(3) + timedelta(hours=30))
    yard.wet(start=moment(2), end=moment(2) + timedelta(hours=15))
    [alert] = alerts_of(db_session, yard, "fermentation_out_of_range")
    assert alert.value == 30 and alert.threshold == 24

    yard.config(min_fermentation_hours=8, max_fermentation_hours=12)
    assert len(alerts_of(db_session, yard, "fermentation_out_of_range")) == 2


def test_closed_harvest_without_cherry_quality(db_session, yard):
    harvest = yard.harvest(ago(12), ago(5))
    [alert] = alerts_of(db_session, yard, "harvest_without_quality")
    assert alert.entity == {"harvest_id": harvest.id}

    yard.add(QualityEval(stage="cherry", harvest_id=harvest.id, eval_date=ago(4), green_pct=Decimal(5)))
    assert alerts_of(db_session, yard, "harvest_without_quality") == []


def test_drying_without_parchment_quality_after_seven_days(db_session, yard):
    old = yard.drying(ago(20), ago(10), output="20")
    yard.drying(ago(15), ago(5), output="20")            # aún dentro del margen
    [alert] = alerts_of(db_session, yard, "drying_without_quality")
    assert alert.entity == {"drying_id": old.id}

    yard.add(QualityEval(stage="parchment", drying_id=old.id, eval_date=ago(1), score=Decimal(82)))
    assert alerts_of(db_session, yard, "drying_without_quality") == []


def test_yield_below_the_farm_history(db_session, yard):
    # Histórico: tres secados al 22 % (22 kg de 100 kg de cereza)
    for offset in (100, 150, 200):
        yard.drying(ago(offset + 10), ago(offset), output="22")
    low = yard.drying(ago(12), ago(2), output="18")       # 18 % < 22 − 3
    yard.drying(ago(11), ago(1), output="20")             # 20 %: dentro de lo normal
    [alert] = alerts_of(db_session, yard, "yield_below_history")
    assert alert.entity == {"drying_id": low.id} and alert.value == 18.0 and alert.threshold == 19.0


def test_yield_alert_needs_history(db_session, yard):
    yard.drying(ago(100), ago(90), output="22")
    yard.drying(ago(12), ago(2), output="10")
    assert alerts_of(db_session, yard, "yield_below_history") == []


# ═══════════════════════════════════════════════════════════════════════════
# Riesgos (high)
# ═══════════════════════════════════════════════════════════════════════════


def test_broca_uses_the_latest_monitoring_and_plot_threshold(db_session, yard):
    yard.add(PestMonitoring(crop_cycle_id=yard.cycle.id, monitoring_date=ago(30), broca_pct=Decimal(5)),
             PestMonitoring(crop_cycle_id=yard.cycle.id, monitoring_date=ago(3), broca_pct=Decimal("1.5")))
    assert alerts_of(db_session, yard, "broca_above_threshold") == []   # el último está bajo el 2 %

    yard.config(plot=True, broca_alert_pct=Decimal(1))
    [alert] = alerts_of(db_session, yard, "broca_above_threshold")
    assert alert.value == 1.5 and alert.threshold == 1


def test_drying_too_long(db_session, yard):
    yard.drying(ago(16))
    yard.drying(ago(10))
    [alert] = alerts_of(db_session, yard, "drying_too_long")
    assert alert.value == 16

    yard.config(max_drying_days=4)
    assert len(alerts_of(db_session, yard, "drying_too_long")) == 2


def test_stalled_fermentation(db_session, yard):
    stalled = yard.wet(status="in_progress", washed=None, start=NOW - timedelta(hours=30))
    yard.wet(status="in_progress", washed=None, start=NOW - timedelta(hours=10))
    [alert] = alerts_of(db_session, yard, "processing_stalled")
    assert alert.entity == {"wet_processing_id": stalled.id} and alert.value == 30


def test_unpaid_labor_is_one_alert_per_farm(db_session, yard):
    harvest = yard.harvest(ago(30), ago(20))
    yard.add(
        HarvestWork(harvest_id=harvest.id, employee_id=yard.employee.id, work_date=ago(20), payment_type="per_kg",
                    kg_collected=Decimal(100), rate_per_kg=Decimal(900), total_value=Decimal(90000)),
        HarvestWork(harvest_id=harvest.id, employee_id=yard.employee.id, work_date=ago(10), payment_type="per_kg",
                    kg_collected=Decimal(100), rate_per_kg=Decimal(900), total_value=Decimal(90000)),
        HarvestWork(harvest_id=harvest.id, employee_id=yard.employee.id, work_date=ago(25), payment_type="per_kg",
                    kg_collected=Decimal(100), rate_per_kg=Decimal(900), total_value=Decimal(90000),
                    paid=True, paid_at=ago(18)),
        DayLabor(employee_id=yard.employee.id, labor_date=ago(16), activity_type="weeding", daily_value=Decimal(60000)),
    )
    [alert] = alerts_of(db_session, yard, "unpaid_labor")
    assert alert.value == 150000 and alert.since == ago(20) and alert.entity == {"farm_id": yard.farm.id}
    assert alert.message.startswith("2 pagos pendientes por $ 150.000")


def test_no_unpaid_alert_for_recent_work(db_session, yard):
    yard.add(DayLabor(employee_id=yard.employee.id, labor_date=ago(10), activity_type="weeding", daily_value=Decimal(60000)))
    assert alerts_of(db_session, yard, "unpaid_labor") == []


def test_harvest_open_too_long(db_session, yard):
    harvest = yard.harvest(ago(31))
    [alert] = alerts_of(db_session, yard, "harvest_open_too_long")
    assert alert.entity == {"harvest_id": harvest.id} and alert.value == 31

    harvest.start_date = ago(20)
    yard.db.flush()
    assert alerts_of(db_session, yard, "harvest_open_too_long") == []


def test_alerts_are_sorted_by_severity_then_age(db_session, yard):
    yard.cycle.start_date = ago(200)
    yard.drying(ago(16))
    yard.harvest(ago(40))
    severities = [a.severity for a in compute_alerts(db_session, [yard.farm.id], today=TODAY, now=NOW)]
    assert severities == sorted(severities, key={"high": 0, "medium": 1, "info": 2}.get)


# ═══════════════════════════════════════════════════════════════════════════
# Temporadas (§2.1)
# ═══════════════════════════════════════════════════════════════════════════


def test_seasons_split_after_45_days_without_harvest():
    spans = [
        HarvestSpan(date(2025, 10, 1), date(2025, 10, 8), Decimal(100)),
        HarvestSpan(date(2025, 10, 25), date(2025, 11, 2), Decimal(200)),
        HarvestSpan(date(2025, 12, 17), date(2025, 12, 20), Decimal(50)),    # 45 días después: misma temporada
        HarvestSpan(date(2026, 4, 20), date(2026, 4, 28), Decimal(300)),     # otra temporada
    ]
    seasons = group_seasons(spans, date(2026, 6, 1))
    assert [(s.date_from, s.date_to, s.harvests, s.cherry_kg) for s in seasons] == [
        (date(2026, 4, 20), date(2026, 4, 28), 1, Decimal(300)),
        (date(2025, 10, 1), date(2025, 12, 20), 3, Decimal(350)),
    ]
    assert seasons[1].label == "Cosecha oct–dic 2025"


def test_open_pass_counts_until_its_last_work():
    # Una pasada que se olvidó cerrar en junio no une la temporada de abril con la de septiembre
    spans = [
        HarvestSpan(date(2026, 4, 20), date(2026, 5, 10), Decimal(100)),
        HarvestSpan(date(2026, 6, 1), None, None, last_work=date(2026, 6, 5)),
        HarvestSpan(date(2026, 9, 15), None, None, last_work=date(2026, 9, 28)),
    ]
    seasons = group_seasons(spans, date(2026, 10, 1))
    assert [(s.date_from, s.date_to, s.open) for s in seasons] == [
        (date(2026, 9, 15), date(2026, 10, 1), True),     # en curso: llega hasta hoy
        (date(2026, 4, 20), date(2026, 6, 5), True),
    ]


# ═══════════════════════════════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def farmer_yard(db_session, make_farmer):
    farmer, user = make_farmer()
    return Farmyard(db_session, name="Mi finca", farmer=farmer), user


def test_farmer_only_sees_his_farms(db_session, login, admin, farmer_yard):
    mine, user = farmer_yard
    other = Farmyard(db_session, name="Ajena")
    other.drying(date.today() - timedelta(days=20))

    client = login(user)
    assert client.get(f"{API}/dashboard/summary").json()["farms_active"] == 1
    assert client.get(f"{API}/dashboard/summary?farm_id={other.farm.id}").status_code == 404
    alerts = client.get(f"{API}/dashboard/alerts").json()
    assert alerts and all(a["farm_id"] == mine.farm.id for a in alerts)
    assert len(client.get(f"{API}/dashboard/farms").json()) == 1
    assert login(admin).get(f"{API}/dashboard/summary").json()["farms_active"] == 2


def test_state_widgets_ignore_the_period(db_session, login, admin, yard):
    today = date.today()
    yard.drying(today - timedelta(days=3))                              # en curso: estado
    yard.harvest(today - timedelta(days=40), today - timedelta(days=30), number=1, total="800")
    client = login(admin)

    recent = client.get(f"{API}/dashboard/summary", params={"date_from": (today - timedelta(days=10)).isoformat(), "date_to": today.isoformat()}).json()
    wide = client.get(f"{API}/dashboard/summary", params={"date_from": (today - timedelta(days=60)).isoformat(), "date_to": today.isoformat()}).json()
    assert recent["drying_in_progress"]["count"] == wide["drying_in_progress"]["count"] == 1
    assert recent["harvests_open"] == wide["harvests_open"]
    assert recent["cherry_kg"] == 0 and wide["cherry_kg"] == 800


def test_period_must_be_ordered(login, admin, yard):
    response = login(admin).get(f"{API}/dashboard/summary", params={"date_from": "2026-05-01", "date_to": "2026-04-01"})
    assert response.status_code == 400


def test_production_and_quality_by_plot(db_session, login, admin, yard):
    today = date.today()
    drying = yard.drying(today - timedelta(days=15), today - timedelta(days=5), output="22")
    yard.add(QualityEval(stage="parchment", drying_id=drying.id, eval_date=today - timedelta(days=2),
                         score=Decimal("84.5"), defects_pct=Decimal(3)))
    client = login(admin)

    production = client.get(f"{API}/dashboard/production", params={"farm_id": yard.farm.id}).json()
    assert production["unit"] == "plot"
    assert production["by_unit"] == {"labels": ["El Alto"], "series": [{"name": "Pergamino seco (kg)", "data": [22.0]}]}
    assert production["yield_by_unit"]["series"][0]["data"] == [22.0]
    quality = client.get(f"{API}/dashboard/quality", params={"farm_id": yard.farm.id}).json()
    assert quality["score_by_variety"]["labels"] == ["Castillo"]
    assert quality["score_defects_by_unit"]["series"][0]["data"] == [84.5]
    assert sum(quality["score_distribution"]["series"][0]["data"]) == 1
    assert quality["humidity_range"] == [10.0, 12.0]


def test_cycles_state_and_farm_ranking(db_session, login, admin, yard):
    today = date.today()
    yard.add(FloweringRecord(crop_cycle_id=yard.cycle.id, flowering_date=today - timedelta(days=10), intensity="high"))
    client = login(admin)

    [cycle] = client.get(f"{API}/dashboard/cycles").json()
    assert cycle["harvest_status"] == "waiting"
    assert cycle["estimated_harvest"] == (today - timedelta(days=10) + timedelta(days=224)).isoformat()
    assert cycle["last_labor"] == {"kind": "flowering-records", "date": (today - timedelta(days=10)).isoformat()}
    [row] = client.get(f"{API}/dashboard/farms").json()
    assert row["farm_name"] == "La Esperanza" and row["plots_active"] == 1
