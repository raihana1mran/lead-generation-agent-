from database.database import SessionLocal
from database.models import Lead
from engine.events import trigger_lead_enrichment, trigger_proposal_generation
from engine.state_machine import WorkflowState
import sys

def main():
    db = SessionLocal()
    # Let's process the latest leads (e.g. ID 24 and 25, or any active lead)
    # We can process all leads that have not yet generated a personalized message
    leads = db.query(Lead).all()
    target_leads = []
    
    for l in leads:
        if not l.intelligence or not l.intelligence.personalized_message:
            target_leads.append(l)
            
    print(f"Found {len(target_leads)} leads needing email drafting.")
    db.close()
    
    for lead in target_leads[:3]: # Limit to first 3 to prevent rate limits
        print(f"\n==========================================")
        print(f"Drafting email for: {lead.company_name} (ID: {lead.id})")
        print(f"==========================================")
        
        # Reset state to INGESTED to start pipeline fresh
        db = SessionLocal()
        db_lead = db.query(Lead).filter(Lead.id == lead.id).first()
        db_lead.workflow_state = WorkflowState.INGESTED.value
        db_lead.requires_hitl = True
        db.commit()
        db.close()
        
        # 1. Run Enrichment & Scoring (will pause at DECISION)
        try:
            print("[Pipeline] Running Website Audit, AI Opportunity, Enrichment, and Scoring...")
            trigger_lead_enrichment(lead.id)
        except Exception as e:
            print(f"[Pipeline] Error during enrichment phase: {e}")
            continue
            
        # 2. Automatically approve DECISION to draft the proposal and personalized email
        print("[Pipeline] Ingestion and scoring complete. Simulating admin approval to draft proposal and email...")
        try:
            trigger_proposal_generation(lead.id, check_hitl=False)
            print(f"[Pipeline] Successfully drafted proposal and email for lead ID {lead.id}!")
        except Exception as e:
            print(f"[Pipeline] Error during drafting phase: {e}")
            
    print("\nDrafting job complete! View the Outreach tab in the UI to review the drafts.")

if __name__ == "__main__":
    main()
