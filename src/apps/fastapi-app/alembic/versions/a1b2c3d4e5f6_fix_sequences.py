"""fix_sequences

Revision ID: a1b2c3d4e5f6
Revises: 5064ad40c48c
Create Date: 2026-02-23 21:00:00.000000

Resets SERIAL sequences for all tables to MAX(id)+1.
Required because the sequence for api_hits (and potentially others) got
out of sync with the actual data, causing duplicate key violations on insert.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '5064ad40c48c'
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
        conn.execute(sa.text(
            f"SELECT setval('{seq}', (SELECT COALESCE(MAX(id), 0) FROM {table}) + 1, false)"
        ))


def downgrade() -> None:
    pass
