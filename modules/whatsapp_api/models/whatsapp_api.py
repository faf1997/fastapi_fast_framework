from core.orm.base import BaseModel
import re
import requests
import logging
import base64, binascii
from urllib.parse import urljoin, quote
import hashlib
import unicodedata
from datetime import datetime

_logger = logging.getLogger(__name__)

def _sanitize_b64(b64: str) -> str:
    b64 = re.sub(r"\s+", "", b64)
    missing = (-len(b64)) % 4
    if missing:
        b64 += "=" * missing
    try:
        base64.b64decode(b64, validate=True)
    except binascii.Error:
        base64.b64decode(b64, validate=False)
    return b64

def _mediatype_from_mime(mime: str) -> str:
    return "image" if mime.startswith("image/") else ("video" if mime.startswith("video/") else "document")


class WhatsappApi(BaseModel):
    _name = 'whatsapp.api'
    _description = 'Whatsapp API Service'

    def _get_company(self):
        # Mock singleton company logic
        companies = self.env['res.company'].search([], limit=1)
        if not companies:
            raise ValueError("No company configured")
        return companies[0]

    def send_message(self, partner_id: int, message: str, ai=False, metadata=False):
        if isinstance(partner_id, int):
            partner = self.env['res.partner'].browse([partner_id])
            if not partner:
                raise ValueError(f"El partner con id {partner_id} no existe")
        else:
            partner = partner_id

        if not getattr(partner, 'whatsapp', False): # Use getattr since field might be dynamically added or mocked
            raise ValueError(f'El cliente no tiene el numero de su móvil/whatsapp, id: {partner.id}')
        
        company = self._get_company()
        if not company.whatsapp_server:
            raise ValueError('No está configurado el servidor de whatsapp')
        if not company.whatsapp_instance:
            raise ValueError('No está configurada la instancia de whatsapp')

        # Firewall logic...
        # Simplified:
        # hash = self.launch_firewalls(partner, message)
        # if not hash: return {}

        url = f"{company.whatsapp_server.rstrip('/')}/message/sendText/{company.whatsapp_instance}"
        final_message = f"\u200b{message}" if ai else message
        payload = self.get_payload_message(partner, final_message) # Assume html_to_whatsapp_friendly removed/simplified
        
        headers = {
            "apikey": company.whatsapp_api_key,
            "Content-Type": "application/json"
        }

        try:
             response = requests.post(url, json=payload, headers=headers, timeout=30)
        except Exception as e:
             raise ValueError(f"Error connecting to WhatsApp Server: {e}")

        if response.status_code != 201:
            raise ValueError(f'{response.text}')
        elif response.status_code == 201:
            created_message = self.env["whatsapp.message"].create({
                'name': message,
                'partner_ids': [(4, partner.id)],
                'message_type': 'ai' if ai else 'system',
                'author_id': self.env.user.id if self.env.user else 1,
                'from_me': True,
                'message_id': response.json().get("key", {}).get("id", False),
                'metadata': str(metadata) if metadata else False,
                # 'internal_hash': hash,
            })
            return response.json()
        return {}

    def get_payload_message(self, partner, message):
        # Logic to extract clean number
        client_mobile = ''.join([char for char in partner.whatsapp if char.isdigit()])
        return {
            "number": client_mobile,
            "text": message,
            "delay": 0,
            "linkPreview": True,
            "mentionsEveryOne": True,
        }

    def get_file_base64(self, whatsapp_message_id:str):
        company = self._get_company()
        if not company.whatsapp_server:
            raise ValueError(f"No whatsapp server")
        
        headers = {
            "apikey": company.whatsapp_api_key,
            "Content-Type": "application/json"
        }
        url = f"{company.whatsapp_server.rstrip('/')}/chat/getBase64FromMediaMessage/{company.whatsapp_instance}"
        payload = {
            "message": {"key": {"id": whatsapp_message_id}},
            "convertToMp4": True
        }
        
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        return r.json().get("base64", None)
