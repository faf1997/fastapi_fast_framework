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
                'partner_id': partner.ids[0],
                'api_key': 'admin' # Default for dev simplicity, or use uuid
            })
            import logging
            logger = logging.getLogger(__name__)
            logger.info("--------------------------------------------------")
            logger.info("Admin User Created")
            logger.info("Login: admin")
            logger.info("Password: admin")
            logger.info("API Key: admin")
            logger.info("--------------------------------------------------")
        else:
            # Check/Set API Key if missing for existing admin
            admin = cls(env).browse([1])
            if not admin.api_key:
                import uuid
                new_key = str(uuid.uuid4())
                admin.write({'api_key': new_key})
                key_to_show = new_key
            else:
                key_to_show = admin.api_key
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info("--------------------------------------------------")
            logger.info(f"Admin API Key: {key_to_show}")
            logger.info("--------------------------------------------------")

