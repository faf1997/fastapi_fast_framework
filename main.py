from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import psycopg2
from contextlib import asynccontextmanager
from core.tools.config import config
from core.orm.environment import Environment
from core.module_loader import ModuleLoader
from core.orm.registry import Registry
from core.release import version

import logging

from core.database import Database

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        Database.initialize()
        
        # Initialize Modules using a dedicated connection
        conn = Database.get_connection()
        try:
            with conn.cursor() as cr:
                # Create a supervisor env
                env = Environment(cr, 1, {}) 
                loader = ModuleLoader(config.MODULES_PATH)
                loader.load_modules(env)
            
            # Register Routes from loaded modules
            for router in loader.get_routers():
                app.include_router(router)
                
            conn.commit()
        finally:
            Database.return_connection(conn)
            
        yield
    except Exception as e:
        print(f"Startup failed: {e}")
        raise e
    finally:
        # Shutdown
        Database.close_all()

app = FastAPI(title="Odoo-like Core", lifespan=lifespan)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    # Get connection from Pool
    # This is non-blocking (in threading sense, but still efficient)
    conn = Database.get_connection()
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
    
    request.state.user_id = user_id or 1 
    
    if api_key and not user_id:
         Database.return_connection(conn) # Important: return early
         return JSONResponse(status_code=401, content={"message": "Invalid API Key"})

    try:
        response = await call_next(request)
        conn.commit()
        return response
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        # Return connection to pool
        Database.return_connection(conn)

@app.get("/")
def read_root():
    return {
        "message": "Odoo-like Core Running",
        "version": version,
        "models": list(Registry.models().keys())
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
