"""Add database check constraints

Revision ID: c6fa40bc51b4
Revises: aa7760c1bcb2
Create Date: 2026-09-21 11:21:07.194648

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c6fa40bc51b4"
down_revision: Union[str, Sequence[str], None] = "aa7760c1bcb2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add database check constraints."""

    with op.batch_alter_table("flights", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "check_flight_price_non_negative",
            "price >= 0",
        )
        batch_op.create_check_constraint(
            "check_flight_seats_non_negative",
            "available_seats >= 0",
        )

    with op.batch_alter_table("buses", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "check_bus_price_non_negative",
            "price >= 0",
        )
        batch_op.create_check_constraint(
            "check_bus_seats_non_negative",
            "available_seats >= 0",
        )

    with op.batch_alter_table("ships", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "check_ship_price_non_negative",
            "price >= 0",
        )
        batch_op.create_check_constraint(
            "check_ship_seats_non_negative",
            "available_seats >= 0",
        )

    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "check_booking_status",
            "status IN ('confirmed', 'cancelled')",
        )

    with op.batch_alter_table("payments", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "check_payment_amount_non_negative",
            "amount >= 0",
        )


def downgrade() -> None:
    """Remove database check constraints."""

    with op.batch_alter_table("payments", schema=None) as batch_op:
        batch_op.drop_constraint(
            "check_payment_amount_non_negative",
            type_="check",
        )

    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.drop_constraint(
            "check_booking_status",
            type_="check",
        )

    with op.batch_alter_table("ships", schema=None) as batch_op:
        batch_op.drop_constraint(
            "check_ship_seats_non_negative",
            type_="check",
        )
        batch_op.drop_constraint(
            "check_ship_price_non_negative",
            type_="check",
        )

    with op.batch_alter_table("buses", schema=None) as batch_op:
        batch_op.drop_constraint(
            "check_bus_seats_non_negative",
            type_="check",
        )
        batch_op.drop_constraint(
            "check_bus_price_non_negative",
            type_="check",
        )

    with op.batch_alter_table("flights", schema=None) as batch_op:
        batch_op.drop_constraint(
            "check_flight_seats_non_negative",
            type_="check",
        )
        batch_op.drop_constraint(
            "check_flight_price_non_negative",
            type_="check",
        )
