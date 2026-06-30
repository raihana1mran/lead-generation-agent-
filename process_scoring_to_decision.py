from database.database import SessionLocal
from database.models import Lead
from engine.events import trigger_lead_decision

db = SessionLocal()
try:
    # Find all leads in SCORING state that have been scored
    leads = db.query(Lead).filter(Lead.workflow_state == "SCORING").all()
    print(f"Found {len(leads)} leads in SCORING state.")
    for lead in leads:
        if lead.intelligence and lead.intelligence.lead_score is not None:
            print(f"Processing decision for lead: {lead.company_name} (ID: {lead.id}, Score: {lead.intelligence.lead_score})")
            # This will transition the lead to DECISION and then attempt to transition to PROPOSAL (which will pause if requires_hitl=True)
            trigger_lead_decision(lead.id)
finally:
    db.close()
print("Done processing decision pipeline transitions!")
