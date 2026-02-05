from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import Base
from app.settings import get_database_url

# Alembic Config object
config = context.config
config.set_main_option("sqlalchemy.url", get_database_url())

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# target metadata for 'autogenerate'
target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata
            )

            with context.begin_transaction():
                context.run_migrations()

    except Exception as e:
        import psycopg2

        # Check if the exception is a connection error
        if isinstance(e.__cause__, psycopg2.OperationalError):
            print("\n" + "#"*80)
            print("\033[1;41m" + " " * 10 + " DATABASE ISN'T RUNNING! " + " " * 10 + "\033[0m")
            print("#"*80 + "\n")
            print("Full error:")
            print(e)
            sys.exit(1)
        else:
            # Re-raise other errors (like migration mismatch)
            raise

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
