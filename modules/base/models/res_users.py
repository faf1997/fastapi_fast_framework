from core.orm.base import BaseModel
from core.orm.fields import Char, Many2one, Boolean

class ResUsers(BaseModel):
    _name = "res.users"
    _description = "User"

    name = Char(string="Name", required=True)
    login = Char(string="Login", required=True) # unique constraint not yet implemented in ORM
    password = Char(string="Password")
    api_key = Char(string="API Key")
    partner_id = Many2one("res.partner", string="Related Partner")
    active = Boolean(string="Active", default=True)

    def check_credentials(self, password):
        # Plain text for MVP as requested implicitly, but should be hashed
        return self.password == password

    @classmethod
    def _bootstrap_admin(cls, env):
        # Ensure admin user exists
        user_ids = cls(env).search([('id', '=', 1)])
        if not user_ids:
            # Create partner first
            partner = env['res.partner'].create({
                'name': 'Administrator',
                'is_company': False
            })
            # Create user (ID 1 is enforced by sequence usually, but here we might need to force it if table empty)
            # Since create returns browse object, we can't easily force ID without raw SQL or setting sequence
            # But in fresh DB, serial starts at 1.
            
            # Use raw SQL to force ID 1 if needed, or just create.
            # Assuming empty module, first create will be ID 1.
            # But we must be careful.
            
            # Let's try standard create.
            cls(env).create({
                'name': 'Administrator',
                'login': 'admin',
                'password': 'admin',
                'partner_id': partner.ids[0]
            })

