"""
Registro central de modelos ORM.

Importa todos los modelos para registrarlos en `Base.metadata` y en el
registro de clases de SQLAlchemy. Lo usan todos los puntos de entrada — la
app, Alembic, los scripts y las pruebas — para que las relaciones por nombre
(`relationship("ProductExpense")`) y las llaves foráneas entre tablas
resuelvan igual en todos lados: un modelo que falte rompe la configuración de
los mappers o el flush de las tablas que lo referencian.

Todo modelo nuevo se registra aquí.
"""

from app.core.db.base import Base  # noqa: F401

from app.models import (  # noqa: F401
    customer,
    detail_process,
    detail_roasted_coffe,
    detail_sale,
    expense_category,
    fair,
    fair_expense,
    fair_inventory,
    fair_product,
    fair_sale,
    farmer,
    general_expense,
    inventory,
    inventory_movement,
    parchment,
    payment_method,
    person,
    process,
    process_expense,
    product,
    product_expense,
    roasted_coffe,
    roasted_movement,
    sale,
    user,
)
