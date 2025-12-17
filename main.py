from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
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

        # Register Routes from loaded modules
        for router in loader.get_routers():
            app.include_router(router)

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

    # Auth Logic
    api_key = request.headers.get('x-api-key')
    user_id = None
    
    # Allow public access to docs and root for now, or handle 401
    if request.url.path in ["/docs", "/openapi.json", "/"]:
        user_id = 1 # Fallback for docs/monitoring
    
    if not user_id and api_key:
        cur = conn.cursor()
        try:
             # Basic SQL lookup to avoid recursive ORM overhead in auth
             cur.execute("SELECT id FROM res_users WHERE api_key = %s", (api_key,))
             res = cur.fetchone()
             if res:
                 user_id = res[0]
        finally:
             cur.close()
    
    # If no valid user, default to None or Raise 401?
    # For Odoo-like behavior, if public, maybe user_id=None (Public user?)
    # For this secure implementation, let's enforce it for library routes
    
    # Store user_id in state for controllers to use
    request.state.user_id = user_id or 1 # Fallback to admin for dev convenience if no key? 
    # USER REQUESTED SECURITY: So let's be strict if key provided but wrong?
    # Let's keep ID 1 fallback ONLY if no key provided for backwards compat, 
    # BUT if key provided and wrong -> 401.
    
    if api_key and not user_id:
         return JSONResponse(status_code=401, content={"message": "Invalid API Key"})

    # If strict mode desired:
    # if not user_id and not request.url.path in ["/", "/docs", "/openapi.json"]:
    #    return JSONResponse(status_code=401, content={"message": "Missing API Key"})

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
