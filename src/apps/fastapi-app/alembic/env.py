import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fipe_hunter.db")
config.set_main_option("sqlalchemy.url", DATABASE_URL)


import sys
_base_dir = os.path.dirname(__file__)


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
        render_as_batch=True,
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
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
