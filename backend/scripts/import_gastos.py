#!/usr/bin/env python3
"""
Importación SELECTIVA de la pestaña "Gastos" del Excel a general_expenses.

A diferencia de import_excel.py, este script NO trunca ni toca el resto de
la base de datos: solo agrega los gastos históricos, reutilizando o creando
las categorías necesarias. Pensado para correr una sola vez sobre una BD ya
en uso.

Ejecutar desde el directorio backend/:  python scripts/import_gastos.py
"""
import sys
from datetime import date, datetime, time as time_type
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import openpyxl

# Importa la app completa para que todos los modelos queden registrados
# y SQLAlchemy pueda resolver las relaciones entre ellos.
import app.main  # noqa: F401

from app.core.db.session import SessionLocal
from app.models.expense_category import ExpenseCategory
from app.models.general_expense import GeneralExpense

EXCEL_PATH = Path(__file__).parent.parent / "data" / "Inventario.xlsx"
IMPORT_DATE = date(2026, 1, 1)


def to_date(v) -> date:
    if v is None or isinstance(v, time_type):
        return IMPORT_DATE
    if isinstance(v, datetime):
        return IMPORT_DATE if v.year <= 1900 else v.date()
    if isinstance(v, date):
        return IMPORT_DATE if v.year <= 1900 else v
    return IMPORT_DATE


def to_dec(v, default: Decimal = Decimal("0.00")) -> Decimal:
    if v is None:
        return default
    try:
        s = str(v).strip()
        return Decimal(s) if s else default
    except InvalidOperation:
        return default


def read_gastos_rows(wb) -> list:
    ws = wb["Gastos"]
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


def main():
    print(f"\n{'='*55}")
    print("  Importacion selectiva: Gastos -> general_expenses")
    print(f"{'='*55}\n")

    if not EXCEL_PATH.exists():
        print(f"ERROR: No se encontró {EXCEL_PATH}")
        sys.exit(1)

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    db = SessionLocal()

    try:
        existing = db.query(GeneralExpense).count()
        if existing > 0:
            print(f"ABORTADO: general_expenses ya tiene {existing} registros.")
            print("Este script solo debe correrse sobre una tabla vacía.")
            sys.exit(1)

        # Cache de categorías existentes (case-insensitive)
        categories = {
            c.name.strip().lower(): c.id
            for c in db.query(ExpenseCategory).all()
        }
        created_cats = 0

        def get_or_create_category(name: str) -> int:
            key = name.strip().lower()
            if key in categories:
                return categories[key]
            nonlocal created_cats
            cat = ExpenseCategory(name=name.strip())
            db.add(cat)
            db.flush()
            categories[key] = cat.id
            created_cats += 1
            return cat.id

        rows = read_gastos_rows(wb)
        count = 0
        for row in rows:
            gid, fecha, cantidad, categoria, motivo = (
                row[0], row[1], row[2], row[3], row[4]
            )
            if gid is None:
                continue

            cat_name = str(categoria).strip() if categoria else "Otro"
            category_id = get_or_create_category(cat_name)

            db.add(GeneralExpense(
                expense_date=to_date(fecha),
                amount=to_dec(cantidad),
                category_id=category_id,
                payment_method_id=None,  # el Excel no registra con qué se pagó
                description=str(motivo).strip() if motivo else "Sin descripción",
                created_by=1,
            ))
            count += 1

        db.commit()
        print(f"OK: {count} gastos importados, {created_cats} categorías nuevas.")
        print(f"Categorías totales: {len(categories)}")
    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}")
        raise
    finally:
        db.close()

    print(f"\n{'='*55}\n")


if __name__ == "__main__":
    main()
