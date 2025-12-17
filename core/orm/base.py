from .registry import Registry
from .fields import *
import psycopg2
import psycopg2.extras
from psycopg2 import sql

class MetaModel(type):
    def __init__(cls, name, bases, attrs):
        super(MetaModel, cls).__init__(name, bases, attrs)
        
        # Handle Extension
        if hasattr(cls, '_is_composed_model'):
             return

        if hasattr(cls, '_inherit') and cls._inherit:
             existing_model = Registry.get(cls._inherit)
             if existing_model:
                 # INHERITANCE COMPOSITION STRATEGY
                 # Instead of monkey-patching, we create a new class that inherits 
                 # from BOTH the new definition (cls) and the existing model.
                 # This ensures MRO is [NewClass, OldClass, Bases...] so super() works.
                 
                 # New class name based on extension to avoid conflicts
                 # But we register it under the ORIGINAL name.
                 
                 # We dynamically create a new class that mixes them.
                 # The 'cls' here is the class defined in the module (e.g. LogExtension1).
                 # We want the final entry in registry to be a class that has 'cls' as base
                 # and 'existing_model' as next base.
                 
                 # Construct the new class
                 # Name it consistent with the original to keep __name__ sane-ish? 
                 # Or use the extension name? Let's use the extension name but register it to original key.
                 
                 # Note: cls already inherits from BaseModel (usually). 
                 # existing_model also inherits from BaseModel.
                 # MRO will be: NewCombined -> cls -> existing_model -> BaseModel
                 
                 # We need to construct a new type that inherits from (cls, existing_model)
                 # Wait, 'cls' is the class currently being created by this type() call.
                 # We can't really change its bases *easily* inside __init__ without some magic, 
                 # BUT we can register a *Different* class than 'cls'.
                 
                 # Actually, we can just say: The 'cls' we just created is NOT the final model.
                 # The final model is a mixin of (cls, existing_model).
                 
                 new_bases = (cls, existing_model)
                 new_class = type(existing_model.__name__, new_bases, {'_is_composed_model': True})
                 
                 # Ensure _name and _table persist from the original if not overwritten
                 if not hasattr(new_class, '_table'):
                     new_class._table = existing_model._table
                     
                 # Update Registry with this new composite class
                 Registry.add(cls._inherit, new_class)
                 
                 return
             else:
                 pass

        if hasattr(cls, '_name') and cls._name:
            Registry.add(cls._name, cls)

class BaseModel(metaclass=MetaModel):
    _name = None
    _description = None
    _table = None
    
    
    def __init__(self, env, ids=()):
        self.env = env
        self.ids = list(ids) if isinstance(ids, (list, tuple)) else [ids]
        self._fields = {}
        self._fields = {}
        # Simple field introspection from Class (to return Field objects, not values)
        cls = self.__class__
        for attr_name in dir(cls):
            val = getattr(cls, attr_name, None)
            if isinstance(val, Field):
                self._fields[attr_name] = val
                val.name = attr_name

    def __len__(self):
        return len(self.ids)

    def __iter__(self):
        for id in self.ids:
            yield self.browse([id])

    def __bool__(self):
        return bool(self.ids)

    @property
    def id(self):
        return self.ids[0] if self.ids else False

    def __getattr__(self, name):
        if name in self._fields:
            if len(self) != 1:
                raise ValueError(f"Expected singleton: {self}")
            vals = self.read([name])
            return vals[0][name] if vals else False
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


    def check_access_rights(self, operation, raise_exception=True):
        """
        Check access rights for the operation.
        operation: 'read', 'write', 'create', 'unlink'
        """
        if self.env.uid == 1:
            return True
            
        # Check ir.model.access
        # We use raw SQL to avoid infinite recursion if we used the ORM to check permissions for ir.model.access
        query = """
            SELECT perm_{op} 
            FROM ir_model_access 
            WHERE model_id = %s AND user_id = %s
        """.format(op=operation)
        
        with self.env.cr.connection.cursor() as cur:
            cur.execute(query, (self._name, self.env.uid))
            res = cur.fetchone()
            
        if res and res[0]:
            return True
            
        if raise_exception:
            raise PermissionError(f"Access Denied: You do not have '{operation}' access to model '{self._name}'")
        return False


    @property
    def _table_name(self):
        return self._table or self._name.replace('.', '_')

    def browse(self, ids):
        return self.__class__(self.env, ids)
    
    def search(self, domain=[], limit=None, offset=0, order=None):
        self.check_access_rights('read')
        # Very basic search implementation
        # Domain is expected to be a list of tuples like [('field', '=', value)]
        query = sql.SQL("SELECT id FROM {}").format(sql.Identifier(self._table_name))
        where_clauses = []
        params = []
        
        if domain:
            query += sql.SQL(" WHERE ")
            for i, criterion in enumerate(domain):
                if i > 0:
                    query += sql.SQL(" AND ")
                field, operator, value = criterion
                where_clauses.append(sql.SQL("{} {} %s").format(sql.Identifier(field), sql.SQL(operator)))
                params.append(value)
            query += sql.SQL("").join(where_clauses)
            
        with self.env.cr.connection.cursor() as cur:
            cur.execute(query, params)
            res = cur.fetchall()
            return self.browse([r[0] for r in res])

    def create(self, vals):
        self.check_access_rights('create')
        # Separate m2m/o2m commands from standard fields
        # This is a simplified version
        columns = []
        values = []
        placeholders = []
        
        for k, v in vals.items():
            if k in self._fields:
                field = self._fields[k]
                if field.type in ('one2many', 'many2many'):
                     continue # Handle later
                columns.append(k)
                values.append(v)
                placeholders.append('%s')
                
        query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING id").format(
            sql.Identifier(self._table_name),
            sql.SQL(', ').join(map(sql.Identifier, columns)),
            sql.SQL(', ').join(map(sql.SQL, placeholders))
        )
        
        with self.env.cr.connection.cursor() as cur:
            cur.execute(query, values)
            new_id = cur.fetchone()[0]
            
        # TODO: Handle x2many commands
        return self.browse(new_id)

    def write(self, vals):
        self.check_access_rights('write')
        if not self.ids:
            return True
            
        set_clauses = []
        values = []
        
        for k, v in vals.items():
            if k in self._fields:
                 field = self._fields[k]
                 if field.type in ('one2many', 'many2many'):
                     continue # Handle later
                 set_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(k)))
                 values.append(v)
                 
        if not set_clauses:
            return True

        query = sql.SQL("UPDATE {} SET {} WHERE id IN %s").format(
            sql.Identifier(self._table_name),
            sql.SQL(', ').join(set_clauses)
        )
        values.append(tuple(self.ids))
        
        with self.env.cr.connection.cursor() as cur:
            cur.execute(query, values)
            
        return True

    def unlink(self):
        self.check_access_rights('unlink')
        if not self.ids:
            return True
        query = sql.SQL("DELETE FROM {} WHERE id IN %s").format(sql.Identifier(self._table_name))
        with self.env.cr.connection.cursor() as cur:
            cur.execute(query, (tuple(self.ids),))
        return True

    def read(self, fields=None):
        self.check_access_rights('read')
        if not self.ids:
            return []
        if fields is None:
            fields = list(self._fields.keys())
        fields = ['id'] + fields
        
        query = sql.SQL("SELECT {} FROM {} WHERE id IN %s").format(
            sql.SQL(', ').join(map(sql.Identifier, fields)),
            sql.Identifier(self._table_name)
        )
        
        with self.env.cr.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (tuple(self.ids),))
            return cur.fetchall()

    @classmethod
    def _auto_init(cls, env):
        # Naive migration strategy
        table_name = cls._table or cls._name.replace('.', '_')
        with env.cr.connection.cursor() as cur:
            # Check if table exists
            cur.execute("SELECT to_regclass(%s)", (table_name,))
            if not cur.fetchone()[0]:
                cur.execute(sql.SQL("CREATE TABLE {} (id SERIAL PRIMARY KEY)").format(sql.Identifier(table_name)))
            
            # Check columns
            # This requires an instance to inspect fields, but we are in classmethod
            # functionality needs a temporary instance or static field inspection
            fields = {}
            for attr_name in dir(cls):
                val = getattr(cls, attr_name)
                if isinstance(val, Field):
                    fields[attr_name] = val
            
            for field_name, field in fields.items():
                if field.type in ('one2many', 'many2many'):
                    continue
                
                # Check if column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = %s
                """, (table_name, field_name))
                if not cur.fetchone():
                    # Add column
                    col_type = "VARCHAR"
                    if field.type == 'integer': col_type = "INTEGER"
                    elif field.type == 'text': col_type = "TEXT"
                    elif field.type == 'boolean': col_type = "BOOLEAN"
                    elif field.type == 'float': col_type = "FLOAT"
                    elif field.type == 'many2one': col_type = "INTEGER" # FK TODO
                    
                    cur.execute(sql.SQL("ALTER TABLE {} ADD COLUMN {} {}").format(
                        sql.Identifier(table_name),
                        sql.Identifier(field_name),
                        sql.SQL(col_type)
                    ))

