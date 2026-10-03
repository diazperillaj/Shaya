"""
Artefacto de auditoría y huella del dataset (generador-sintetico-ml §3.7).

- La auditoría guarda, por cada secado cerrado, las variables latentes que
  produjeron sus targets: nivel de manejo, valores verdaderos ponderados por
  la cereza trazada, componentes de q_s y ruidos sorteados. Vive fuera de la
  base (parquet en `scripts/farm_ml/output/`) y **jamás entra como feature**.
- La huella resume el contenido sintético de la base sin ids: dos corridas
  con los mismos parámetros dan la misma huella.
"""

import hashlib
import json
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.farm_operations.models import Supply
from scripts.farm_ml import rules
from scripts.farm_ml.persist import Persisted
from scripts.farm_ml.wipe import synthetic_scope
from scripts.farm_ml.world import World

OUTPUT_DIR = Path(__file__).parent / "output"


def dataset_name(world: World) -> str:
    p = world.params
    return f"r{rules.RULES_VERSION}_s{p.seed}_{p.end_date.isoformat()}_{p.missing_level}"


def audit_rows(world: World, persisted: Optional[Persisted] = None) -> list[dict]:
    rows = []
    for farm in world.farms:
        for drying in farm.dryings:
            if not drying.audit:
                continue
            db_drying = persisted.dryings.get(drying.key) if persisted else None
            rows.append({
                "drying_key": drying.key,
                "drying_id": db_drying.id if db_drying is not None else None,
                "farm_key": farm.key,
                "farm_name": farm.name,
                "start_date": drying.start,
                "end_date": drying.end,
                "method": drying.method,
                "destination": drying.destination,
                "quality_recorded": bool(drying.quality and drying.quality.recorded),
                **drying.audit,
            })
    return rows


def write_audit(world: World, persisted: Persisted, directory: Path = OUTPUT_DIR) -> Path:
    """Escribe la auditoría en parquet, con los parámetros del dataset como metadatos."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"audit_{dataset_name(world)}.parquet"
    table = pa.Table.from_pylist(audit_rows(world, persisted))
    p = world.params
    metadata = {
        "rules_version": rules.RULES_VERSION, "seed": str(p.seed), "end_date": p.end_date.isoformat(),
        "years": str(p.years), "farms": str(p.farms), "missing_level": p.missing_level,
    }
    table = table.replace_schema_metadata({**(table.schema.metadata or {}), **{k: v.encode() for k, v in metadata.items()}})
    pq.write_table(table, path)
    return path


def write_report(world: World, report: dict, directory: Path = OUTPUT_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"validation_{dataset_name(world)}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def _plain(value):
    if isinstance(value, Decimal):
        return str(value.normalize())
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):   # enums
        return value.value
    return value


def fingerprint(db: Session) -> str:
    """
    SHA-256 del contenido sintético, sin ids ni fechas de creación.

    Cada llave foránea se reemplaza por la posición de la fila referida dentro
    de su tabla (en orden de inserción); los insumos, que son catálogo
    compartido, por su nombre.
    """
    scope = synthetic_scope()
    positions: dict[str, dict[int, int]] = {}
    rows_by_table: dict[str, list] = {}
    for name, (model, ids) in scope.items():
        table = model.__table__
        rows = db.execute(select(table).where(table.c.id.in_(ids)).order_by(table.c.id)).mappings().all()
        positions[name] = {row["id"]: n for n, row in enumerate(rows)}
        rows_by_table[name] = (table, rows)
    supply_names = dict(db.query(Supply.id, Supply.name).all())
    # El puente al inventario cita el id del secado en las observaciones
    drying_position = lambda match: f"secado #{positions['dryings'].get(int(match.group(1)), 'externo')}"  # noqa: E731

    canonical = {}
    for name, (table, rows) in rows_by_table.items():
        foreign = {
            column.name: next(iter(column.foreign_keys)).column.table.name
            for column in table.columns if column.foreign_keys
        }
        items = []
        for row in rows:
            item = []
            for column, value in row.items():
                if column in ("id", "created_at"):
                    continue
                if column in foreign and value is not None:
                    target = foreign[column]
                    value = supply_names.get(value) if target == "supplies" else positions.get(target, {}).get(value, "externo")
                elif name == "inventories" and column == "observations" and value:
                    value = re.sub(r"secado (\d+)", drying_position, value)
                item.append((column, _plain(value)))
            items.append(item)
        canonical[name] = items
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
