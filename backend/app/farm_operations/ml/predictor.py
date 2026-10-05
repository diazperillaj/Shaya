"""
Proyección de calidad de los ciclos activos (generador-sintetico-ml §6).

Carga el artefacto al primer uso, no en el arranque de la API, y se niega a
usarlo si lo entrenaron otras versiones de scikit-learn o numpy, o con otras
features. Cada proyección arma las features a hoy (`features.py`), rellena
las etapas que aún no ocurren con los valores típicos de la finca —o, sin
historia, los del entrenamiento— y predice los tres targets: puntaje,
defectos y factor de rendimiento. La humedad del pergamino no se predice:
depende solo del secado y el caficultor la mide al cerrarlo.
"""

import threading
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.core.exceptions.domain import DomainError
from app.farm_operations.ml.features import (
    FEATURE_NAMES,
    build_features,
    cycle_origins,
    drying_origins,
    fill_future_stages,
    reference_values,
    to_matrix,
)
from app.farm_operations.models import CropCycle, Drying, Farm, Plot
from app.farm_operations.models.enums import DryingStatusEnum

MODEL_VERSION = "v1"
ARTIFACT = Path(__file__).parent / "artifacts" / f"quality_model_{MODEL_VERSION}.joblib"
DISCLAIMER = (
    "Estimación de un modelo entrenado con datos sintéticos: orienta sobre la calidad esperada, "
    "no reemplaza la evaluación del café."
)
ROUNDING = {"score": 1, "defects_pct": 1, "yield_factor": 1}


class ModelUnavailableError(DomainError):
    """El servidor no tiene un modelo que pueda usar."""

    status_code = 503


_bundle: Optional[dict] = None
_lock = threading.Lock()


def _read(path: Path) -> dict:
    if not path.exists():
        raise ModelUnavailableError("La proyección de calidad no está disponible: falta el modelo en este servidor")
    import joblib
    import numpy
    import sklearn

    bundle = joblib.load(path)
    trained = (bundle.get("sklearn_version"), bundle.get("numpy_version"))
    if trained != (sklearn.__version__, numpy.__version__):
        raise ModelUnavailableError(
            f"La proyección de calidad no está disponible: el modelo se entrenó con scikit-learn {trained[0]} "
            f"y numpy {trained[1]}, y el servidor tiene {sklearn.__version__} y {numpy.__version__}"
        )
    if list(bundle.get("features", [])) != list(FEATURE_NAMES):
        raise ModelUnavailableError("La proyección de calidad no está disponible: el modelo no corresponde a las "
                                    "features actuales y hay que reentrenarlo")
    return bundle


def load_model(path: Optional[Path] = None) -> dict:
    """El artefacto, leído una sola vez por proceso."""
    global _bundle
    if _bundle is None:
        with _lock:
            if _bundle is None:
                _bundle = _read(path or ARTIFACT)
    return _bundle


def reset_model() -> None:
    """Olvida el artefacto cargado (pruebas, o tras reemplazarlo)."""
    global _bundle
    _bundle = None


@dataclass
class Projection:
    crop_cycle_id: int
    cycle_number: int
    plot_id: int
    plot_name: str
    farm_id: int
    farm_name: str
    as_of: date
    score: float
    defects_pct: float
    yield_factor: float
    completeness: float
    stages: list[str]
    model_version: str
    disclaimer: str

    def as_dict(self) -> dict:
        return asdict(self)


def farm_references(db: Session, farm_ids: Iterable[int], as_of: date) -> dict[int, dict]:
    """Valor típico (mediana o moda) de cada feature en los secados cerrados de cada finca."""
    drying_ids = [
        row[0] for row in db.query(Drying.id).filter(
            Drying.farm_id.in_(list(farm_ids)), Drying.status == DryingStatusEnum.completed,
            Drying.end_date <= as_of,
        )
    ]
    by_farm: dict[int, list[dict]] = defaultdict(list)
    for row in build_features(db, drying_origins(db, drying_ids)):
        by_farm[row.farm_id].append(row.values)
    return {farm_id: reference_values(rows) for farm_id, rows in by_farm.items()}


def project_cycles(db: Session, cycle_ids: Iterable[int], as_of: date) -> list[Projection]:
    """Proyección de cada ciclo, en el orden de sus ids."""
    cycle_ids = sorted(set(cycle_ids))
    if not cycle_ids:
        return []
    bundle = load_model()
    rows = build_features(db, cycle_origins(db, cycle_ids, as_of))
    references = farm_references(db, {row.farm_id for row in rows}, as_of)
    filled = [fill_future_stages(row.values, row.stages, references.get(row.farm_id, {}), bundle["global_reference"])
              for row in rows]
    matrix = to_matrix(filled, bundle["vocabularies"])
    predictions = {target: bundle["models"][target].predict(matrix) for target in bundle["targets"]}
    info = {
        cycle_id: (number, plot_id, plot_name, farm_id, farm_name)
        for cycle_id, number, plot_id, plot_name, farm_id, farm_name in (
            db.query(CropCycle.id, CropCycle.cycle_number, Plot.id, Plot.name, Farm.id, Farm.name)
            .join(Plot, CropCycle.plot_id == Plot.id).join(Farm, Plot.farm_id == Farm.id)
            .filter(CropCycle.id.in_(cycle_ids))
        )
    }
    projections = []
    for i, row in enumerate(rows):
        number, plot_id, plot_name, farm_id, farm_name = info[row.key]
        value = {t: round(float(predictions[t][i]), ROUNDING[t]) for t in predictions}
        projections.append(Projection(
            crop_cycle_id=row.key, cycle_number=number, plot_id=plot_id, plot_name=plot_name,
            farm_id=farm_id, farm_name=farm_name, as_of=as_of,
            score=value["score"], defects_pct=value["defects_pct"], yield_factor=value["yield_factor"],
            completeness=round(row.completeness, 2),
            stages=[stage for stage in ("pre", "harvest", "wet", "drying") if stage in row.stages],
            model_version=bundle["version"], disclaimer=DISCLAIMER,
        ))
    return projections
