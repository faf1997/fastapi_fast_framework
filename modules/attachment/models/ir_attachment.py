from core.orm.base import BaseModel
from core.orm import fields

class IrAttachment(BaseModel):
    _name = "ir.attachment"
    _description = "Attachment"

    name = fields.Char(string="Name", required=True)
    type = fields.Selection([
        ('binary', 'Binary'),
        ('url', 'URL')
    ], string="Type", default='binary')
    datas = fields.Binary(string="File Content")
    url = fields.Char(string="Url")
    res_model = fields.Char(string="Resource Model")
    res_id = fields.Integer(string="Resource ID")
    mimetype = fields.Char(string="Mime Type")
    file_size = fields.Integer(string="File Size")
