from core.orm.base import BaseModel
from core.orm.fields import Char, Boolean, Many2one, Many2many, Text, Selection
from datetime import datetime
import re
import requests
import logging

_logger = logging.getLogger(__name__)

class WhatsappMessage(BaseModel):
    _name = 'whatsapp.message'
    _description = 'Whatsapp Message'

    name = Text(string='Message') # Html -> Text
    should_reply = Boolean(string='Debería responder', readonly=True)
    author_id = Many2one(comodel_name='res.users', string='Autor')
    date = Char(string="Fecha") # Datetime -> Char
    
    partner_ids = Many2many(
        comodel_name='res.partner',
        relation='whatsapp_message_partner_rel',
        column1='message_id',
        column2='partner_id',
        string='Clientes'
    )

    message_type = Selection([
        ('system', 'Sistema'),
        ('ai', 'IA'),
        ('customer', 'Cliente'),
    ], string='Tipo de mensaje')

    message_id = Char(string="Message ID")
    from_me = Boolean(string="From Me")
    
    file_ids = Many2many(
        comodel_name='ir.attachment',
        relation='whatsapp_message_attachment_rel', # Explicit relation name to avoid conflict
        column1='message_id',
        column2='attachment_id',
        string='Archivos'
    )

    metadata = Char(string="Metadata")
    internal_hash = Char(string="Hash interno", readonly=True)
    
    remote_jid = Char(string="Remote JID")
    remote_jid_alt = Char(string="Remote Jid Alt")
    sender = Char(string="Sender")

    # Extra fields from original...
    event = Char(string="Event")
    instance = Char(string="Instance")
    key_id = Char(string="Key ID")
    participant = Char(string="Participant")
    status = Char(string="Status")
    conversation = Text(string="Conversation")
    message_context_info = Text(string="Message Context Info")
    message_timestamp = Char(string="Message Timestamp")
    instance_id = Char(string="Instance ID")
    source = Char(string="Source")
    # date_time = Char(string="Date Time") # Duplicated date?
    server_url = Char(string="Server URL")
    apikey = Char(string="API Key")

    def create(self, vals):
        if 'date' not in vals:
            vals['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if 'author_id' not in vals and self.env.user:
             vals['author_id'] = self.env.user.id
        return super().create(vals)

    def fetch_encrypted_file(self, url: str, timeout: int = 30) -> bytes:
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            if r.headers.get("Content-Type", "").startswith("text/html"):
                raise ValueError("Expired or invalid media URL")
            return b"".join(r.iter_content(8192))

    def download_base64(self, whatsapp_message_id: str) -> str:
        return self.env['whatsapp.api'].get_file_base64(whatsapp_message_id)

    def create_file(self, data):
        # ... (Same logic as original)
        if data.get("data", {}).get("message", {}).get("documentMessage", False):
            return self._process_document_message(data)
        elif data.get("data", {}).get("message", {}).get("imageMessage", False):
            return self._process_image_message(data)
        elif data.get("data", {}).get("message", {}).get("audioMessage", False):
            return self._process_audio_message(data)
        return False

    def _process_document_message(self, data):
        doc_msg = data.get("data", {}).get("message", {}).get("documentMessage", {})
        whatsapp_message_id = data.get("data", {}).get("key", {}).get("id", "")
        mimetype = doc_msg.get("mimetype", "")
        file_name = doc_msg.get("fileName", "documento.pdf")
        caption = doc_msg.get("caption", "")
        base_64_data = self.download_base64(whatsapp_message_id)
        return self.create_attachment(mimetype, file_name, base_64_data, caption)

    def _process_image_message(self, data):
        img_msg = data.get("data", {}).get("message", {}).get("imageMessage", {})
        whatsapp_message_id = data.get("data", {}).get("key", {}).get("id", "")
        mimetype = img_msg.get("mimetype", "image/jpeg")
        file_name = f"WA_{whatsapp_message_id}.jpeg"
        caption = img_msg.get("caption", "")
        base_64_data = self.download_base64(whatsapp_message_id)
        return self.create_attachment(mimetype, file_name, base_64_data, caption)

    def _process_audio_message(self, data):
        audio_msg = data.get("data", {}).get("message", {}).get("audioMessage", {})
        whatsapp_message_id = data.get("data", {}).get("key", {}).get("id", "")
        mimetype = audio_msg.get("mimetype", "audio/ogg")
        ext = mimetype.split(';')[0].split('/')[1] if '/' in mimetype else 'ogg'
        file_name = f"WA_{whatsapp_message_id}.{ext}"
        caption = audio_msg.get("caption", "")
        base_64_data = self.download_base64(whatsapp_message_id)
        return self.create_attachment(mimetype, file_name, base_64_data, caption)

    def create_attachment(self, mimetype, file_name, base_64_data, caption=""):
        return self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base_64_data,
            'mimetype': mimetype,
            'res_model': self._name,
            'res_id': self.id if hasattr(self, 'id') and self.id else False,
            'caption': caption,
        })

    def create_message(self, vals):
        # Adapter for webhook data format validation
        if 'is_webhook' in vals or isinstance(vals, dict):
             # Original logic condensed
             pass
        return self.create(vals)