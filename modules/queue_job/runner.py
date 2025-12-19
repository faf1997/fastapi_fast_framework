import time
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.database import Database
from core.orm.registry import Registry
from core.module_loader import ModuleLoader

def run_worker():
    print("Starting Queue Job Worker...")
    
    # Initialize Core
    db = Database()
    ModuleLoader.load_modules()
    
    env = Registry.get("queue.job").env  # Get an env from a model
    QueueJob = env["queue.job"]
    
    print("Worker initialized. Polling for jobs...")
    
    while True:
        try:
            # 1. Find pending jobs with ETA passed
            now = int(time.time())
            
            # We need a domain to filter. 
            # ORM search is basic, so we might need to filter manually or improve search if needed.
            # Assuming search supports basic operators.
            
            # Find all pending jobs first (add limit to avoid overload)
            jobs = QueueJob.search([("state", "=", "pending")], limit=50)
            
            for job in jobs:
                # Check ETA
                if job.eta and job.eta > now:
                    continue
                
                # Check Dependency
                if job.depends_on_id:
                    # If dependency is not done, skip
                    if job.depends_on_id.state != "done":
                        # If dependency failed, maybe fail this one too? 
                        # For now just wait.
                        if job.depends_on_id.state == "failed":
                             job.write({"state": "failed", "error": "Dependency failed"})
                        continue
                
                # Run Job
                print(f"Processing Job {job.uuid} ({job.model_name}.{job.method_name})")
                success = job.run_job()
                if success:
                    print(f"Job {job.uuid} DONE")
                else:
                    print(f"Job {job.uuid} FAILED")
                    
            time.sleep(2) # Poll interval
            
        except KeyboardInterrupt:
            print("Stopping worker...")
            break
        except Exception as e:
            print(f"Worker Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_worker()
