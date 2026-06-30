from database.database import SessionLocal
from database.models import Lead, LeadIntelligence
import json

def get_custom_agents(company_name):
    name_lower = company_name.lower()
    if any(w in name_lower for w in ["restaurant", "food", "cafe", "pizza", "kitchen", "grill", "diner", "bakery", "crumbl"]):
        return ["AI Reservation Bot", "Menu FAQ Agent", "Food Order Chatbot"]
    elif any(w in name_lower for w in ["real estate", "realty", "immobilien", "property", "housing", "estate", "homes", "landings"]):
        return ["Property Listing Bot", "Virtual Tour Booking Agent", "Mortgage Pre-qualification Agent"]
    elif any(w in name_lower for w in ["medical", "clinic", "health", "doctor", "dental", "plastic", "hospital"]):
        return ["Patient Appointment Scheduler", "Medical FAQ Bot", "Insurance Verification Agent"]
    elif any(w in name_lower for w in ["barber", "salon", "beauty", "hair", "spa", "nail", "flower"]):
        return ["Appointment Booking Bot", "Service Recommendation Agent", "Review Follow-up Agent"]
    elif any(w in name_lower for w in ["shop", "store", "retail", "ecommerce", "mart", "boutique", "supermarket", "webstore"]):
        return ["Product Recommendation Engine", "Cart Abandonment Recovery Agent", "Returns Processing Bot"]
    elif any(w in name_lower for w in ["law", "legal", "attorney", "solicitor"]):
        return ["Case Intake Automation Bot", "Document Summarization Agent", "Client Onboarding Agent"]
    elif any(w in name_lower for w in ["gym", "fitness", "yoga", "training", "crossfit"]):
        return ["Class Booking Bot", "Personal Training Scheduler", "Member Retention Agent"]
    elif any(w in name_lower for w in ["hotel", "resort", "inn", "hostel"]):
        return ["Concierge AI Bot", "Room Booking Agent", "Guest Feedback Bot"]
    elif any(w in name_lower for w in ["web", "design", "digital", "agency", "marketing", "seo", "creative", "squads"]):
        return ["Campaign Performance Bot", "Lead Nurturing Agent", "Content Repurposing Agent"]
    elif any(w in name_lower for w in ["auto", "car", "motor", "vehicle", "driver"]):
        return ["Service Appointment Agent", "Parts Availability Bot", "Test Drive Booking Agent"]
    elif any(w in name_lower for w in ["school", "education", "university", "academy", "tutor"]):
        return ["Course Enrollment Bot", "Student Progress Tracker", "Tutor Matching Agent"]
    elif any(w in name_lower for w in ["finance", "bank", "account", "insurance", "tax"]):
        return ["Invoice Processing Agent", "Expense Report Automation", "Financial FAQ Bot"]
    elif any(w in name_lower for w in ["storage", "warehouse", "logistics", "moving"]):
        return ["Inventory Tracking Bot", "Space Availability Agent", "Customer Booking Agent"]
    elif any(w in name_lower for w in ["glass", "construction", "build", "plumb", "electric"]):
        return ["Project Estimation Bot", "Supplier Quote Agent", "Safety Compliance Tracker"]
    elif any(w in name_lower for w in ["art", "gallery", "museum", "exchange"]):
        return ["Exhibition Booking Bot", "Visitor Guide Agent", "Event Registration Agent"]
    else:
        return [f"Customer Inquiry Bot for {company_name}", f"Booking Automation Agent for {company_name}", f"Lead Follow-up Agent for {company_name}"]

def main():
    db = SessionLocal()
    try:
        leads = db.query(Lead).all()
        updated_count = 0
        for lead in leads:
            if lead.intelligence:
                # Get tailored agents based on company name
                tailored_agents = get_custom_agents(lead.company_name)
                
                # Load current ai_opportunities JSON
                current_opps = lead.intelligence.ai_opportunities or {}
                if isinstance(current_opps, str):
                    try:
                        current_opps = json.loads(current_opps)
                    except Exception:
                        current_opps = {}
                
                # Update the recommended_agents
                current_opps["recommended_agents"] = tailored_agents
                
                # Also set realistic ROI estimation and complexity if they are default/empty
                if not current_opps.get("roi_estimation") or current_opps.get("roi_estimation") == "Not analyzed":
                    current_opps["roi_estimation"] = "Expected 20-35% efficiency gain in 30 days"
                if not current_opps.get("implementation_complexity") or current_opps.get("implementation_complexity") == "Not analyzed":
                    current_opps["implementation_complexity"] = "Medium (3-5 days integration)"
                
                lead.intelligence.ai_opportunities = current_opps
                updated_count += 1
        
        db.commit()
        print(f"Successfully updated AI agent suggestions for {updated_count} leads in the database!")
    except Exception as e:
        print(f"Error updating database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
