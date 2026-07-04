#!/usr/bin/env python3
"""
Importación de datos desde backend/data/Inventario.xlsx a la BD Shaya.
Ejecutar desde el directorio backend/:  python scripts/import_excel.py
"""
import sys
from datetime import datetime, date, timezone, time as time_type
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import openpyxl
from passlib.context import CryptContext
from sqlalchemy import text

# Registrar todos los modelos antes de usar ORM
from app.core.db.base import Base  # noqa: F401
import app.models.person           # noqa: F401
import app.models.user             # noqa: F401
import app.models.farmer           # noqa: F401
import app.models.customer         # noqa: F401
import app.models.product          # noqa: F401
import app.models.inventory        # noqa: F401
import app.models.parchment        # noqa: F401
import app.models.process          # noqa: F401
import app.models.detail_process   # noqa: F401
import app.models.roasted_coffe    # noqa: F401
import app.models.detail_roasted_coffe  # noqa: F401
import app.models.sale             # noqa: F401
import app.models.detail_sale      # noqa: F401
import app.models.inventory_movement   # noqa: F401
import app.models.roasted_movement     # noqa: F401
import app.models.fair             # noqa: F401
import app.models.fair_inventory   # noqa: F401
import app.models.fair_sale        # noqa: F401
import app.models.fair_expense     # noqa: F401

from app.core.db.session import SessionLocal
from app.models.person import Person
from app.models.user import User
from app.models.farmer import Farmer
from app.models.customer import Customer
from app.models.product import Product, ProductTypeEnum
from app.models.inventory import Inventory
from app.models.parchment import Parchment
from app.models.process import Process
from app.models.detail_process import DetailProcess
from app.models.roasted_coffe import RoastedCoffee
from app.models.detail_roasted_coffe import DetailRoastedCoffee
from app.models.sale import Sale, SaleStatusEnum
from app.models.detail_sale import DetailSale
from app.models.roasted_movement import MovementDirectionEnum, RoastedMovement, RoastedMovementDetail

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
EXCEL_PATH = Path(__file__).parent.parent / "data" / "Inventario.xlsx"
DEFAULT_PASSWORD = "shaya2026"
IMPORT_DATE = date(2026, 1, 1)  # fecha por defecto para registros sin fecha

# Procesos placeholder en el Excel (todas las filas con fecha=1900)
SKIP_PROCESS_IDS = {3, 4}

# Mapeo columna de Movements -> product_id
MOV_PROD_COLS = {3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def to_date(v) -> date:
    """Convierte valor de celda Excel a date. Devuelve IMPORT_DATE si es nulo/época."""
    if v is None or isinstance(v, time_type):
        return IMPORT_DATE
    if isinstance(v, datetime):
        return IMPORT_DATE if v.year <= 1900 else v.date()
    if isinstance(v, date):
        return IMPORT_DATE if v.year <= 1900 else v
    return IMPORT_DATE


def to_dt(v) -> datetime:
    # Mediodia local (naive) para que la fecha no se corra al cambiar de zona horaria
    d = to_date(v)
    return datetime(d.year, d.month, d.day, 12, 0, 0)


def to_dec(v, default: Decimal = Decimal("0.00")) -> Decimal:
    if v is None:
        return default
    try:
        s = str(v).strip()
        return Decimal(s) if s else default
    except InvalidOperation:
        return default


def read_sheet_rows(wb, sheet_name: str) -> list:
    """Devuelve las filas de datos (omite la fila de título y la fila de encabezados)."""
    ws = wb[sheet_name]
    header_skipped = False
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if all(v is None for v in row):
            continue
        if not header_skipped:
            header_skipped = True
            continue
        rows.append(row)
    return rows


# ─── Truncate ─────────────────────────────────────────────────────────────────

def truncate_all(db) -> None:
    print("Truncando todas las tablas...", end=" ", flush=True)
    db.execute(text(
        "TRUNCATE TABLE "
        "fair_expenses, fair_sales, fair_inventories, fairs, "
        "roasted_movement_details, roasted_movements, "
        "inventory_movements, "
        "detail_sales, sales, "
        "detail_roasted_coffees, roasted_coffees, "
        "detail_processes, processes, "
        "parchments, inventories, "
        "customers, farmers, users, persons, "
        "products "
        "RESTART IDENTITY CASCADE"
    ))
    db.commit()
    print("OK")


# ─── Reset sequences ──────────────────────────────────────────────────────────

def reset_sequences(db) -> None:
    print("Reiniciando secuencias...", end=" ", flush=True)
    tables = [
        "persons", "products", "inventories", "parchments",
        "processes", "detail_processes", "roasted_coffees",
        "detail_roasted_coffees", "sales", "detail_sales",
        "roasted_movements", "roasted_movement_details",
        "inventory_movements", "farmers", "customers", "users",
    ]
    for table in tables:
        db.execute(text(
            f"SELECT setval("
            f"pg_get_serial_sequence('{table}', 'id'), "
            f"COALESCE((SELECT MAX(id) FROM {table}), 1)"
            f")"
        ))
    db.commit()
    print("OK")


# ─── Step 1: Products ─────────────────────────────────────────────────────────

def import_products(db, wb) -> int:
    """Importa productos y crea el producto interno 'Café Pergamino'. Retorna su ID."""
    print("Importando productos...", end=" ", flush=True)
    rows = read_sheet_rows(wb, "Products")

    for row in rows:
        pid, name, qty_g, desc = row[0], row[1], row[2], row[3]
        if pid is None:
            continue
        pid = int(pid)
        qty = int(qty_g) if qty_g not in (None, "") else 0

        if 1 <= pid <= 6:
            ptype = ProductTypeEnum.processed
            generates = True
        else:
            ptype = ProductTypeEnum.other
            generates = False

        db.add(Product(
            id=pid,
            name=str(name),
            quantity=qty,
            type=ptype,
            description=str(desc) if desc else None,
            active=True,
            generates_inventory=generates,
        ))

    # Producto interno para los Inventories de pergamino (no visible en frontend)
    parchment_prod = Product(
        id=100,
        name="Café Pergamino",
        quantity=0,
        type=ProductTypeEnum.parchment,
        description="Producto interno para trazabilidad de pergamino importado",
        active=False,
        generates_inventory=True,
    )
    db.add(parchment_prod)
    db.flush()
    print(f"OK ({len(rows)} productos + 1 pergamino [id={parchment_prod.id}])")
    return parchment_prod.id


# ─── Step 2: Farmers ──────────────────────────────────────────────────────────

def import_farmers(db, wb) -> None:
    print("Importando caficultores...", end=" ", flush=True)
    rows = read_sheet_rows(wb, "Farmers")

    for row in rows:
        fid, name, farm, village, municipality, altitude = row
        if fid is None:
            continue
        fid = int(fid)

        person = Person(
            full_name=str(name),
            phone=None,
            email=None,
            document=None,
            observation=f"Altura: {altitude}" if altitude else None,
        )
        db.add(person)
        db.flush()

        db.add(Farmer(
            id=fid,
            farm_name=str(farm) if farm else "Sin finca",
            village=str(village) if village else "Sin vereda",
            municipality=str(municipality) if municipality else "Sin municipio",
            person_id=person.id,
        ))
        db.flush()

    print(f"OK ({len(rows)} caficultores)")


# ─── Step 3: Customers ────────────────────────────────────────────────────────

def import_customers(db, wb) -> None:
    print("Importando clientes...", end=" ", flush=True)
    rows = read_sheet_rows(wb, "Customers")

    for row in rows:
        cid, name, phone, obs = row[0], row[1], row[2], row[3]
        if cid is None:
            continue
        cid = int(cid)

        person = Person(
            full_name=str(name),
            phone=str(int(phone)) if phone else None,
            email=None,
            document=None,
            observation=str(obs) if obs else None,
        )
        db.add(person)
        db.flush()

        db.add(Customer(
            id=cid,
            customerType="Regular",
            address=None,
            city="Sin ciudad",
            person_id=person.id,
        ))
        db.flush()

    print(f"OK ({len(rows)} clientes)")


# ─── Step 4: Users ────────────────────────────────────────────────────────────

def import_users(db, wb) -> None:
    print("Importando usuarios...", end=" ", flush=True)
    rows = read_sheet_rows(wb, "Users")
    hashed_pw = pwd_ctx.hash(DEFAULT_PASSWORD)
    count = 0

    for row in rows:
        uid, name, phone, obs = row[0], row[1], row[2], row[3]
        if uid is None or int(uid) == 0:
            continue
        uid = int(uid)

        slug = (str(name).lower()
                .replace(" ", "_")
                .replace("á", "a").replace("é", "e")
                .replace("í", "i").replace("ó", "o").replace("ú", "u"))

        person = Person(
            full_name=str(name),
            phone=str(int(phone)) if phone else None,
            email=None,
            document=None,
            observation=str(obs) if obs else None,
        )
        db.add(person)
        db.flush()

        db.add(User(
            id=uid,
            username=slug,
            hashed_password=hashed_pw,
            role="admin" if uid == 1 else "user",
            person_id=person.id,
        ))
        db.flush()
        count += 1

    print(f"OK ({count} usuarios  |  contraseña por defecto: '{DEFAULT_PASSWORD}')")


# ─── Step 5: Inventories + Parchments (sintéticos, uno por proceso) ───────────

def import_parchments(db, wb, parchment_product_id: int) -> dict:
    """Crea Inventory + Parchment para cada proceso. Retorna {excel_process_id: parchment_id}."""
    print("Importando pergaminos...", end=" ", flush=True)
    rows = read_sheet_rows(wb, "Process")
    parchment_map: dict[int, int] = {}

    for row in rows:
        pid = row[0]
        if pid is None:
            continue
        pid = int(pid)
        if pid in SKIP_PROCESS_IDS:
            continue

        parchment_kg = to_dec(row[8], Decimal("1.000"))
        farmer_id = int(row[11]) if row[11] is not None else 0
        variety = str(row[7]) if row[7] not in (None, "No") else "Sin variedad"
        process_date = to_date(row[2])

        inv = Inventory(
            product_id=parchment_product_id,
            date=to_dt(row[2]),
            quantity=parchment_kg,
            observations=f"Pergamino proceso {pid} - {variety}",
        )
        db.add(inv)
        db.flush()

        parchment = Parchment(
            inventory_id=inv.id,
            farmer_id=farmer_id,
            variety=variety,
            altitude=None,
            humidity=None,
            purchase_price=Decimal("0.00"),
            full_price=Decimal("0.00"),
            initial_quantity=parchment_kg,
            remaining_quantity=Decimal("0.000"),
            purchase_date=process_date,
            origin_batch=str(pid),
        )
        db.add(parchment)
        db.flush()
        parchment_map[pid] = parchment.id

    print(f"OK ({len(parchment_map)} pergaminos)")
    return parchment_map


# ─── Step 6: Processes ────────────────────────────────────────────────────────

def import_processes(db, wb, parchment_map: dict) -> None:
    print("Importando procesos...", end=" ", flush=True)
    rows = read_sheet_rows(wb, "Process")
    count = 0

    for row in rows:
        pid = row[0]
        if pid is None:
            continue
        pid = int(pid)
        if pid in SKIP_PROCESS_IDS:
            continue
        if pid not in parchment_map:
            print(f"\n  [WARN] Proceso {pid}: sin pergamino, saltado")
            continue

        db.add(Process(
            id=pid,
            invoice_number=str(int(row[6])) if row[6] not in (None, "") else "0",
            process_date=to_date(row[2]),
            parchment_id=parchment_map[pid],
            parchment_kg=to_dec(row[8], Decimal("1.000")),
            resultant_kg=to_dec(row[9]),
            yield_percentage=to_dec(row[10]),
            subtotal=to_dec(row[3]),
            iva=to_dec(row[4]),
            total=to_dec(row[5]),
            observations=str(row[13]) if row[13] else None,
        ))
        count += 1

    db.flush()
    print(f"OK ({count} procesos)")


# ─── Step 7: DetailProcess ────────────────────────────────────────────────────

def import_detail_processes(db, wb) -> None:
    print("Importando detalles de proceso...", end=" ", flush=True)
    rows = read_sheet_rows(wb, "Process_Detail")
    count = 0

    for row in rows:
        did, proc_id, fecha = int(row[0]) if row[0] is not None else None, row[1], row[2]
        prod_id, bags = row[3], row[5]
        grams_total, unit_val, iva, total, obs = row[6], row[7], row[8], row[9], row[10]

        if proc_id is None or prod_id is None:
            continue
        proc_id = int(proc_id)
        if proc_id in SKIP_PROCESS_IDS:
            continue

        bags = int(bags) if bags is not None else 0
        if bags == 0 and to_dec(total) == Decimal("0.00"):
            continue  # fila placeholder

        prod_id = int(prod_id)
        grams_total_dec = to_dec(grams_total)
        gpb = int(grams_total_dec / bags) if bags > 0 and grams_total_dec > 0 else 0

        kwargs = dict(
            process_id=proc_id,
            date=to_date(fecha),
            product_id=prod_id,
            bag_quantity=bags,
            grams_per_bag=gpb,
            unit_value=to_dec(unit_val),
            iva=to_dec(iva),
            total=to_dec(total),
            observations=str(obs) if obs else None,
        )
        if did is not None:
            kwargs["id"] = did

        db.add(DetailProcess(**kwargs))
        count += 1

    db.flush()
    print(f"OK ({count} detalles)")


# ─── Step 8: RoastedCoffee ────────────────────────────────────────────────────

def import_roasted_coffees(db, parchment_map: dict) -> dict:
    """Crea un RoastedCoffee por proceso. Retorna {process_id: roasted_coffee_id}."""
    print("Importando roasted_coffees...", end=" ", flush=True)
    rc_map: dict[int, int] = {}

    for proc_id in sorted(parchment_map.keys()):
        rc = RoastedCoffee(
            process_id=proc_id,
            observations=f"Inventario generado del proceso {proc_id}",
        )
        db.add(rc)
        db.flush()
        rc_map[proc_id] = rc.id

    print(f"OK ({len(rc_map)} lotes)")
    return rc_map


# ─── Step 9: DetailRoastedCoffee ─────────────────────────────────────────────

def import_detail_roasted_coffees(db, wb, rc_map: dict) -> dict:
    """
    Crea DetailRoastedCoffee desde Process_Detail (cantidades originales)
    y Inventory (cantidades actuales / remaining).
    Retorna {(process_id, product_id): drc_id}.
    """
    print("Importando detail_roasted_coffees...", end=" ", flush=True)

    # Cantidades actuales desde hoja Inventory
    remaining: dict[tuple, int] = {}
    for row in read_sheet_rows(wb, "Inventory"):
        _, prod_id, lote = row[0], row[1], row[2]
        qty = row[5]
        if lote is None or prod_id is None:
            continue
        remaining[(int(lote), int(prod_id))] = int(qty) if qty else 0

    # Cantidades originales desde Process_Detail
    original: dict[tuple, int] = {}
    for row in read_sheet_rows(wb, "Process_Detail"):
        _, proc_id, _, prod_id, _, bags = row[0], row[1], row[2], row[3], row[4], row[5]
        if proc_id is None or prod_id is None:
            continue
        proc_id = int(proc_id)
        if proc_id in SKIP_PROCESS_IDS:
            continue
        prod_id = int(prod_id)
        # prod 0 = "Sin tipo": lineas de costos (bolsas, seleccion), no inventario
        if prod_id == 0:
            continue
        if bags and int(bags) > 0:
            original[(proc_id, prod_id)] = int(bags)

    drc_map: dict[tuple, int] = {}

    # DRCs para procesos 1, 2, 5, 6
    for (proc_id, prod_id), bags in original.items():
        if proc_id not in rc_map:
            continue
        rem = remaining.get((proc_id, prod_id), 0)
        drc = DetailRoastedCoffee(
            roasted_coffee_id=rc_map[proc_id],
            product_id=prod_id,
            quantity=bags,
            remaining_quantity=rem,
        )
        db.add(drc)
        db.flush()
        drc_map[(proc_id, prod_id)] = drc.id

    # DRCs para proceso 0 (ventas y movimientos previos al sistema)
    p0_products: set[int] = set()
    for row in read_sheet_rows(wb, "Sales"):
        if row[6] is not None and int(row[6]) == 0 and row[3] is not None:
            p0_products.add(int(row[3]))
    for row in read_sheet_rows(wb, "Movements"):
        if row[2] is not None and int(row[2]) == 0:
            for col_idx, prod_id in MOV_PROD_COLS.items():
                val = row[col_idx]
                if val is not None and val != 0:
                    p0_products.add(prod_id)

    if 0 in rc_map:
        for prod_id in sorted(p0_products):
            if (0, prod_id) not in drc_map:
                rem = remaining.get((0, prod_id), 0)
                drc = DetailRoastedCoffee(
                    roasted_coffee_id=rc_map[0],
                    product_id=prod_id,
                    quantity=0,
                    remaining_quantity=rem,
                )
                db.add(drc)
                db.flush()
                drc_map[(0, prod_id)] = drc.id

    print(f"OK ({len(drc_map)} registros)")
    return drc_map


# ─── Step 10: Sales + DetailSale ─────────────────────────────────────────────

def import_sales(db, wb, drc_map: dict) -> None:
    print("Importando ventas...", end=" ", flush=True)
    rows = read_sheet_rows(wb, "Sales")
    used_ids: set[int] = set()
    count = 0
    warnings = 0

    for row in rows:
        sid, fecha, user_id, prod_id = row[0], row[1], row[2], row[3]
        cli_id, proc_id, qty, precio = row[5], row[6], row[7], row[8]
        obs, estado = row[9], row[10]

        if sid is None:
            continue
        try:
            sid = int(sid)
        except (ValueError, TypeError):
            sid = None

        user_id = int(user_id) if user_id else 1
        prod_id = int(prod_id) if prod_id is not None else 1
        proc_id = int(proc_id) if proc_id is not None else 0
        cli_id = int(cli_id) if cli_id is not None else 0
        qty = int(qty) if qty else 1
        precio = to_dec(precio)
        status = (SaleStatusEnum.completed
                  if str(estado or "").lower() == "completado"
                  else SaleStatusEnum.in_progress)

        # Manejar ID duplicado (e.g. ID=28 aparece dos veces):
        # asignar explicitamente max+1 para no chocar con IDs ya usados
        if sid is not None and sid not in used_ids:
            use_id = sid
        else:
            use_id = (max(used_ids) + 1) if used_ids else 1
        used_ids.add(use_id)

        sale_kwargs = dict(
            customer_id=cli_id if cli_id > 0 else None,
            user_id=user_id,
            sale_date=to_date(fecha),
            status=status,
            observations=str(obs) if obs else None,
            subtotal=precio,
            iva=Decimal("0.00"),
            total=precio,
        )
        if use_id is not None:
            sale_kwargs["id"] = use_id

        sale = Sale(**sale_kwargs)
        db.add(sale)
        db.flush()

        # Buscar el DetailRoastedCoffee correspondiente
        drc_id = drc_map.get((proc_id, prod_id)) or drc_map.get((0, prod_id))
        if drc_id is None:
            print(f"\n  [WARN] Sin DRC para (proc={proc_id}, prod={prod_id}) - venta {sale.id} sin detalle")
            warnings += 1
            continue

        unit_val = (precio / qty).quantize(Decimal("0.01")) if qty > 0 else precio
        db.add(DetailSale(
            sale_id=sale.id,
            detail_roasted_coffee_id=drc_id,
            quantity=qty,
            unit_value=unit_val,
            iva_percentage=Decimal("0.00"),
            subtotal=precio,
            iva=Decimal("0.00"),
            total=precio,
        ))
        count += 1

    db.flush()
    msg = f"OK ({count} ventas)"
    if warnings:
        msg += f"  [{warnings} advertencias sin DRC]"
    print(msg)


# ─── Step 11: Movements -> RoastedMovement + RoastedMovementDetail ────────────

def import_movements(db, wb, drc_map: dict) -> None:
    print("Importando movimientos...", end=" ", flush=True)
    rows = read_sheet_rows(wb, "Movements")
    count = 0

    for row in rows:
        mid, fecha, proc_id = row[0], row[1], row[2]
        if mid is None:
            continue
        mid = int(mid)
        if mid == 0:
            continue  # fila placeholder

        proc_id = int(proc_id) if proc_id is not None else 0
        obs_raw = str(row[12]) if row[12] else ""

        # Recopilar detalles no-cero
        details_data = []
        for col_idx, prod_id in MOV_PROD_COLS.items():
            val = row[col_idx]
            if val is None or val == 0:
                continue
            qty_int = int(val)
            drc_id = drc_map.get((proc_id, prod_id)) or drc_map.get((0, prod_id))
            if drc_id is not None:
                direction = (MovementDirectionEnum.entry if qty_int > 0
                             else MovementDirectionEnum.exit)
                details_data.append((drc_id, abs(qty_int), direction))

        if not details_data:
            continue

        rm = RoastedMovement(
            movement_date=to_dt(fecha),
            observations=f"{obs_raw} [proceso={proc_id}]".strip(),
            created_by=1,
        )
        db.add(rm)
        db.flush()

        for drc_id, qty, direction in details_data:
            db.add(RoastedMovementDetail(
                movement_id=rm.id,
                detail_roasted_coffee_id=drc_id,
                quantity=qty,
                direction=direction,
            ))
        count += 1

    db.flush()
    print(f"OK ({count} movimientos)")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print("  Importacion Excel -> BD Shaya")
    print(f"  Archivo: {EXCEL_PATH.name}")
    print(f"{'='*55}\n")

    if not EXCEL_PATH.exists():
        print(f"ERROR: No se encontró {EXCEL_PATH}")
        sys.exit(1)

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    db = SessionLocal()

    try:
        truncate_all(db)

        parchment_prod_id = import_products(db, wb)
        db.commit()

        import_farmers(db, wb)
        db.commit()

        import_customers(db, wb)
        db.commit()

        import_users(db, wb)
        db.commit()

        parchment_map = import_parchments(db, wb, parchment_prod_id)
        db.commit()

        import_processes(db, wb, parchment_map)
        db.commit()

        import_detail_processes(db, wb)
        db.commit()

        rc_map = import_roasted_coffees(db, parchment_map)
        db.commit()

        drc_map = import_detail_roasted_coffees(db, wb, rc_map)
        db.commit()

        import_sales(db, wb, drc_map)
        db.commit()

        import_movements(db, wb, drc_map)
        db.commit()

        reset_sequences(db)

        print(f"\n{'='*55}")
        print("  OK  Importacion completada correctamente.")
        print(f"{'='*55}\n")

    except Exception:
        db.rollback()
        print(f"\n{'='*55}")
        print("  ERROR  durante la importacion. Rollback aplicado.")
        print(f"{'='*55}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
