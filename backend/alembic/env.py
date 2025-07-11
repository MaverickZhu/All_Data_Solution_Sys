import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path to allow running alembic from the 'backend' directory
# This makes both local execution and docker execution work
if 'APP_ENV' in os.environ and os.environ['APP_ENV'] == 'docker':
    # In Docker, the project root is /app
    project_root = Path('/app')
    sys.path.insert(0, str(project_root))
else:
    # For local execution, calculate the path
    # (backend/alembic/env.py -> backend/alembic -> backend -> project_root)
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

# Load .env file with UTF-8 encoding
# This is crucial for environments where the .env file might be saved with a different default encoding (e.g., on Windows)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path, encoding='utf-8')

from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name:
    fileConfig(config.config_file_name)

# Add the 'backend' directory to sys.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Overwrite sqlalchemy.url from environment variables
# This ensures that we use the database configuration from the .env file
sync_db_url = os.getenv("SYNC_DATABASE_URL", "postgresql+pg8000://postgres:password@localhost:5433/multimodal_analysis?client_encoding=utf8")
if sync_db_url:
    config.set_main_option("sqlalchemy.url", sync_db_url)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from backend.core.database import Base
from backend.models.user import User
from backend.models.project import Project
from backend.models.data_source import DataSource
from backend.models.task import Task
from backend.core.config import settings

target_metadata = Base.metadata

def get_db_url():
    """
    从环境变量构造数据库连接URL，这是在容器化环境中的最佳实践。
    """
    postgres_user = os.getenv("POSTGRES_USER", "postgres")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "password")
    postgres_host = os.getenv("POSTGRES_HOST", "localhost") # 在Docker网络中，服务名就是主机名
    postgres_port = os.getenv("POSTGRES_PORT", "5433")
    postgres_db = os.getenv("POSTGRES_DB", "multimodal_analysis")
    
    # 使用pg8000以避免在Windows上出现psycopg2编码问题
    return f"postgresql+pg8000://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # url = config.get_main_option("sqlalchemy.url")
    url = get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # 使用从环境变量生成的URL创建引擎
    database_url = get_db_url()
    connectable = create_engine(database_url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
