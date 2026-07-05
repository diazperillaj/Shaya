from logging.config import fileConfig
import os

from sqlalchemy import create_engine, pool
from alembic import context

from dotenv import load_dotenv
load_dotenv()

from app.core.db.base import Base

# Importa modelos para que Alembic los detecte
from app.models.customer import Customer
from app.models.farmer import Farmer
from app.models.inventory_movement import InventoryMovement
from app.models.inventory import Inventory
from app.models.parchment import Parchment
from app.models.person import Person
from app.models.process import Process
from app.models.detail_process import DetailProcess
from app.models.product import Product
from app.models.user import User
from app.models.roasted_coffe import RoastedCoffee
from app.models.detail_roasted_coffe import DetailRoastedCoffee
from app.models.sale import Sale
from app.models.detail_sale import DetailSale
from app.models.fair import Fair
from app.models.fair_inventory import FairInventory
from app.models.fair_sale import FairSale
from app.models.fair_expense import FairExpense
from app.models.roasted_movement import RoastedMovement, RoastedMovementDetail
from app.models.process_expense import ProcessExpense
from app.models.product_expense import ProductExpense
from app.models.payment_method import PaymentMethod
from app.models.expense_category import ExpenseCategory
from app.models.general_expense import GeneralExpense

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# CLAVE: metadata correcto
target_metadata = Base.metadata

# Construir URL desde .env
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def run_migrations_offline():
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()