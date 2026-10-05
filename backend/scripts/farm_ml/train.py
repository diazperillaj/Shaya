"""
Entrenamiento del modelo de calidad (generador-sintetico-ml §5).

    python -m scripts.farm_ml.train --dataset scripts/farm_ml/output/ml/dataset_…_realistic.parquet

Un `HistGradientBoostingRegressor` por target. Valida con GroupKFold por
finca contra la media y la regresión lineal, entrena con todo el dataset y
guarda el artefacto versionado en `app/farm_operations/ml/artifacts/`. El
artefacto lleva lo necesario para proyectar sin el dataset: vocabularios de
las categóricas, valores de referencia para las etapas futuras, métricas y
la identidad del dataset (reglas, semilla, fecha final, escala).
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import sklearn

from app.farm_operations.ml.features import FEATURE_NAMES, reference_values
from scripts.farm_ml.dataset import TARGETS
from scripts.farm_ml.modeling import GBM_PARAMS, MODELS, TARGET_LABELS, cross_validate, fit, fold_metrics, folds, load, metrics

ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "app" / "farm_operations" / "ml" / "artifacts"


def train(dataset_path: Path, version: str) -> dict:
    data = load(dataset_path)
    splits = folds(data.groups)
    cv = cross_validate(data, splits)
    scores = {}
    for target in TARGETS:
        y = data.y(target)
        scores[target] = {
            name: {**metrics(y, cv["predictions"][name][target]),
                   "folds": fold_metrics(y, cv["predictions"][name][target], splits)}
            for name in cv["predictions"]
        }
    models = {target: fit(MODELS["gbm"], data.X, data.y(target)) for target in TARGETS}
    return {
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "features": list(FEATURE_NAMES),
        "targets": list(TARGETS),
        "vocabularies": data.vocab,
        "global_reference": reference_values(data.records),
        "models": models,
        "params": GBM_PARAMS,
        "metrics": scores,
        "dataset": {**data.meta, "file": dataset_path.name, "rows": len(data.frame),
                    "farms_with_rows": int(len(set(data.groups)))},
    }


def main(argv: Optional[list] = None) -> int:
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description="Entrena el modelo de calidad")
    parser.add_argument("--dataset", type=Path, required=True, help="dataset realista (parquet)")
    parser.add_argument("--version", default="v1", help="versión del artefacto (v1)")
    parser.add_argument("--artifacts", type=Path, default=ARTIFACTS_DIR, help="carpeta de los artefactos")
    args = parser.parse_args(argv)

    bundle = train(args.dataset, args.version)
    args.artifacts.mkdir(parents=True, exist_ok=True)
    path = args.artifacts / f"quality_model_{args.version}.joblib"
    joblib.dump(bundle, path, compress=3)

    d = bundle["dataset"]
    rows = f"{d['rows']:,}".replace(",", ".")
    print(f"Dataset: {rows} secados de {d['farms_with_rows']} fincas "
          f"(reglas {d.get('rules_version')}, semilla {d.get('seed')}, hasta {d.get('end_date')})")
    print("Validación cruzada por finca (5 folds), MAE · R²:")
    for target in TARGETS:
        cells = "   ".join(f"{name} {m['mae']:.3f} · {m['r2']:.3f}" for name, m in bundle["metrics"][target].items())
        print(f"  {TARGET_LABELS[target]:22s} {cells}")
    print(f"Artefacto: {path} ({path.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
