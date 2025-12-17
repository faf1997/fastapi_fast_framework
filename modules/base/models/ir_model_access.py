from core.orm.base import BaseModel
from core.orm.fields import Char, Boolean, Many2one

class IrModelAccess(BaseModel):
    _name = "ir.model.access"
    _description = "Model Access"

    name = Char(string="Name", required=True)
    model_id = Char(string="Model Name", required=True) # Storing name for simplicity instead of ir.model link
    user_id = Many2one("res.users", string="User") # If NULL, global? Or specific user.
    # Group implementation is complex, so let's stick to user-based or simpler role based as requested "user permissions per model"
    
    perm_read = Boolean(string="Read Access")
    perm_write = Boolean(string="Write Access")
    perm_create = Boolean(string="Create Access")
    perm_unlink = Boolean(string="Delete Access")
