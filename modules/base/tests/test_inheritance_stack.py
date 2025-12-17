import pytest
from core.orm.base import BaseModel
from core.orm.registry import Registry
from core.orm.fields import Char

def test_method_override_with_super(env_test):
    """
    Test that extending a model and overriding a method calls the original method via super().
    """
    # 1. Define base model
    class BaseLog(BaseModel):
        _name = 'test.log'
        name = Char() # Dummy field for INSERT
        
        def log(self):
            return ["Base"]
            
    BaseLog._auto_init(env_test)

    # 2. Define Extension 1
    class LogExtension1(BaseModel):
        _inherit = 'test.log'
        
        def log(self):
            res = super().log() # This is expected to call BaseLog.log
            res.append("Ext1")
            return res

    # 3. Define Extension 2
    class LogExtension2(BaseModel):
        _inherit = 'test.log'
        
        def log(self):
            # This 'super()' is tricky. 
            # If our implementation is correct (Mixin based), 
            # super() here should call LogExtension1.log
            res = super().log()
            res.append("Ext2")
            return res

    # Force re-instantiation of model from registry to pick up changes
    # note: MetaModel logic runs at class definition time.
    
    # 4. Instantiate and test
    # The registry should now point 'test.log' to the final composed class
    Model = env_test['test.log']
    instance = Model.create({'name': 'Test'})
    
    # Expected: ["Base", "Ext1", "Ext2"]
    # Current MonkeyPatch implementation:
    # - LogExtension1 overwrites BaseLog.log. super() in LogExtension1 points to BaseModel (empty/error) or object?
    # - LogExtension2 overwrites LogExtension1.log.
    # It will likely fail or return just ["Ext2"] or crash.
    
    try:
        result = instance.log()
        assert result == ["Base", "Ext1", "Ext2"]
    except AttributeError as e:
        pytest.fail(f"Super call failed: {e}")
