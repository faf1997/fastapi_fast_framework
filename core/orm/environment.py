import psycopg2
from psycopg2.extras import RealDictCursor
from .registry import Registry

class Environment:
    def __init__(self, cr, uid, context=None):
        self.cr = cr
        self.uid = uid
        self.context = context or {}
        self.registry = Registry()

    def __getitem__(self, model_name):
        model_class = self.registry.get(model_name)
        if model_class:
            # Return an instance/recordset bound to this environment
            return model_class(self)
        raise KeyError(f"Model '{model_name}' not found in registry")

    @property
    def user(self):
        return self['res.users'].browse(self.uid)

    @property
    def company(self):
        # Placeholder for multi-company support
        return None
