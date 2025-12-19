import pytest
import base64
from core.database import Database
from core.orm.registry import Registry
from core.module_loader import ModuleLoader
from core.orm.environment import Environment
from core.tools.config import config

class TestIrAttachment:
    @classmethod
    def setup_class(cls):
        if Database._pool is None:
            Database.initialize()
            
        cls.conn = Database.get_connection()
        with cls.conn.cursor() as cr:
            env = Environment(cr, 1, {})
            loader = ModuleLoader(config.MODULES_PATH)
            loader.load_modules(env)
            cls.conn.commit()

    @classmethod
    def teardown_class(cls):
        Database.return_connection(cls.conn)

    def setup_method(self):
        self.cr = self.conn.cursor()
        self.env = Environment(self.cr, 1, {})
        IrAttachmentCls = Registry.get("ir.attachment")
        self.IrAttachment = IrAttachmentCls(self.env)

    def teardown_method(self):
        self.cr.close()
        self.conn.rollback()

    def test_create_attachment(self):
        data = b"Hello World"
        encoded = base64.b64encode(data).decode('utf-8')
        
        attachment = self.IrAttachment.create({
            "name": "test.txt",
            "type": "binary",
            "datas": encoded,
            "res_model": "res.partner",
            "res_id": 1
        })
        
        assert attachment
        assert attachment.name == "test.txt"
        assert attachment.datas == encoded
        
        # Verify persistence
        att_read = self.IrAttachment.browse([attachment.id])
        assert att_read.datas == encoded
