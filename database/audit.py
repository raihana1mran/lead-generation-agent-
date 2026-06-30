from functools import wraps
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import AgentLog
import time

def log_agent_action(agent_name: str, action: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "failed"
                raise e
            finally:
                execution_time = int((time.time() - start_time) * 1000)
                
                # Attempt to extract lead_id from kwargs if it exists
                lead_id = str(kwargs.get("lead_id", ""))
                
                # Create DB session explicitly for logging
                db = SessionLocal()
                try:
                    log_entry = AgentLog(
                        agent_name=agent_name,
                        action=action,
                        lead_id=lead_id if lead_id else None,
                        status=status,
                        execution_time_ms=execution_time
                    )
                    db.add(log_entry)
                    db.commit()
                except Exception as e:
                    print(f"Failed to log audit event: {e}")
                finally:
                    db.close()
        return wrapper
    return decorator
