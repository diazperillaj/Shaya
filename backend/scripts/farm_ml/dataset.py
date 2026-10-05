"""
Dataset del modelo de calidad (generador-sintetico-ml §4–§5).

Una fila por secado cerrado con su evaluación en pergamino: las features de
`app/farm_operations/ml/features.py` (la misma extracción de la
proyección), los tres targets, la finca (el grupo de la validación) y la
completitud de la fila.

    python -m scripts.farm_ml.dataset --farms 130 --years 8 --end-date 2026-09-30

genera el mundo dos veces, con faltantes realistas y sin faltantes (el mismo
mundo, G15), y guarda los dos datasets en parquet con sus metadatos. Borra
lo sintético antes de cada corrida: va en la base efímera de pruebas, nunca
en una base con datos reales.
"""

import argparse
import json
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.farm_operations.ml.features import FEATURE_NAMES, build_features, drying_origins
from app.farm_operations.models import Drying, QualityEval
from app.farm_operations.models.enums import DryingStatusEnum, QualityStageEnum
from scripts.farm_ml import rules
from scripts.farm_ml.audit import OUTPUT_DIR
from scripts.farm_ml.generate_synthetic import GeneratorError, console_log, generate, plot_range
from scripts.farm_ml.wipe import synthetic_scope
from scripts.farm_ml.world import Params

# La humedad del pergamino no se predice: depende solo del secado y el caficultor
# la mide al cerrarlo, así que proyectarla no le aporta nada (sigue como feature)
TARGETS = ("score", "defects_pct", "yield_factor")
MISSING_LEVELS = ("realistic", "none")
DATASET_DIR = OUTPUT_DIR / "ml"


def dataset_stem(params: Params) -> str:
    return (f"dataset_r{rules.RULES_VERSION}_s{params.seed}_{params.end_date.isoformat()}"
            f"_{params.farms}f{params.years}y_{params.missing_level}")


def extract(db: Session) -> list[dict]:
    """Filas de los secados sintéticos cerrados con los tres targets."""
    farms = synthetic_scope()["farms"][1]
    evals = (
        db.query(QualityEval.drying_id, QualityEval.score, QualityEval.defects_pct, QualityEval.yield_factor)
        .join(Drying, QualityEval.drying_id == Drying.id)
        .filter(
            QualityEval.stage == QualityStageEnum.parchment,
            Drying.status == DryingStatusEnum.completed,
            Drying.farm_id.in_(farms),
        )
        .order_by(QualityEval.eval_date, QualityEval.id)
        .all()
    )
    targets = {}
    for drying_id, *values in evals:
        if all(value is not None for value in values):
            targets[drying_id] = dict(zip(TARGETS, (float(value) for value in values)))
    rows = []
    for row in build_features(db, drying_origins(db, targets)):
        rows.append({
            "drying_id": row.key,
            "farm_id": row.farm_id,
            "end_date": row.as_of,
            "completeness": round(row.completeness, 3),
            **row.values,
            **targets[row.key],
        })
    return rows


def write(rows: list[dict], path: Path, meta: dict) -> None:
    import pandas as pd

    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows, columns=["drying_id", "farm_id", "end_date", "completeness", *FEATURE_NAMES, *TARGETS])
    frame.to_parquet(path, index=False)
    path.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def build(db: Session, params: Params, output: Path = DATASET_DIR, log=None) -> dict[str, Path]:
    """Genera y extrae los dos datasets (realista y sin faltantes) del mismo mundo."""
    log = log or (lambda message: None)
    paths = {}
    for level in MISSING_LEVELS:
        level_params = replace(params, missing_level=level)
        log(f"Dataset {level}: generando el mundo…")
        result = generate(db, level_params, wipe=True, output=output, log=lambda m: log(f"  {m}"))
        if not result.report.passed:
            raise GeneratorError(f"La validación del dataset {level} falló: revisa {result.report_path}")
        log(f"Dataset {level}: extrayendo las features…")
        rows = extract(db)
        path = output / f"{dataset_stem(level_params)}.parquet"
        write(rows, path, {
            "rules_version": rules.RULES_VERSION, "seed": params.seed, "end_date": params.end_date,
            "farms": params.farms, "years": params.years, "plots_per_farm": list(params.plots_per_farm),
            "missing_level": level, "fingerprint": result.fingerprint, "rows": len(rows),
            "farms_with_rows": len({row["farm_id"] for row in rows}), "counts": result.persisted.counts,
        })
        log(f"Dataset {level}: {len(rows):,} filas → {path}".replace(",", "."))
        paths[level] = path
    return paths


def main(argv: Optional[list] = None) -> int:
    from app.core.db.base import engine
    from app.core.db.session import SessionLocal

    sys.stdout.reconfigure(line_buffering=True)
    engine.echo = False
    parser = argparse.ArgumentParser(description="Datasets del modelo de calidad (realista y sin faltantes)")
    parser.add_argument("--farms", type=int, default=130, help="fincas sintéticas (130)")
    parser.add_argument("--years", type=int, default=8, help="años simulados (8)")
    parser.add_argument("--plots-per-farm", type=plot_range, default=(2, 6), help="lotes por finca (2-6)")
    parser.add_argument("--seed", type=int, default=42, help="semilla (42)")
    parser.add_argument("--end-date", type=date.fromisoformat, required=True,
                        help="último día simulado: fija el dataset (obligatoria para que sea reproducible)")
    parser.add_argument("--output", type=Path, default=DATASET_DIR, help="carpeta de los datasets")
    args = parser.parse_args(argv)
    params = Params(end_date=args.end_date, farms=args.farms, plots_per_farm=args.plots_per_farm,
                    years=args.years, seed=args.seed)
    db = SessionLocal()
    try:
        build(db, params, args.output, log=console_log())
    except GeneratorError as error:
        print(f"✗ {error}", file=sys.stderr)
        return 2
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
