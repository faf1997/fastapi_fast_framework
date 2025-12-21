import sys
import os
from unittest.mock import MagicMock

# Add root to sys.path
sys.path.append(os.getcwd())

# Mock psycopg2
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['psycopg2.pool'] = MagicMock()
sys.modules['psycopg2.sql'] = MagicMock()

from core.module_loader import ModuleLoader
from core.orm.registry import Registry

# Mocks for Env
class MockCursor:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def execute(self, *args): pass
    def fetchone(self): return [1] # Return logic ID 1 for bootstrap checks
    def fetchall(self): return []

class MockConnection:
    def cursor(self, *args, **kwargs): return MockCursor()

class MockCR:
    def __init__(self):
        self.connection = MockConnection()

class MockEnv:
    def __init__(self):
        self.cr = MockCR()
        self.uid = 1

    def __getitem__(self, model_name):
        ModelClass = Registry.get(model_name)
        if ModelClass:
            # Instantiate
            return ModelClass(self)
        return MagicMock() # Return mock if model not found to avoid crash during bootstrap

def verify_modules():
    print("Starting verification...")
    
    loader = ModuleLoader(modules_path="modules")
    env = MockEnv()
    
    # Load modules
    loader.load_modules(env=env)
    
    print("Modules loaded.")
    
    # Check Registry
    expected_models = [
        'mcp.tools',
        'mcp.agent',
        'mcp.default.prompt',
        'mcp.launcher',
        'ia.conversation',
        'ia.message',
        'mcp.agent.utilities'
    ]
    
    missing = []
    for m in expected_models:
        if Registry.get(m):
            print(f"✅ Model {m} found.")
        else:
            print(f"❌ Model {m} NOT found.")
            missing.append(m)
            
    if missing:
        print("FAIL: Some models are missing.")
        sys.exit(1)
    
    print("SUCCESS: All models loaded correctly.")

if __name__ == "__main__":
    verify_modules()
