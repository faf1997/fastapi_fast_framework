from datetime import datetime
from core.orm.base import BaseModel
from core.orm.fields import Char, Many2one, One2many, Selection, Text, Boolean

# Helpers
def _get_datetime_now(self):
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class IaConversation(BaseModel):
    _name = 'ia.conversation'
    _description = 'IA Conversation'

    name = Char(string='Nombre', required=True) 
    # Default lambda logic handled in create if needed, or simple default string not supported as dynamic yet.

    datetime = Char(string='Fecha y hora', required=True) # Datetime field not in core.orm.fields yet, using Char
    
    message_ids = One2many(
        comodel_name='ia.message',
        inverse_name='conversation_id',
        string='Messages'
    )

    def create(self, vals):
        if 'datetime' not in vals:
            vals['datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if 'name' not in vals:
             vals['name'] = "Nueva conversación %s" % vals['datetime']
        return super().create(vals)

    def action_open_wizard(self):
        # NOT IMPLEMENTED: Frontend Actions
        return False

    def action_open_conversation(self):
        # NOT IMPLEMENTED: Frontend Actions
        return False

    def get_recordset_in_string_format(self, message_ids):
        # message_ids is a list of instances or a generic list of browse records in this ORM?
        # In this ORM, One2many returns a list of instances (if I recall read() properly, or check One2many impl).
        # Actually One2many in `read` isn't implemented fully in `read` method shown (it says "Handle later").
        # Use simple list for now.
        
        if not isinstance(message_ids, list):
             # Try to convert to list if it's a RecordSet (which is iterable)
             message_ids = list(message_ids)

        # Context limit
        # limit = self.env.company.context_message_count 
        # Hardcoding limit for now as no company settings.
        limit = 50 
        
        buffer = []
        last_message_ids = message_ids[-limit:] if len(message_ids) > limit else message_ids
        
        # Sorting? message_ids is a list of objects.
        # Assuming they have 'id' or 'datetime'.
        last_message_ids.sort(key=lambda x: x.id)
        
        for message in last_message_ids:
            if not message.name:
                continue
            buffer.append(f"#--------- fecha del mensaje: {message.datetime} --------------\n{message.message_type}: {message.name}")
        
        # Access mcp.tools via env
        mcp_tools = self.env['mcp.tools']
        # Call strip_equal_fences via an instance or static? It's an instance method in my refactor.
        # But creating an empty instance is cheap.
        buffer_str = mcp_tools.strip_equal_fences("\n".join(buffer))
        
        fecha = f"===FECHA ACTUAL===\n{datetime.now()}\n===FECHA ACTUAL==="
        return f"{fecha}\n===MENSAJES===\n" + buffer_str + "\n===FIN MENSAJES==="


class IaMessage(BaseModel):
    _name = 'ia.message'
    _description = 'IA Message'
    # _order = 'create_date desc'

    name = Text(string='Mensaje', required=True) # Html -> Text
    
    conversation_id = Many2one(
        comodel_name='ia.conversation',
        string='Conversación'
        # ondelete='cascade'
    )
    
    message_type = Selection([
        ('user', 'Usuario'),
        ('ia', 'IA'),
        ('system', 'Sistema'),
    ], string='Tipo', default='user')
    
    datetime = Char(string='Fecha y hora', required=True) # Datetime -> Char

    def create(self, vals):
        if 'datetime' not in vals:
            vals['datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return super().create(vals)