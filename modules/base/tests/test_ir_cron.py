import pytest
import time
from core.database import Database
from core.orm.registry import Registry
from core.module_loader import ModuleLoader
from core.orm.environment import Environment
from core.tools.config import config

class TestIrCron:
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
        
        IrCronCls = Registry.get("ir.cron")
        PartnerCls = Registry.get("res.partner")
        
        self.IrCron = IrCronCls(self.env)
        self.Partner = PartnerCls(self.env)

    def teardown_method(self):
        self.cr.close()
        self.conn.rollback()

    def test_cron_execution(self):
        partner = self.Partner.create({"name": "Cron Target"})
        
        code = f"""
partner = env['res.partner'].browse([{partner.id}])
partner.write({{'name': 'Cron Executed'}})
"""
        now = int(time.time())
        cron = self.IrCron.create({
            "name": "Test Cron",
            "model_id": "res.partner",
            "code": code,
            "interval_number": 1,
            "interval_type": "minutes",
            "nextcall": now - 10,
            "numbercall": 1,
            "active": True
        })
        
        # Process All
        # IrCron.process_all() is an instance method? 
        # Usually it's a model method. self.IrCron is an empty recordset (instance).
        self.IrCron.process_all()
        
        p_refresh = self.Partner.browse([partner.id])
        assert p_refresh.name == "Cron Executed"
        
        cron_refresh = self.IrCron.browse([cron.id])
        assert cron_refresh.nextcall > now
        assert cron_refresh.numbercall == 0
        assert cron_refresh.active is False

    def test_cron_interval(self):
        cron = self.IrCron.create({
            "name": "Interval Test",
            "interval_number": 1, 
            "interval_type": "hours",
            "nextcall": 1000,
            "numbercall": -1
        })
        
        cron._update_nextcall()
        
        # 1000 + 3600 = 4600
        assert cron.nextcall == 4600
