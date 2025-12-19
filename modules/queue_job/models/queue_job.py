import json
import uuid
import time
import traceback
from core.orm.base import BaseModel
from core.orm import fields

class QueueJob(BaseModel):
    _name = "queue.job"
    _description = "Queue Job"

    uuid = fields.Char(string="UUID")
    model_name = fields.Char(string="Model Name")
    method_name = fields.Char(string="Method Name")
    record_ids = fields.Text(string="Record IDs")  # JSON list of IDs
    args = fields.Text(string="Args")  # JSON list
    kwargs = fields.Text(string="Kwargs")  # JSON dict
    eta = fields.Integer(string="ETA")  # Timestamp
    depends_on_id = fields.Many2one("queue.job", string="Dependency")
    state = fields.Selection([
        ("pending", "Pending"),
        ("started", "Started"),
        ("done", "Done"),
        ("failed", "Failed")
    ], string="State", default="pending")
    result = fields.Text(string="Result")
    error = fields.Text(string="Error")

    def run_job(self):
        """Execute the job."""
        self.state = "started"
        self.write({"state": "started"})
        
        try:
            # Reconstruct context and model
            model_cls = self.env[self.model_name]
            ids = json.loads(self.record_ids)
            records = model_cls.browse(ids)
            
            # Prepare args/kwargs
            args = json.loads(self.args) if self.args else []
            kwargs = json.loads(self.kwargs) if self.kwargs else {}
            
            # execute
            method = getattr(records, self.method_name)
            res = method(*args, **kwargs)
            
            self.write({
                "state": "done",
                "result": str(res)
            })
            return True
        except Exception as e:
            tb = traceback.format_exc()
            self.write({
                "state": "failed",
                "error": tb
            })
            return False

class JobProxy:
    def __init__(self, record, eta=None, job_id=None):
        self.record = record
        self.eta = eta
        self.job_id = job_id

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            return self._create_job(name, args, kwargs)
        return wrapper

    def _create_job(self, method_name, args, kwargs):
        env = self.record.env
        QueueJobModel = env["queue.job"]
        
        # Calculate ETA
        eta_ts = int(time.time())
        if self.eta:
            eta_ts += self.eta
            
        vals = {
            "uuid": str(uuid.uuid4()),
            "model_name": self.record._name,
            "method_name": method_name,
            "record_ids": json.dumps(self.record.ids),
            "args": json.dumps(args),
            "kwargs": json.dumps(kwargs),
            "eta": eta_ts,
            "state": "pending"
        }
        
        if self.job_id:
            # If job_id is an integer, assume it's the ID. If it's a record, get ID.
            dep_id = self.job_id.id if hasattr(self.job_id, 'id') else self.job_id
            vals["depends_on_id"] = dep_id
            
        job = QueueJobModel.create(vals)
        return job

# Monkey Patch BaseModel
def with_delay(self, eta=None, job_id=None):
    return JobProxy(self, eta=eta, job_id=job_id)

BaseModel.with_delay = with_delay
