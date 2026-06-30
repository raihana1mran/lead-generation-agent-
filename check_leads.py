from database.database import SessionLocal
from database.models import Lead

db = SessionLocal()
leads = db.query(Lead).all()
print(f"Total leads: {len(leads)}")
for l in leads:
    print(f"ID: {l.id} | Name: {l.company_name} | State: {l.workflow_state} | Requires HITL: {l.requires_hitl}")
db.close()
