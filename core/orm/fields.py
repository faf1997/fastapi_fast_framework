class Command:
    """
    Odoo-like Command object for x2many fields.
    0: CREATE
    1: UPDATE
    2: DELETE
    3: UNLINK
    4: LINK
    5: CLEAR
    6: SET
    """
    @staticmethod
    def create(values):
        return (0, 0, values)
    
    @staticmethod
    def update(id, values):
        return (1, id, values)
    
    @staticmethod
    def delete(id):
        return (2, id, 0)
    
    @staticmethod
    def unlink(id):
        return (3, id, 0)
    
    @staticmethod
    def link(id):
        return (4, id, 0)
    
    @staticmethod
    def clear():
        return (5, 0, 0)
    
    @staticmethod
    def set(ids):
        return (6, 0, ids)

class Field:
    def __init__(self, string=None, required=False, default=None, **kwargs):
        self.string = string
        self.required = required
        self.default = default
        self.name = None  # Set by metaclass
        self.model_name = None # Set by metaclass

    def __set_name__(self, owner, name):
        self.name = name
        self.model_name = owner._name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        vals = instance.read([self.name])
        return vals[0][self.name] if vals else False


class Char(Field):
    type = 'char'

class Text(Field):
    type = 'text'

class Integer(Field):
    type = 'integer'

class Float(Field):
    type = 'float'

class Boolean(Field):
    type = 'boolean'

class Many2one(Field):
    type = 'many2one'
    def __init__(self, comodel_name, string=None, **kwargs):
        super().__init__(string=string, **kwargs)
        self.comodel_name = comodel_name

class One2many(Field):
    type = 'one2many'
    def __init__(self, comodel_name, inverse_name, string=None, **kwargs):
        super().__init__(string=string, **kwargs)
        self.comodel_name = comodel_name
        self.inverse_name = inverse_name

class Many2many(Field):
    type = 'many2many'
    def __init__(self, comodel_name, relation=None, column1=None, column2=None, string=None, **kwargs):
        super().__init__(string=string, **kwargs)
        self.comodel_name = comodel_name
        self.relation = relation
        self.column1 = column1
        self.column2 = column2
