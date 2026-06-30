from database.database import SessionLocal
from database.models import Lead, BusinessProfile
from agents.all_agents import PersonalizationAgent
import sys

def main():
    db = SessionLocal()
    try:
        # Get business profile for the portfolio URL
        profile = db.query(BusinessProfile).first()
        portfolio_url = profile.website if (profile and profile.website) else "https://raihana.dev"
        
        # Instantiate personalization agent
        agent_personalize = PersonalizationAgent()
        
        # Get all leads with intelligence
        leads = db.query(Lead).all()
        target_leads = [l for l in leads if l.intelligence]
        
        print(f"Found {len(target_leads)} leads eligible for pitch regeneration.")
        
        regenerated_count = 0
        for lead in target_leads:
            print(f"\nRegenerating pitch for: {lead.company_name} (ID: {lead.id})")
            
            personalization_data = {
                "company_name": lead.company_name,
                "website_audit": lead.intelligence.website_audit or {},
                "ai_opportunities": lead.intelligence.ai_opportunities or {},
                "freelancer_name": "Raihana",
                "portfolio_url": portfolio_url
            }
            
            try:
                # Run the personalization agent (with automatic multi-model fallback chain)
                result = agent_personalize.run(personalization_data)
                
                lead.intelligence.personalized_message = result.model_dump()
                db.commit()
                print(f"Successfully updated pitch for {lead.company_name}!")
                regenerated_count += 1
            except Exception as e:
                print(f"Error regenerating pitch for {lead.company_name}: {e}")
                
        print(f"\nDone! Regenerated pitches for {regenerated_count} leads.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
