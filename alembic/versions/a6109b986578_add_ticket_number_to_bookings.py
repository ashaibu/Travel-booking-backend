"""add ticket number to bookings

Revision ID: a6109b986578
Revises: 92a212087002
Create Date: 2026-09-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6109b986578'
down_revision: Union[str, Sequence[str], None] = '92a212087002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'bookings',
        sa.Column(
            'ticket_number',
            sa.String(),
            nullable=False,
            server_default='TEMP-TICKET'
        )
    )

    op.execute("UPDATE bookings SET ticket_number = 'TKT-' || id")

    op.create_index(
        op.f('ix_bookings_ticket_number'),
        'bookings',
        ['ticket_number'],
        unique=True
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_bookings_ticket_number'),
        table_name='bookings'
    )
    op.drop_column('bookings', 'ticket_number')
