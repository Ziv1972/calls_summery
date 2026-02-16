"""Alembic environment configuration."""

import os
import sys
from logging.config import fileConfig

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.config.settings import get_settings
from src.models.database import Base

# Import all models so Alembic can detect them
from src.models.call import Call  # noqa: F401
from src.models.transcription import Transcription  # noqa: F401
from src.models.summary import Summary  # noqa: F401
from src.models.notification import Notification  # noqa: F401
from src.models.settings import UserSettings  # noqa: F401
from src.models.user import User  # noqa: F401
from src.models.api_key import ApiKey  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override URL from settings
settings = get_settings()
sync_url = settings.database_url.replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
