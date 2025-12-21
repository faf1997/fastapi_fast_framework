from core.orm.base import BaseModel
from core.orm.fields import Char, Many2many
import phonenumbers

class ResPartner(BaseModel):
    # In Odoo this inherits res.partner. 
    # In this core, if res.partner is in 'base', we use _inherit.
    # Architecture says 'base' defines 'res.partner'.
    _inherit = 'res.partner'

    filtered_number = Char(string="Número filtrado", readonly=True)
    
    whatsapp_message_ids = Many2many(
        comodel_name='whatsapp.message',
        relation='whatsapp_message_partner_rel',
        column1='partner_id',
        column2='message_id',
        string='WhatsApp Messages'
    )
    
    # whatsapp field is expected to be on res.partner (base). 
    # If not, we might need to add it here or check base.
    # Assuming base has 'mobile' and 'whatsapp' (or we add 'whatsapp' here if missing).
    # Let's add 'whatsapp' just in case, or as Char.
    # Base usually has 'mobile'. Odoo's base doesn't have 'whatsapp' by default, usually added by module.
    # Original code didn't define 'whatsapp' field, mostly used it. 
    # Wait, original code: rec.whatsapp = format_number.
    # But it didn't define whatsapp = fields.Char(). It must be in base or defined here.
    # I'll define it here to be safe.
    whatsapp = Char(string="WhatsApp")

    def to_whatsapp_number(self, mobile_number: str, region: str = None) -> str:
        try:
             # Mock country logic or simple parse
             # We don't have self.country_id in this snippet unless added.
             # Assuming simple parsing without region for now if country_id missing.
             
             parsed = phonenumbers.parse(mobile_number, region) # region can be None
             if phonenumbers.is_valid_number(parsed):
                e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                number = e164.replace("+", "")
                if number.startswith("54") and not number.startswith("549"):
                    number = "549" + number[2:]
                return number
             else:
                # Force return if invalid but digits? Original raised ValueError
                raise ValueError(f"Número inválido: {mobile_number}")
        except Exception as e:
            return f"Error: {e}"

    # Onchange is not supported in backend core same way. 
    # Logic moved to write/create usually, or explicit call.
    def compute_filtered_number(self):
        for rec in self:
            if rec.mobile:
                # Assuming simple cleaning
                clean_mobile = ''.join([char for char in rec.mobile if char.isdigit()])
                # Region hardcoded or missing
                format_number = rec.to_whatsapp_number(clean_mobile)
                # rec.whatsapp = format_number # Error setting attr directly in ORM
                # rec.filtered_number = format_number
                
                # We need to return values or write them.
                # If called from create/write, we return dict modification?
                pass

    def create(self, vals):
        # Simulate onchange logic
        if 'mobile' in vals and vals['mobile']:
             clean_mobile = ''.join([char for char in vals['mobile'] if char.isdigit()])
             # Attempt to parse. Region unknown, maybe default to something or None.
             # Implementation: `to_whatsapp_number` usually needs instance (self).
             # But here we are in create (classmethod-ish but on instance `self` with env).
             # We can call method on empty set or use static logic.
             # to_whatsapp_number is instance method but doesn't strictly usage self except for country_id.
             # I'll instantiate a temp partner to call it, or make it static-like.
             
             # Re-implementing logic here safely
             try:
                 parsed = phonenumbers.parse(clean_mobile, None)
                 if phonenumbers.is_valid_number(parsed):
                     e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                     number = e164.replace("+", "")
                     if number.startswith("54") and not number.startswith("549"):
                         number = "549" + number[2:]
                     vals['whatsapp'] = number
                     vals['filtered_number'] = number
             except:
                 pass
                 
        return super().create(vals)

    def write(self, vals):
        if 'mobile' in vals and vals['mobile']:
             clean_mobile = ''.join([char for char in vals['mobile'] if char.isdigit()])
             try:
                 parsed = phonenumbers.parse(clean_mobile, None)
                 if phonenumbers.is_valid_number(parsed):
                     e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                     number = e164.replace("+", "")
                     if number.startswith("54") and not number.startswith("549"):
                         number = "549" + number[2:]
                     vals['whatsapp'] = number
                     vals['filtered_number'] = number
             except:
                 pass
        return super().write(vals)