import sys
import os
from unittest.mock import MagicMock

# Add root to sys.path
sys.path.append(os.getcwd())

# Mock dependencies
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['psycopg2.pool'] = MagicMock()
sys.modules['psycopg2.sql'] = MagicMock()
sys.modules['phonenumbers'] = MagicMock()
sys.modules['requests'] = MagicMock()

from core.module_loader import ModuleLoader
from core.orm.registry import Registry

# Mocks for Env
class MockCursor:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def execute(self, *args): pass
    def fetchone(self): return [1] # Return logic ID 1
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
        self.user = MagicMock()
        self.user.id = 1

    def __getitem__(self, model_name):
        ModelClass = Registry.get(model_name)
        if ModelClass:
            # Instantiate
            return ModelClass(self)
        # Return mock for unknown models to safely fail checks or mock dependency
        return MagicMock()

def verify_modules():
    print("Starting whatsapp_api verification...")
    
    loader = ModuleLoader(modules_path="modules")
    env = MockEnv()
    
    # Load all modules (including mcp_tools, whatsapp_api)
    loader.load_modules(env=env)
    
    print("Modules loaded.")
    
    # Check Registry
    expected_models = [
        'whatsapp.api',
        'whatsapp.message',
        'res.company',
        # 'res.partner', # Base model, should be there
        # 'ir.attachment' # Base model
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

    # Test instantiation and basic method call
    wap = env['whatsapp.api']
    print(f"✅ Instantiated whatsapp.api: {wap}")
    
    # Test message creation logic (mocked)
    vals = {'name': 'Test Msg', 'date': '2023-01-01 12:00:00'}
    msg = env['whatsapp.message'].create(vals)
    print(f"✅ Created whatsapp.message (mocked DB): {msg}")

    print("SUCCESS: whatsapp_api verified.")

if __name__ == "__main__":
    verify_modules()
