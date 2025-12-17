import pytest
from core.orm.base import BaseModel
from core.orm.registry import Registry
from core.orm.fields import Char

def test_multiple_inheritance_mixin(env_test):
    """
    Test extending a model with multiple inheritance (Mixins).
    _inherit = ['target.model', 'mixin.model']
    """
    # 1. Define Target Model
    class TargetModel(BaseModel):
        _name = 'target.multi'
        name = Char()
        
        def hello(self):
            return ["Target"]
            
    TargetModel._auto_init(env_test)

    # 2. Define a Mixin (Abstract-ish, but registered for now so we can fetch it)
    class MyMixin(BaseModel):
        _name = 'my.mixin'
        
        def hello(self):
            return ["Mixin"]
            
        def mixin_method(self):
            return "MixinMethod"

    # 3. Define Extension that inherits from both
    class MultiExtension(BaseModel):
        _inherit = ['target.multi', 'my.mixin']
        
        def hello(self):
            # Should call Target.hello() then ???
            # MRO depends on composition order.
            # Usually: Extension -> Target -> Mixin
            res = super().hello()
            res.append("Extension")
            return res

    # 4. Instantiate Target and check behavior
    Model = env_test['target.multi']
    instance = Model.create({'name': 'Test'})
    
    # Check Mixin method presence
    assert hasattr(instance, 'mixin_method')
    assert instance.mixin_method() == "MixinMethod"
    
    # Check method override and super()
    # If MRO is [MultiExtension, TargetModel, MyMixin], then:
    # super() in Extension calls TargetModel.hello().
    # TargetModel.hello() returns ["Target"].
    # Result: ["Target", "Extension"]
    # Wait, simple Mixin usage in Odoo:
    # If TargetModel inherits from BaseModel, and MyMixin inherits from BaseModel.
    # NewClass(Extension, TargetModel, MyMixin).
    # MRO: Extension, TargetModel, MyMixin, BaseModel.
    # If TargetModel.hello calls super() -> BaseModel.hello (error?).
    # If TargetModel.hello does NOT call super(), then MyMixin.hello is NOT called unless Target calls it?
    # OR if we want Mixin to run, TargetModel should ideally be designed to call super, OR Mixin should be first?
    # If `_inherit = ['my.mixin', 'target.multi']`:
    # NewClass(Extension, MyMixin, TargetModel).
    # MRO: Extension, MyMixin, TargetModel.
    # super() calls MyMixin.hello(). MyMixin returns ["Mixin"]. 
    # TargetModel.hello() is NOT called unless MyMixin calls super().
    
    # Let's assume the user wants to ADD mixin functionality.
    # The order in `_inherit` matters.
    # Odoo: `_inherit = ['mail.thread', 'res.partner']`? No Odoo usually does `_inherit = ['res.partner', 'mail.thread']`.
    # Actually Odoo creates a new class inheriting from them.
    
    # FOR THIS TEST: We expect Extension -> Target -> Mixin?
    # If Target doesn't call super, Mixin methods usually just "exist" on the instance.
    # But if we want `hello` to be cumulative...
    # Let's just assert that `super()` works and calls the next in line.
    
    res = instance.hello()
    assert "Target" in res
    assert "Extension" in res
    # We don't necessarily expect "Mixin" unless Target calls super.
    # But we DO expect 'mixin_method' to be available.
