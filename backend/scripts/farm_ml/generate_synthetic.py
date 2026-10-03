"""
Generador de datos sintéticos del módulo de cultivo (generador-sintetico-ml).

Puebla la base con fincas, lotes, ciclos, labores, cosechas, beneficios,
secados y evaluaciones de calidad coherentes entre sí, bajo un caficultor
marcado que `--wipe` borra completo. Valida el resultado, escribe la
auditoría de latentes y la huella del dataset.

Solo corre en desarrollo, pruebas o un entorno de demostración: nunca con
`ENV=production` (las fincas ficticias no se mezclan con las reales).

    docker compose run --rm <servicio> python -m scripts.farm_ml.generate_synthetic --help
"""

import argparse
import sys
import time
from dataclasses import dataclass, replace
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app import models_registry  # noqa: F401  (registra todos los modelos)
from app.core.config import settings
from app.farm_operations.services.dates import business_today
from app.models.product import Product
from scripts.farm_ml import audit, catalogs, rules
from scripts.farm_ml.persist import Persisted, Persister, synthetic_farmer
from scripts.farm_ml.validate import Report, validate
from scripts.farm_ml.wipe import wipe_synthetic
from scripts.farm_ml.world import Params, World, simulate


class GeneratorError(Exception):
    """El generador no puede correr con esta base o estos parámetros."""


@dataclass
class Result:
    world: World
    persisted: Persisted
    report: Report
    fingerprint: str
    audit_path: Optional[Path] = None
    report_path: Optional[Path] = None
    seconds: float = 0.0


def ensure_allowed() -> None:
    if settings.ENV == "production":
        raise GeneratorError(
            "El generador no corre en producción: las fincas sintéticas no se mezclan con las reales. "
            "Úsalo en desarrollo, pruebas o un entorno de demostración."
        )


def ensure_audit_tools() -> None:
    """La auditoría necesita pyarrow: se comprueba antes de escribir nada en la base."""
    try:
        import pyarrow  # noqa: F401
    except ImportError:
        raise GeneratorError(
            "Falta pyarrow (requirements-dev.txt): esta imagen no es la de desarrollo. Reconstrúyela con "
            "`docker compose -f docker-compose.test.yml build tests` y vuelve a correr el generador."
        ) from None


def generate(db: Session, params: Params, wipe: bool = False, output: Optional[Path] = None, progress=None) -> Result:
    """Genera, escribe, valida y audita un dataset. `output=None` no escribe archivos."""
    ensure_allowed()
    started = time.monotonic()
    if params.end_date >= business_today():
        raise GeneratorError("La fecha final debe ser anterior a hoy: nada del dataset puede quedar en el futuro")
    if params.farms > len(catalogs.FARM_NAMES):
        raise GeneratorError(
            f"Hay {len(catalogs.FARM_NAMES)} nombres de finca en el catálogo y cada finca usa uno distinto: "
            f"no se pueden generar {params.farms} fincas"
        )
    if output is not None:
        ensure_audit_tools()
    if synthetic_farmer(db) is not None:
        if not wipe:
            raise GeneratorError("Ya hay datos sintéticos en esta base: usa --wipe para reemplazarlos")
        wipe_synthetic(db)

    inventory_available = db.query(Product.id).filter(Product.type == "other").first() is not None
    params = replace(params, inventory_available=inventory_available)
    world = simulate(params)
    persisted = Persister(db, world).run(progress)
    report = validate(db, world, persisted)
    result = Result(world, persisted, report, audit.fingerprint(db))
    if output is not None:
        result.audit_path = audit.write_audit(world, persisted, output)
        result.report_path = audit.write_report(world, {
            "rules_version": rules.RULES_VERSION, "seed": params.seed, "end_date": params.end_date,
            "missing_level": params.missing_level, "fingerprint": result.fingerprint,
            "counts": persisted.counts, **report.as_dict(),
        }, output)
    result.seconds = time.monotonic() - started
    return result


# ── Línea de comandos ─────────────────────────────────────────────────────


def plot_range(text: str) -> tuple[int, int]:
    low, _, high = text.partition("-")
    low_value, high_value = int(low), int(high or low)
    if not 1 <= low_value <= high_value <= 12:
        raise argparse.ArgumentTypeError("usa un número o un rango como 2-6 (máximo 12)")
    return low_value, high_value


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.farm_ml.generate_synthetic",
        description="Genera datos sintéticos del módulo de cultivo (fincas, ciclos, cosechas, beneficio, secado y calidad).",
    )
    parser.add_argument("--farms", type=int, default=12,
                        help=f"fincas sintéticas, cada una con un nombre distinto (12; máximo {len(catalogs.FARM_NAMES)})")
    parser.add_argument("--plots-per-farm", type=plot_range, default=(2, 6), help="lotes por finca: número o rango (2-6)")
    parser.add_argument("--years", type=int, default=5, help="años simulados hacia atrás (5)")
    parser.add_argument("--seed", type=int, default=42, help="semilla: mismo dataset con la misma semilla (42)")
    parser.add_argument("--missing-level", choices=sorted(rules.MISSING_LEVELS), default="realistic",
                        help="datos que el caficultor no registra (realistic)")
    parser.add_argument("--end-date", type=date.fromisoformat, default=None,
                        help="último día simulado, AAAA-MM-DD (ayer); fija el dataset junto con la semilla")
    parser.add_argument("--wipe", action="store_true", help="borra lo sintético antes de generar")
    parser.add_argument("--only-wipe", action="store_true", help="solo borra lo sintético")
    parser.add_argument("--output", type=Path, default=audit.OUTPUT_DIR, help="carpeta de la auditoría y el reporte")
    args = parser.parse_args(argv)
    if args.farms < 1 or args.years < 1:
        parser.error("--farms y --years deben ser al menos 1")
    return args


def print_report(result: Result) -> None:
    counts = result.persisted.counts
    print("\nRegistros escritos:")
    for name in sorted(counts):
        print(f"  {name:22s} {counts[name]:>8,}".replace(",", "."))
    print("\nValidación:")
    for check in result.report.checks:
        mark = "OK " if check.ok else ("ERR" if check.severity == "error" else "ADV")
        print(f"  [{mark}] {check.name}: {check.detail}")
    if not result.world.params.inventory_available:
        print("\nAviso: el inventario no tiene producto de pergamino (tipo «other»): los secados que irían "
              "al inventario quedaron guardados en la finca.")
    print(f"\nHuella del dataset: {result.fingerprint}")
    if result.audit_path:
        print(f"Auditoría: {result.audit_path}")
        print(f"Reporte:   {result.report_path}")
    print(f"Tiempo: {result.seconds:.0f} s")


def main(argv: Optional[list] = None) -> int:
    from app.core.db.base import engine
    from app.core.db.session import SessionLocal

    engine.echo = False   # decenas de miles de inserciones: sin eco de SQL en la consola
    args = parse_args(argv)
    try:
        ensure_allowed()
    except GeneratorError as error:
        print(f"✗ {error}", file=sys.stderr)
        return 2
    print(f"Base: {settings.DB_NAME} en {settings.DB_HOST} (ENV={settings.ENV})")

    db = SessionLocal()
    try:
        if args.only_wipe:
            deleted = wipe_synthetic(db)
            print("Borrado: " + ", ".join(f"{name} {n}" for name, n in deleted.items() if n))
            return 0
        params = Params(
            end_date=args.end_date or business_today() - timedelta(days=1),
            farms=args.farms, plots_per_farm=args.plots_per_farm, years=args.years,
            seed=args.seed, missing_level=args.missing_level,
        )
        print(f"Generando {params.farms} fincas, {params.years} años hasta {params.end_date} "
              f"(semilla {params.seed}, reglas {rules.RULES_VERSION}, faltantes {params.missing_level})…")
        result = generate(db, params, wipe=args.wipe, output=args.output,
                          progress=lambda farm: print(f"  ✓ {farm.name} ({farm.municipality.name})"))
    except GeneratorError as error:
        print(f"✗ {error}", file=sys.stderr)
        return 2
    finally:
        db.close()

    print_report(result)
    if not result.report.passed:
        print("\n✗ La validación falló: revisa el reporte; `--only-wipe` borra lo generado.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
