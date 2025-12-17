from core.orm.base import BaseModel
from core.orm.fields import Char, Boolean

class ResPartner(BaseModel):
    _name = "res.partner"
    _description = "Contact"

    name = Char(string="Name", required=True)
    email = Char(string="Email")
    phone = Char(string="Phone")
    street = Char(string="Street")
    city = Char(string="City")
    state = Char(string="State")
    country = Char(string="Country")
    is_company = Boolean(string="Is Company")
