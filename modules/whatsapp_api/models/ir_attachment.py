from core.orm.base import BaseModel
from core.orm.fields import Char

class IrAttachment(BaseModel):
    _inherit = 'ir.attachment'

    caption = Char(string='Subtitulo')