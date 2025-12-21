from core.orm.base import BaseModel
from core.orm.fields import Text

class WhatsappLog(BaseModel):
    _name = 'whatsapp.log'
    _description = 'Whatsapp Log'

    name = Text(string='whatsapp log')