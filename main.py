from fastapi import FastAPI, Request
import uvicorn
import psycopg2
from contextlib import asynccontextmanager
from core.tools.config import config
from core.orm.environment import Environment
from core.module_loader import ModuleLoader
from core.orm.registry import Registry

# Global DB Pool (Simple)
db_connection = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_connection
    try:
        db_connection = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )
        # Initialize Modules
        with db_connection.cursor() as cr:
            # Create a supervisor env
            env = Environment(cr, 1, {}) 
            loader = ModuleLoader(config.MODULES_PATH)
            loader.load_modules(env)
            db_connection.commit()
            
        yield
    except Exception as e:
        print(f"Startup failed: {e}")
        # In production this should stop the server, but for dev we let it run or raise
        raise e
    finally:
        # Shutdown
        if db_connection:
            db_connection.close()

app = FastAPI(title="Odoo-like Core", lifespan=lifespan)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    # Create a new cursor for each request
    # NOTE: In a real app, use a connection pool (e.g. psycopg2.pool)
    # Here we are reusing the single connection which is NOT thread safe for async FastAPI 
    # if we have multiple workers or concurrent requests.
    # For this MVP simulation, we should really create a new connection or use valid pool.
    # Let's create a new connection per request for safety now, or assume single worker.
    # To keep it simple and correct:
    conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
    )
    request.state.conn = conn
    try:
        response = await call_next(request)
        conn.commit()
        return response
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@app.get("/")
def read_root():
    return {
        "message": "Odoo-like Core Running",
        "version": version,
        "models": list(Registry.models().keys())
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
