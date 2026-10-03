"""link parchments to dryings

Quinta migración del módulo de cultivo (bloque 4) y la única que toca una
tabla del núcleo: `parchments` gana `drying_id`, el eslabón entre el
inventario y el secado que produjo el pergamino (decisión C2).

- NULL = café comprado; los registros existentes quedan así, sin cambios.
- Único: un secado produce a lo sumo un registro de pergamino (el índice
  del único sirve también para las consultas por secado).
- `origin_batch` no se toca: sigue siendo el texto libre del café comprado
  y de los datos históricos (R4).

Ver app/farm_operations/docs/modelo-datos.md §4 y plan-migraciones.md (M5).

Revision ID: dd940c212d49
Revises: 9a5de8974e57
Create Date: 2026-10-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd940c212d49'
down_revision: Union[str, Sequence[str], None] = '9a5de8974e57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('parchments', sa.Column('drying_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_parchments_drying', 'parchments', 'dryings',
        ['drying_id'], ['id'], ondelete='RESTRICT',
    )
    op.create_unique_constraint('uq_parchments_drying', 'parchments', ['drying_id'])


def downgrade() -> None:
    op.drop_constraint('uq_parchments_drying', 'parchments', type_='unique')
    op.drop_constraint('fk_parchments_drying', 'parchments', type_='foreignkey')
    op.drop_column('parchments', 'drying_id')
