import pytest
import time
import json
import os
from core.database import Database
from core.orm.registry import Registry
from core.module_loader import ModuleLoader
from core.orm.environment import Environment
from core.tools.config import config
from modules.queue_job.models.queue_job import with_delay

class TestQueueJob:
    @classmethod
    def setup_class(cls):
        # Initialize Database and Modules once
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
        # Database.close_all() # Don't close if other tests need it

    def setup_method(self):
        # Use a fresh cursor/env for each test if needed, or reuse class one.
        # Ideally, tests should run in transaction rollback. 
        # For now, we just get a new env from registry which uses a fresh cursor if we request it,
        # but Registry.get returns the model class. Model methods usually expect self.env.
        
        # We need to construct an environment for our test calls
        self.cr = self.conn.cursor()
        self.env = Environment(self.cr, 1, {})
        
        # Get Model Classes (they are classes, so they don't hold env yet until instantiation)
        # But wait, create/browse need env.
        # Logic: Model(env) -> instance.
        
        # The Registry stores classes.
        QueueJobCls = Registry.get("queue.job")
        PartnerCls = Registry.get("res.partner")
        
        # To call create, we assume Cls.create(vals) uses an internal env if available?
        # Looking at BaseModel.create:
        # It calls self.check_access_rights.
        # It needs self.env.
        # But if we call Class.create(vals), 'self' is the Class. 
        # The Current ORM implementation in BaseModel seems to expect an instance for some things,
        # or it relies on 'env' being passed to __init__.
        
        # Wait, if I call Model.create(vals), I need an instance bound to an env?
        # Usually in Odoo: env['model'].create(vals).
        # env['model'] returns an empty dataset (instance) with env bound.
        
        # So I need:
        self.QueueJob = QueueJobCls(self.env)
        self.Partner = PartnerCls(self.env)

    def teardown_method(self):
        self.cr.close()
        # Rollback via connection? 
        # Since we reuse connection in class, we should rollback here to keep it clean.
        self.conn.rollback()

    def test_with_delay_creates_job(self):
        partner = self.Partner.create({"name": "Test Partner"})
        
        # Call with_delay
        job = partner.with_delay(eta=10).write({"name": "Delayed Name"})
        
        assert job
        assert job.model_name == "res.partner"
        assert job.method_name == "write"
        assert job.state == "pending"
        
        args = json.loads(job.args)
        assert args == [{"name": "Delayed Name"}]
        
        now = int(time.time())
        assert job.eta >= now + 10

    def test_run_job_execution(self):
        partner = self.Partner.create({"name": "Exec Partner"})
        job = partner.with_delay().write({"name": "Updated Name"})
        
        # We need to run job. But 'job' returned by with_delay (via create) 
        # is an instance of QueueJob bound to self.env (from partner).
        # partner was bound to self.env.
        # So job should have env.
        
        res = job.run_job()
        
        # Re-browse to get updated state (write doesn't update object in place)
        job = self.QueueJob.browse([job.id])
        
        assert res is True
        assert job.state == "done"
        
        # Check side effect
        # Re-browse to get fresh data
        p_refresh = self.Partner.browse([partner.id])
        assert p_refresh.name == "Updated Name"

    def test_dependency(self):
        partner = self.Partner.create({"name": "Dep Partner"})
        
        job1 = partner.with_delay().write({"name": "Step 1"})
        job2 = partner.with_delay(job_id=job1).write({"name": "Step 2"})
        
        # depends_on_id is an integer (ID), not a recordset in this ORM
        assert job2.depends_on_id == job1.id
        assert job1.state == "pending"
