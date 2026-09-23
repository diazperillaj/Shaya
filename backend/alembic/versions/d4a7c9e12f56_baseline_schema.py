"""baseline: consolidated schema

Consolida las 26 migraciones históricas en una sola revisión que crea el
esquema completo tal como está en producción (volcado
`pg_dump --schema-only --schema=public` del 2026-09-22, PostgreSQL 16.14).

Por qué: la cadena anterior no podía construir la base desde cero. Su
migración raíz (8b54c737047e) modificaba `persons`, una tabla que ninguna
migración creaba, así que ni las pruebas ni un entorno nuevo podían levantar
la base con `alembic upgrade head`.

Conserva el ID del head anterior (d4a7c9e12f56) con down_revision = None:
una base existente ya está en esta revisión y no ejecuta nada; una base
vacía se construye completa. Las migraciones originales quedan como
historia en alembic/versions_archive/.

Ver app/farm_operations/docs/implementation/plan-implementacion.md §2.3.

Revision ID: d4a7c9e12f56
Revises:
Create Date: 2026-09-22

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd4a7c9e12f56'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # DDL del volcado, ejecutado tal cual por el driver.
    op.get_bind().exec_driver_sql(SCHEMA_SQL)


def downgrade() -> None:
    raise RuntimeError(
        'La migración base no tiene downgrade: deshacerla borraría todas '
        'las tablas del negocio.'
    )


SCHEMA_SQL = """
CREATE TYPE public.expensecategoryenum AS ENUM (
    'food',
    'supplies',
    'transport',
    'other'
);

CREATE TYPE public.fairstatusenum AS ENUM (
    'open',
    'closed'
);

CREATE TYPE public.movementdirectionenum AS ENUM (
    'entry',
    'exit'
);

CREATE TYPE public.movementtypeenum AS ENUM (
    'parchment_entrance',
    'parchment_exit',
    'processed_entrance',
    'processed_exit',
    'adjustment',
    'spoilage',
    'devolution',
    'fair_entrance',
    'fair_return'
);

CREATE TYPE public.paymenttypeenum AS ENUM (
    'cash',
    'transfer',
    'credit'
);

CREATE TYPE public.processexpensecategoryenum AS ENUM (
    'transport',
    'labor',
    'supplies',
    'other'
);

CREATE TYPE public.productexpensecategoryenum AS ENUM (
    'packaging',
    'label',
    'supplies',
    'other'
);

CREATE TYPE public.productmovementtypeenum AS ENUM (
    'parchment',
    'processed'
);

CREATE TYPE public.producttypeenum AS ENUM (
    'parchment',
    'processed',
    'other'
);

CREATE TYPE public.saleproducttypeenum AS ENUM (
    'parchment',
    'processed'
);

CREATE TYPE public.salestatusenum AS ENUM (
    'completed',
    'in_progress'
);

CREATE TABLE public.customers (
    id integer NOT NULL,
    "customerType" character varying(255) NOT NULL,
    address character varying(255),
    city character varying(255) NOT NULL,
    person_id integer NOT NULL
);

CREATE SEQUENCE public.customers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.customers_id_seq OWNED BY public.customers.id;

CREATE TABLE public.detail_processes (
    id integer NOT NULL,
    process_id integer NOT NULL,
    date date NOT NULL,
    product_id integer NOT NULL,
    bag_quantity integer NOT NULL,
    grams_per_bag integer NOT NULL,
    unit_value numeric(12,2) NOT NULL,
    iva numeric(12,2) NOT NULL,
    total numeric(12,2) NOT NULL,
    observations text
);

CREATE SEQUENCE public.detail_processes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.detail_processes_id_seq OWNED BY public.detail_processes.id;

CREATE TABLE public.detail_roasted_coffees (
    id integer NOT NULL,
    roasted_coffee_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity integer NOT NULL,
    remaining_quantity integer NOT NULL,
    unit_cost numeric(12,2)
);

CREATE SEQUENCE public.detail_roasted_coffees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.detail_roasted_coffees_id_seq OWNED BY public.detail_roasted_coffees.id;

CREATE TABLE public.detail_sales (
    id integer NOT NULL,
    sale_id integer NOT NULL,
    detail_roasted_coffee_id integer NOT NULL,
    quantity integer NOT NULL,
    unit_value numeric(12,2) NOT NULL,
    iva_percentage numeric(5,2) NOT NULL,
    subtotal numeric(12,2) NOT NULL,
    iva numeric(12,2) NOT NULL,
    total numeric(12,2) NOT NULL
);

CREATE SEQUENCE public.detail_sales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.detail_sales_id_seq OWNED BY public.detail_sales.id;

CREATE TABLE public.expense_categories (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);

CREATE SEQUENCE public.expense_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.expense_categories_id_seq OWNED BY public.expense_categories.id;

CREATE TABLE public.fair_expenses (
    id integer NOT NULL,
    fair_id integer NOT NULL,
    user_id integer NOT NULL,
    category public.expensecategoryenum NOT NULL,
    description character varying(300) NOT NULL,
    amount numeric(12,2) NOT NULL,
    expense_datetime timestamp with time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE public.fair_expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.fair_expenses_id_seq OWNED BY public.fair_expenses.id;

CREATE TABLE public.fair_inventories (
    id integer NOT NULL,
    fair_id integer NOT NULL,
    detail_roasted_coffee_id integer NOT NULL,
    initial_quantity integer NOT NULL,
    remaining_quantity integer NOT NULL,
    unit_value numeric(12,2) NOT NULL
);

CREATE SEQUENCE public.fair_inventories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.fair_inventories_id_seq OWNED BY public.fair_inventories.id;

CREATE TABLE public.fair_products (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    default_price numeric(12,2) NOT NULL
);

CREATE SEQUENCE public.fair_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.fair_products_id_seq OWNED BY public.fair_products.id;

CREATE TABLE public.fair_sales (
    id integer NOT NULL,
    fair_id integer NOT NULL,
    fair_inventory_id integer,
    sale_datetime timestamp with time zone DEFAULT now() NOT NULL,
    quantity integer NOT NULL,
    unit_value numeric(12,2) NOT NULL,
    total numeric(12,2) NOT NULL,
    observations text,
    payment_method_id integer NOT NULL,
    fair_product_id integer,
    CONSTRAINT ck_fair_sale_item_source CHECK (((fair_inventory_id IS NULL) <> (fair_product_id IS NULL)))
);

CREATE SEQUENCE public.fair_sales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.fair_sales_id_seq OWNED BY public.fair_sales.id;

CREATE TABLE public.fairs (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    location character varying(200),
    start_datetime timestamp with time zone NOT NULL,
    end_datetime timestamp with time zone,
    status public.fairstatusenum NOT NULL,
    user_id integer NOT NULL,
    sale_id integer,
    observations text
);

CREATE SEQUENCE public.fairs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.fairs_id_seq OWNED BY public.fairs.id;

CREATE TABLE public.farmers (
    id integer NOT NULL,
    farm_name character varying(255) NOT NULL,
    person_id integer NOT NULL,
    village character varying(255) NOT NULL,
    municipality character varying(255) NOT NULL
);

CREATE SEQUENCE public.farmers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.farmers_id_seq OWNED BY public.farmers.id;

CREATE TABLE public.general_expenses (
    id integer NOT NULL,
    expense_date date NOT NULL,
    amount numeric(12,2) NOT NULL,
    category_id integer NOT NULL,
    payment_method_id integer,
    description text NOT NULL,
    created_by integer
);

CREATE SEQUENCE public.general_expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.general_expenses_id_seq OWNED BY public.general_expenses.id;

CREATE TABLE public.inventories (
    id integer NOT NULL,
    product_id integer NOT NULL,
    date timestamp with time zone NOT NULL,
    quantity numeric(10,3) NOT NULL,
    observations text
);

CREATE SEQUENCE public.inventories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.inventories_id_seq OWNED BY public.inventories.id;

CREATE TABLE public.inventory_movements (
    id integer NOT NULL,
    movement_date timestamp with time zone DEFAULT now() NOT NULL,
    movement_type public.movementtypeenum NOT NULL,
    product_type public.productmovementtypeenum NOT NULL,
    parchment_id integer,
    quantity numeric(10,3) NOT NULL,
    reason character varying(255),
    responsible character varying(255),
    observations text,
    process_id integer,
    sale_id integer,
    fair_id integer
);

CREATE SEQUENCE public.inventory_movements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.inventory_movements_id_seq OWNED BY public.inventory_movements.id;

CREATE TABLE public.parchments (
    id integer NOT NULL,
    inventory_id integer NOT NULL,
    farmer_id integer NOT NULL,
    variety character varying(100),
    altitude numeric(6,2),
    humidity numeric(5,2),
    purchase_price numeric(12,2) NOT NULL,
    initial_quantity numeric(10,3) NOT NULL,
    remaining_quantity numeric(10,3) NOT NULL,
    purchase_date date NOT NULL,
    origin_batch character varying(100),
    full_price numeric(12,2) NOT NULL
);

CREATE SEQUENCE public.parchments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.parchments_id_seq OWNED BY public.parchments.id;

CREATE TABLE public.payment_methods (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);

CREATE SEQUENCE public.payment_methods_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.payment_methods_id_seq OWNED BY public.payment_methods.id;

CREATE TABLE public.persons (
    id integer NOT NULL,
    full_name character varying(255) NOT NULL,
    document character varying(255),
    phone character varying(20),
    email character varying(255),
    observation text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE public.persons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.persons_id_seq OWNED BY public.persons.id;

CREATE TABLE public.process_expenses (
    id integer NOT NULL,
    process_id integer NOT NULL,
    category public.processexpensecategoryenum NOT NULL,
    amount numeric(12,2) NOT NULL,
    expense_date date NOT NULL,
    observations text,
    created_by integer
);

CREATE SEQUENCE public.process_expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.process_expenses_id_seq OWNED BY public.process_expenses.id;

CREATE TABLE public.processes (
    id integer NOT NULL,
    invoice_number character varying(100) NOT NULL,
    process_date date NOT NULL,
    parchment_id integer NOT NULL,
    parchment_kg numeric(10,3) NOT NULL,
    resultant_kg numeric(10,3) NOT NULL,
    yield_percentage numeric(7,3) NOT NULL,
    subtotal numeric(12,2) NOT NULL,
    iva numeric(12,2) NOT NULL,
    total numeric(12,2) NOT NULL,
    observations text
);

CREATE SEQUENCE public.processes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.processes_id_seq OWNED BY public.processes.id;

CREATE TABLE public.product_expenses (
    id integer NOT NULL,
    product_id integer NOT NULL,
    category public.productexpensecategoryenum NOT NULL,
    amount numeric(12,2) NOT NULL,
    observations text
);

CREATE SEQUENCE public.product_expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.product_expenses_id_seq OWNED BY public.product_expenses.id;

CREATE TABLE public.products (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    type public.producttypeenum NOT NULL,
    description text,
    active boolean NOT NULL,
    quantity integer NOT NULL,
    generates_inventory boolean NOT NULL
);

CREATE SEQUENCE public.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;

CREATE TABLE public.roasted_coffees (
    id integer NOT NULL,
    process_id integer NOT NULL,
    observations text
);

CREATE SEQUENCE public.roasted_coffees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.roasted_coffees_id_seq OWNED BY public.roasted_coffees.id;

CREATE TABLE public.roasted_movement_details (
    id integer NOT NULL,
    movement_id integer NOT NULL,
    detail_roasted_coffee_id integer NOT NULL,
    quantity integer NOT NULL,
    direction public.movementdirectionenum DEFAULT 'exit'::public.movementdirectionenum NOT NULL,
    created_lot boolean DEFAULT false NOT NULL
);

CREATE SEQUENCE public.roasted_movement_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.roasted_movement_details_id_seq OWNED BY public.roasted_movement_details.id;

CREATE TABLE public.roasted_movements (
    id integer NOT NULL,
    movement_date timestamp with time zone NOT NULL,
    observations text,
    created_by integer
);

CREATE SEQUENCE public.roasted_movements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.roasted_movements_id_seq OWNED BY public.roasted_movements.id;

CREATE TABLE public.sales (
    id integer NOT NULL,
    customer_id integer,
    user_id integer NOT NULL,
    sale_date date NOT NULL,
    observations text,
    subtotal numeric(12,2) NOT NULL,
    iva numeric(12,2) NOT NULL,
    total numeric(12,2) NOT NULL,
    status public.salestatusenum DEFAULT 'in_progress'::public.salestatusenum NOT NULL,
    payment_method_id integer
);

CREATE SEQUENCE public.sales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.sales_id_seq OWNED BY public.sales.id;

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    role character varying(255),
    person_id integer NOT NULL
);

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;

ALTER TABLE ONLY public.customers ALTER COLUMN id SET DEFAULT nextval('public.customers_id_seq'::regclass);

ALTER TABLE ONLY public.detail_processes ALTER COLUMN id SET DEFAULT nextval('public.detail_processes_id_seq'::regclass);

ALTER TABLE ONLY public.detail_roasted_coffees ALTER COLUMN id SET DEFAULT nextval('public.detail_roasted_coffees_id_seq'::regclass);

ALTER TABLE ONLY public.detail_sales ALTER COLUMN id SET DEFAULT nextval('public.detail_sales_id_seq'::regclass);

ALTER TABLE ONLY public.expense_categories ALTER COLUMN id SET DEFAULT nextval('public.expense_categories_id_seq'::regclass);

ALTER TABLE ONLY public.fair_expenses ALTER COLUMN id SET DEFAULT nextval('public.fair_expenses_id_seq'::regclass);

ALTER TABLE ONLY public.fair_inventories ALTER COLUMN id SET DEFAULT nextval('public.fair_inventories_id_seq'::regclass);

ALTER TABLE ONLY public.fair_products ALTER COLUMN id SET DEFAULT nextval('public.fair_products_id_seq'::regclass);

ALTER TABLE ONLY public.fair_sales ALTER COLUMN id SET DEFAULT nextval('public.fair_sales_id_seq'::regclass);

ALTER TABLE ONLY public.fairs ALTER COLUMN id SET DEFAULT nextval('public.fairs_id_seq'::regclass);

ALTER TABLE ONLY public.farmers ALTER COLUMN id SET DEFAULT nextval('public.farmers_id_seq'::regclass);

ALTER TABLE ONLY public.general_expenses ALTER COLUMN id SET DEFAULT nextval('public.general_expenses_id_seq'::regclass);

ALTER TABLE ONLY public.inventories ALTER COLUMN id SET DEFAULT nextval('public.inventories_id_seq'::regclass);

ALTER TABLE ONLY public.inventory_movements ALTER COLUMN id SET DEFAULT nextval('public.inventory_movements_id_seq'::regclass);

ALTER TABLE ONLY public.parchments ALTER COLUMN id SET DEFAULT nextval('public.parchments_id_seq'::regclass);

ALTER TABLE ONLY public.payment_methods ALTER COLUMN id SET DEFAULT nextval('public.payment_methods_id_seq'::regclass);

ALTER TABLE ONLY public.persons ALTER COLUMN id SET DEFAULT nextval('public.persons_id_seq'::regclass);

ALTER TABLE ONLY public.process_expenses ALTER COLUMN id SET DEFAULT nextval('public.process_expenses_id_seq'::regclass);

ALTER TABLE ONLY public.processes ALTER COLUMN id SET DEFAULT nextval('public.processes_id_seq'::regclass);

ALTER TABLE ONLY public.product_expenses ALTER COLUMN id SET DEFAULT nextval('public.product_expenses_id_seq'::regclass);

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);

ALTER TABLE ONLY public.roasted_coffees ALTER COLUMN id SET DEFAULT nextval('public.roasted_coffees_id_seq'::regclass);

ALTER TABLE ONLY public.roasted_movement_details ALTER COLUMN id SET DEFAULT nextval('public.roasted_movement_details_id_seq'::regclass);

ALTER TABLE ONLY public.roasted_movements ALTER COLUMN id SET DEFAULT nextval('public.roasted_movements_id_seq'::regclass);

ALTER TABLE ONLY public.sales ALTER COLUMN id SET DEFAULT nextval('public.sales_id_seq'::regclass);

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_person_id_key UNIQUE (person_id);

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.detail_processes
    ADD CONSTRAINT detail_processes_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.detail_roasted_coffees
    ADD CONSTRAINT detail_roasted_coffees_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.detail_sales
    ADD CONSTRAINT detail_sales_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.expense_categories
    ADD CONSTRAINT expense_categories_name_key UNIQUE (name);

ALTER TABLE ONLY public.expense_categories
    ADD CONSTRAINT expense_categories_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.fair_expenses
    ADD CONSTRAINT fair_expenses_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.fair_inventories
    ADD CONSTRAINT fair_inventories_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.fair_products
    ADD CONSTRAINT fair_products_name_key UNIQUE (name);

ALTER TABLE ONLY public.fair_products
    ADD CONSTRAINT fair_products_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.fair_sales
    ADD CONSTRAINT fair_sales_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.fairs
    ADD CONSTRAINT fairs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.farmers
    ADD CONSTRAINT farmers_person_id_key UNIQUE (person_id);

ALTER TABLE ONLY public.farmers
    ADD CONSTRAINT farmers_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.general_expenses
    ADD CONSTRAINT general_expenses_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.inventories
    ADD CONSTRAINT inventories_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.inventory_movements
    ADD CONSTRAINT inventory_movements_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.parchments
    ADD CONSTRAINT parchments_inventory_id_key UNIQUE (inventory_id);

ALTER TABLE ONLY public.parchments
    ADD CONSTRAINT parchments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.payment_methods
    ADD CONSTRAINT payment_methods_name_key UNIQUE (name);

ALTER TABLE ONLY public.payment_methods
    ADD CONSTRAINT payment_methods_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.persons
    ADD CONSTRAINT persons_document_key UNIQUE (document);

ALTER TABLE ONLY public.persons
    ADD CONSTRAINT persons_email_key UNIQUE (email);

ALTER TABLE ONLY public.persons
    ADD CONSTRAINT persons_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.process_expenses
    ADD CONSTRAINT process_expenses_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.processes
    ADD CONSTRAINT processes_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.product_expenses
    ADD CONSTRAINT product_expenses_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.roasted_coffees
    ADD CONSTRAINT roasted_coffees_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.roasted_movement_details
    ADD CONSTRAINT roasted_movement_details_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.roasted_movements
    ADD CONSTRAINT roasted_movements_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.sales
    ADD CONSTRAINT sales_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_person_id_key UNIQUE (person_id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);

CREATE INDEX idx_detail_sale_drc_id ON public.detail_sales USING btree (detail_roasted_coffee_id);

CREATE INDEX idx_detail_sale_sale_id ON public.detail_sales USING btree (sale_id);

CREATE INDEX idx_fair_exp_fair_id ON public.fair_expenses USING btree (fair_id);

CREATE INDEX idx_fair_inv_drc_id ON public.fair_inventories USING btree (detail_roasted_coffee_id);

CREATE INDEX idx_fair_inv_fair_id ON public.fair_inventories USING btree (fair_id);

CREATE INDEX idx_fair_sale_datetime ON public.fair_sales USING btree (sale_datetime);

CREATE INDEX idx_fair_sale_fair_id ON public.fair_sales USING btree (fair_id);

CREATE INDEX idx_fair_sale_inv_id ON public.fair_sales USING btree (fair_inventory_id);

CREATE INDEX idx_fair_sale_product_id ON public.fair_sales USING btree (fair_product_id);

CREATE INDEX idx_fair_start ON public.fairs USING btree (start_datetime);

CREATE INDEX idx_fair_status ON public.fairs USING btree (status);

CREATE INDEX idx_fair_user_id ON public.fairs USING btree (user_id);

CREATE INDEX idx_farmer ON public.parchments USING btree (farmer_id);

CREATE INDEX idx_general_expense_category_id ON public.general_expenses USING btree (category_id);

CREATE INDEX idx_general_expense_date ON public.general_expenses USING btree (expense_date);

CREATE INDEX idx_movement_date ON public.inventory_movements USING btree (movement_date);

CREATE INDEX idx_movement_type ON public.inventory_movements USING btree (movement_type);

CREATE INDEX idx_process_expense_process_id ON public.process_expenses USING btree (process_id);

CREATE INDEX idx_process_id ON public.roasted_coffees USING btree (process_id);

CREATE INDEX idx_process_invoice_number ON public.processes USING btree (invoice_number);

CREATE INDEX idx_process_parchment_id ON public.processes USING btree (parchment_id);

CREATE INDEX idx_process_process_date ON public.processes USING btree (process_date);

CREATE INDEX idx_product_expense_product_id ON public.product_expenses USING btree (product_id);

CREATE INDEX idx_product_id ON public.detail_roasted_coffees USING btree (product_id);

CREATE INDEX idx_purchase_date ON public.parchments USING btree (purchase_date);

CREATE INDEX idx_roasted_coffee_id ON public.detail_roasted_coffees USING btree (roasted_coffee_id);

CREATE INDEX idx_sale_customer_id ON public.sales USING btree (customer_id);

CREATE INDEX idx_sale_date ON public.sales USING btree (sale_date);

CREATE INDEX idx_sale_status ON public.sales USING btree (status);

CREATE INDEX idx_sale_user_id ON public.sales USING btree (user_id);

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.persons(id);

ALTER TABLE ONLY public.detail_processes
    ADD CONSTRAINT detail_processes_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.processes(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.detail_processes
    ADD CONSTRAINT detail_processes_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.detail_roasted_coffees
    ADD CONSTRAINT detail_roasted_coffees_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.detail_roasted_coffees
    ADD CONSTRAINT detail_roasted_coffees_roasted_coffee_id_fkey FOREIGN KEY (roasted_coffee_id) REFERENCES public.roasted_coffees(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.detail_sales
    ADD CONSTRAINT detail_sales_detail_roasted_coffee_id_fkey FOREIGN KEY (detail_roasted_coffee_id) REFERENCES public.detail_roasted_coffees(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.detail_sales
    ADD CONSTRAINT detail_sales_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES public.sales(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.fair_expenses
    ADD CONSTRAINT fair_expenses_fair_id_fkey FOREIGN KEY (fair_id) REFERENCES public.fairs(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.fair_expenses
    ADD CONSTRAINT fair_expenses_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.fair_inventories
    ADD CONSTRAINT fair_inventories_detail_roasted_coffee_id_fkey FOREIGN KEY (detail_roasted_coffee_id) REFERENCES public.detail_roasted_coffees(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.fair_inventories
    ADD CONSTRAINT fair_inventories_fair_id_fkey FOREIGN KEY (fair_id) REFERENCES public.fairs(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.fair_sales
    ADD CONSTRAINT fair_sales_fair_id_fkey FOREIGN KEY (fair_id) REFERENCES public.fairs(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.fair_sales
    ADD CONSTRAINT fair_sales_fair_inventory_id_fkey FOREIGN KEY (fair_inventory_id) REFERENCES public.fair_inventories(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.fairs
    ADD CONSTRAINT fairs_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES public.sales(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.fairs
    ADD CONSTRAINT fairs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.farmers
    ADD CONSTRAINT farmers_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.persons(id);

ALTER TABLE ONLY public.fair_sales
    ADD CONSTRAINT fk_fair_sales_fair_product_id FOREIGN KEY (fair_product_id) REFERENCES public.fair_products(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.fair_sales
    ADD CONSTRAINT fk_fair_sales_payment_method_id FOREIGN KEY (payment_method_id) REFERENCES public.payment_methods(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.sales
    ADD CONSTRAINT fk_sales_payment_method_id FOREIGN KEY (payment_method_id) REFERENCES public.payment_methods(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.general_expenses
    ADD CONSTRAINT general_expenses_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.expense_categories(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.general_expenses
    ADD CONSTRAINT general_expenses_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.general_expenses
    ADD CONSTRAINT general_expenses_payment_method_id_fkey FOREIGN KEY (payment_method_id) REFERENCES public.payment_methods(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.inventories
    ADD CONSTRAINT inventories_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.inventory_movements
    ADD CONSTRAINT inventory_movements_fair_id_fkey FOREIGN KEY (fair_id) REFERENCES public.fairs(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.inventory_movements
    ADD CONSTRAINT inventory_movements_parchment_id_fkey FOREIGN KEY (parchment_id) REFERENCES public.parchments(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.inventory_movements
    ADD CONSTRAINT inventory_movements_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.processes(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.inventory_movements
    ADD CONSTRAINT inventory_movements_sale_id_fkey FOREIGN KEY (sale_id) REFERENCES public.sales(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.parchments
    ADD CONSTRAINT parchments_farmer_id_fkey FOREIGN KEY (farmer_id) REFERENCES public.farmers(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.parchments
    ADD CONSTRAINT parchments_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventories(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.process_expenses
    ADD CONSTRAINT process_expenses_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.process_expenses
    ADD CONSTRAINT process_expenses_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.processes(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.processes
    ADD CONSTRAINT processes_parchment_id_fkey FOREIGN KEY (parchment_id) REFERENCES public.parchments(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.product_expenses
    ADD CONSTRAINT product_expenses_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.roasted_coffees
    ADD CONSTRAINT roasted_coffees_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.processes(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.roasted_movement_details
    ADD CONSTRAINT roasted_movement_details_detail_roasted_coffee_id_fkey FOREIGN KEY (detail_roasted_coffee_id) REFERENCES public.detail_roasted_coffees(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.roasted_movement_details
    ADD CONSTRAINT roasted_movement_details_movement_id_fkey FOREIGN KEY (movement_id) REFERENCES public.roasted_movements(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.roasted_movements
    ADD CONSTRAINT roasted_movements_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.sales
    ADD CONSTRAINT sales_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.sales
    ADD CONSTRAINT sales_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE RESTRICT;

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.persons(id);

"""
