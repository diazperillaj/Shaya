"""
Trazabilidad de la cadena cosecha → beneficio → secado → inventario
(modelo-datos §7).

Las mezclas se reparten en proporción a los kg: si de un beneficio que lavó
100 kg van 40 kg a un secado, a ese secado le corresponde el 40 % del café
cereza que entró al beneficio, y de él, a cada cosecha, lo que aportó.
"""

from collections import defaultdict
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.farm_operations.models import Drying, DryingInput, Harvest, WetProcessingInput

ZERO = Decimal(0)
HUNDRED = Decimal(100)


def _share(part: Decimal, whole: Decimal) -> Decimal:
    return (part * HUNDRED / whole).quantize(Decimal("0.1")) if whole else ZERO


def traced_cherry_by_harvest(drying: Drying) -> dict[Harvest, Decimal]:
    """Café cereza de cada cosecha que terminó en este secado."""
    by_harvest: dict[Harvest, Decimal] = defaultdict(lambda: ZERO)
    for drying_input in drying.inputs:
        wet_processing = drying_input.wet_processing
        if not wet_processing.washed_kg:
            continue
        fraction = drying_input.wet_kg / wet_processing.washed_kg
        for wet_input in wet_processing.inputs:
            by_harvest[wet_input.harvest] += wet_input.cherry_kg * fraction
    return dict(by_harvest)


def drying_composition(drying: Drying) -> dict:
    """
    Composición del secado por lote, café cereza trazado y rendimiento
    cereza → pergamino seco (F2: siempre calculado).
    """
    by_harvest = traced_cherry_by_harvest(drying)
    traced = sum(by_harvest.values(), ZERO)

    plots: dict[int, dict] = {}
    for harvest, cherry_kg in by_harvest.items():
        cycle = harvest.crop_cycle
        plot = cycle.plot
        entry = plots.setdefault(plot.id, {
            "plot_id": plot.id,
            "plot_name": plot.name,
            "variety": plot.variety,
            "cherry_kg": ZERO,
            "harvests": [],
        })
        entry["cherry_kg"] += cherry_kg
        entry["harvests"].append({
            "harvest_id": harvest.id,
            "pass_number": harvest.pass_number,
            "crop_cycle_id": cycle.id,
            "cycle_number": cycle.cycle_number,
            "cherry_kg": cherry_kg.quantize(Decimal("0.001")),
        })

    composition = sorted(plots.values(), key=lambda item: item["cherry_kg"], reverse=True)
    for entry in composition:
        entry["share_pct"] = _share(entry["cherry_kg"], traced)
        entry["cherry_kg"] = entry["cherry_kg"].quantize(Decimal("0.001"))
        entry["harvests"].sort(key=lambda item: (item["cycle_number"], item["pass_number"]))

    yield_pct = (
        _share(drying.output_kg, traced) if drying.output_kg is not None and traced else None
    )
    return {
        "cherry_kg_traced": traced.quantize(Decimal("0.001")),
        "yield_pct": yield_pct,
        "composition": composition,
    }


def dominant_variety(drying: Drying) -> Optional[str]:
    """Variedad del lote que más café aporta al secado."""
    composition = drying_composition(drying)["composition"]
    return composition[0]["variety"] if composition else None


def harvest_destinations(db: Session, harvest: Harvest) -> list[dict]:
    """A qué beneficios fue el café de la cosecha y, de ahí, a qué secados."""
    destinations = []
    inputs = db.query(WetProcessingInput).filter(WetProcessingInput.harvest_id == harvest.id).all()
    for wet_input in sorted(inputs, key=lambda item: item.wet_processing_id):
        wet_processing = wet_input.wet_processing
        dryings = []
        drying_inputs = (
            db.query(DryingInput).filter(DryingInput.wet_processing_id == wet_processing.id).all()
            if wet_processing.washed_kg else []
        )
        for drying_input in sorted(drying_inputs, key=lambda item: item.drying_id):
            drying = drying_input.drying
            fraction = drying_input.wet_kg / wet_processing.washed_kg
            dryings.append({
                "drying_id": drying.id,
                "status": drying.status,
                "destination": drying.destination,
                "cherry_kg": (wet_input.cherry_kg * fraction).quantize(Decimal("0.001")),
                "parchment_id": drying.parchment.id if drying.parchment else None,
            })
        destinations.append({
            "wet_processing_id": wet_processing.id,
            "status": wet_processing.status,
            "cherry_kg": wet_input.cherry_kg,
            "dryings": dryings,
        })
    return destinations
