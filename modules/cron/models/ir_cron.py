import time
import datetime
import traceback
from core.orm.base import BaseModel
from core.orm import fields

class IrCron(BaseModel):
    _name = "ir.cron"
    _description = "Scheduled Actions"

    name = fields.Char(string="Name")
    model_id = fields.Char(string="Model")
    code = fields.Text(string="Python Code")
    interval_number = fields.Integer(string="Interval Number", default=1)
    interval_type = fields.Selection([
        ("minutes", "Minutes"),
        ("hours", "Hours"),
        ("days", "Days")
    ], string="Interval Unit", default="minutes")
    nextcall = fields.Integer(string="Next Execution Date") # Timestamp
    numbercall = fields.Integer(string="Number of Calls", default=-1) # -1 for infinite
    priority = fields.Integer(string="Priority", default=5)
    active = fields.Boolean(string="Active", default=True)

    def process_all(self):
        """Process all due crons."""
        now = int(time.time())
        # Find due crons
        # Domain support is limited, so we search active ones and filter in python for now if needed.
        # Ideally: [('active', '=', True), ('nextcall', '<=', now)]
        # Assuming search works sequentially.
        
        # NOTE: Since search implementation in base.py is simple, we rely on it.
        # But wait, nextcall <= now might not be supported directly if search only does '='.
        # Let's read all active crons and filter.
        crons = self.search([("active", "=", True)])
        print(f"DEBUG: Found {len(crons)} active crons. Now={now}")
        for cron in crons:
            print(f"DEBUG: Checking cron {cron.name}, nextcall={cron.nextcall}")
            if cron.numbercall == 0:
                continue
            
            if cron.nextcall and cron.nextcall <= now:
                cron._process_cron_job()

    def _process_cron_job(self):
        """Execute a single cron job."""
        print(f"Executing Cron: {self.name}")
        
        try:
            # Prepare context
            env = self.env
            model = env[self.model_id] if self.model_id else None
            
            # Safe globals
            safe_globals = {
                "env": env,
                "model": model,
                "time": time,
                "datetime": datetime,
                "print": print,
                "re": None # Explicitly disable some imports if wanted, or just allow standard.
            }
            
            # Execute code
            exec(self.code, safe_globals)
            
        except Exception as e:
            print(f"Cron Execution Failed: {e}")
            traceback.print_exc()
        finally:
            self._update_nextcall()

    def _update_nextcall(self):
        """Calculate next call time."""
        if self.numbercall > 0:
            self.numbercall -= 1
            if self.numbercall == 0:
                self.active = False
        
        current_next = self.nextcall or int(time.time())
        # Add interval
        # Convert to datetime for easier math? Or just seconds.
        seconds_to_add = 0
        if self.interval_type == "minutes":
            seconds_to_add = self.interval_number * 60
        elif self.interval_type == "hours":
            seconds_to_add = self.interval_number * 3600
        elif self.interval_type == "days":
            seconds_to_add = self.interval_number * 86400
            
        new_next = current_next + seconds_to_add
        self.write({
            "nextcall": new_next,
            "numbercall": self.numbercall,
            "active": self.active
        })
