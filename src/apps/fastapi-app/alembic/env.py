import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Load .env if present (local dev)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Alembic config
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from DATABASE_URL env var
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fipe_hunter.db")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Import all models so autogenerate can detect them
import sys
_base_dir = os.path.dirname(__file__)
# Docker layout: /app/alembic/../libs/infra-py = /app/libs/infra-py
# Local layout:  src/apps/fastapi-app/alembic/../../libs/infra-py = src/libs/infra-py  (via PYTHONPATH)
# Try Docker path first, then local path
for _candidate in [
    os.path.join(_base_dir, "..", "libs", "infra-py"),
    os.path.join(_base_dir, "..", "..", "..", "libs", "infra-py"),
]:
    _resolved = os.path.realpath(_candidate)
    if os.path.exists(_resolved) and _resolved not in sys.path:
        sys.path.insert(0, _resolved)
        break
from fipe_infra.database.models import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # required for SQLite ALTER TABLE support
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # required for SQLite ALTER TABLE support
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
