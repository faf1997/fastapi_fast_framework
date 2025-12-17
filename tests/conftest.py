import pytest
import psycopg2
from core.tools.config import config
from core.orm.environment import Environment
from core.module_loader import ModuleLoader
from core.orm.registry import Registry

@pytest.fixture(scope="session")
def db_conn():
    conn = psycopg2.connect(
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT
    )
    yield conn
    conn.close()

@pytest.fixture(scope="session")
def env(db_conn):
    # Load modules first
    with db_conn.cursor() as cr:
        e = Environment(cr, 1, {})
        loader = ModuleLoader(config.MODULES_PATH)
        loader.load_modules(e)
        db_conn.commit()
        return e

@pytest.fixture
def test_cursor(db_conn):
    conn = db_conn
    # Start a transaction
    # Note: In real tests we might want rollback after each test.
    # For now we will just commit to keep it simple, or careful cleanup.
    # Psycopg2 default is in transaction.
    return conn.cursor()

@pytest.fixture
def env_test(test_cursor):
    return Environment(test_cursor, 1, {})
