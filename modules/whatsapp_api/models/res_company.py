from core.orm.base import BaseModel
from core.orm.fields import Char

class ResCompany(BaseModel):
    _name = 'res.company'
    _description = 'Company'
    # _inherit removed as it is the base definition in this context or standalone.

    whatsapp_api_key = Char(string='Whatsapp api key')
    whatsapp_instance = Char(string="Instancia")
    whatsapp_server = Char(string='Whatsapp server')
    whatsapp_phone_number = Char(string='Número de Whatsapp')

    def create(self, vals):
        if 'whatsapp_server' in vals and vals['whatsapp_server']:
            if not vals['whatsapp_server'].startswith("https://"):
                raise ValueError('La url debe ser https')
        return super().create(vals)

    def write(self, vals):
        if 'whatsapp_server' in vals and vals['whatsapp_server']:
             if not vals['whatsapp_server'].startswith("https://"):
                raise ValueError('La url debe ser https')
        return super().write(vals)

    def get_whatsapp_instance(self):
        # self.ensure_one() # Not implemented in base, implied by singleton check if needed
        if len(self) != 1:
            raise ValueError("Expected singleton: %s" % self)
            
        # Parent company logic omitted as parent_id not defined in this model
        if self.whatsapp_instance:
            return self.whatsapp_instance

        # Fallback to env.company behavior assumption: self is the company
        # If we had a mechanism to get 'current company', we'd use it. 
        # For now, simplistic return.
        
        raise ValueError('No se puede enviar mensajes porque no hay una instancia de whatsapp configurada en la empresa')
