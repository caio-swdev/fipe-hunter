"""fix_sequences_v2

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-02-23 22:00:00.000000

v1 (a1b2c3d4e5f6) ran setval with is_called=false but the sequence keeps
returning values that already exist. This v2 uses is_called=true (canonical
form) and resets each sequence to MAX(id) so next nextval() returns MAX(id)+1.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SERIAL_TABLES = [
    ('listings', 'listings_id_seq'),
    ('opportunities', 'opportunities_id_seq'),
    ('price_cache', 'price_cache_id_seq'),
    ('search_cache', 'search_cache_id_seq'),
    ('alerts', 'alerts_id_seq'),
    ('rate_limit_events', 'rate_limit_events_id_seq'),
    ('api_hits', 'api_hits_id_seq'),
]


def upgrade() -> None:
    conn = op.get_bind()
    for table, seq in SERIAL_TABLES:
        # is_called=true: sets last_value=MAX(id), next nextval() returns MAX(id)+1
        conn.execute(sa.text(
            f"SELECT setval('{seq}', GREATEST((SELECT COALESCE(MAX(id), 1) FROM {table}), 1))"
        ))


def downgrade() -> None:
    pass
