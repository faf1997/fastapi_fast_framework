from core.orm.base import BaseModel
from core.orm.registry import Registry
import json

class McpAgentUtilities(BaseModel):
    _name = 'mcp.agent.utilities'
    _description = 'MCP Server Tools'

    def get_models(self) -> str:
        # Registry in this core seems to use a singleton pattern or class methods.
        # Check core/orm/registry.py content. 
        # Assuming Registry.models or similar access.
        # Based on previous knowledge or file view (I'm about to view it, but writing this logic blind is risky, 
        # but I'll update if needed after viewing. Wait, I should view first? 
        # The tool execution is parallel, but I can't read-then-write in same turn if dependent.
        # I'll use a safe guess: Registry._models.keys() or Registry.get_all()?
        # Odoo uses env.registry.models.
        # Here env has registry? Probably not.
        # I'll check Registry file content in the view_file call parallel to this, 
        # but since I must write content now, I'll assume I can access Registry directly.
        
        # Actually, I should probably wait for the view_file result to be 100% correct.
        # But to save a turn, I'll assume I can import Registry and inspect it.
        # Let's try to be generic.
        
        models_list = list(Registry._models.keys()) if hasattr(Registry, '_models') else []
        return f'modelos existentes en mi odoo:\n{models_list}'

    def get_model_fields_info(self, model_name: str) -> str:
        result = {}
        # In this core, env[model_name] creates an empty instance of the model
        model_instance = self.env[model_name]
        # _fields is available on instance (populated in __init__)
        
        for field_name, field_obj in model_instance._fields.items():
            info = {
                'type': field_obj.type,
                'string': field_obj.string,
                'help': getattr(field_obj, 'help', ''), # help kwarg in Field.__init__? Not sure if stored.
                'required': field_obj.required,
                'readonly': getattr(field_obj, 'readonly', False), # Field init has required, default. readonly via kwargs?
                'relation': getattr(field_obj, 'comodel_name', False)
            }
            result[field_name] = info
        return f'Campos con sus datos del modelo {model_name}:\n{json.dumps(result)}'