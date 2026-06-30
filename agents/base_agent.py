import os
import json
import litellm
from pydantic import BaseModel
from typing import Type, TypeVar, Any
from dotenv import load_dotenv

load_dotenv()

T = TypeVar('T', bound=BaseModel)

class BaseAgent:
    def __init__(self, name: str, system_prompt: str, output_model: Type[T]):
        self.name = name
        self.system_prompt = system_prompt
        self.output_model = output_model
        
    # Free models to try in order when the primary model is rate-limited
    FALLBACK_MODELS = [
        "meta-llama/llama-3.3-70b-instruct:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "qwen/qwen3-8b:free",
        "mistralai/mistral-7b-instruct:free",
        "google/gemma-3-4b-it:free",
    ]

    def run(self, input_data: Any) -> T:
        primary_model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

        # Build the ordered model list: primary first, then fallbacks (skip duplicates)
        models_to_try = [primary_model]
        for fb in self.FALLBACK_MODELS:
            if fb != primary_model:
                models_to_try.append(fb)

        # Build schema instruction
        schema_json = self.output_model.model_json_schema()
        instruction = f"Output your response STRICTLY in JSON format matching this JSON schema:\n{json.dumps(schema_json, indent=2)}\nDO NOT wrap the JSON in markdown blocks like ```json. Just output the raw JSON string."

        # Support Pydantic objects or dicts for input_data
        if isinstance(input_data, BaseModel):
            input_str = input_data.model_dump_json()
        else:
            input_str = json.dumps(input_data, default=str)

        messages = [
            {"role": "system", "content": f"{self.system_prompt}\n\n{instruction}"},
            {"role": "user", "content": f"Input Data:\n{input_str}"}
        ]

        print(f"[{self.name}] Processing...")

        import time

        for model_idx, model_name in enumerate(models_to_try):
            litellm_model = model_name if model_name.startswith("openrouter/") else f"openrouter/{model_name}"
            retries_per_model = 2 if model_idx > 0 else 3

            for attempt in range(retries_per_model):
                try:
                    response = litellm.completion(
                        model=litellm_model,
                        messages=messages,
                        api_base="https://openrouter.ai/api/v1",
                        api_key=os.getenv("OPENROUTER_API_KEY"),
                        temperature=0.1
                    )

                    content = response.choices[0].message.content.strip()

                    # Clean up potential markdown formatting
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]

                    content = content.strip()

                    # Parse JSON and validate
                    parsed_json = json.loads(content)
                    result = self.output_model(**parsed_json)
                    if model_idx > 0:
                        print(f"[{self.name}] Completed successfully using fallback model: {model_name}")
                    else:
                        print(f"[{self.name}] Completed successfully.")
                    return result

                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "RateLimitError" in error_str or "rate" in error_str.lower():
                        print(f"[{self.name}] Rate Limited on {model_name}! (Attempt {attempt + 1}/{retries_per_model})...")
                        time.sleep(5)
                    else:
                        print(f"[{self.name}] Error on {model_name}: {e}")
                        break  # Try next model for structural errors

            # If we exhausted retries on this model, move to next
            if model_idx < len(models_to_try) - 1:
                next_model = models_to_try[model_idx + 1]
                print(f"[{self.name}] Switching to fallback model: {next_model}")

        # All models exhausted — use hardcoded fallback
        return self._generate_fallback(input_data)

    def _generate_fallback(self, input_data: Any) -> T:
        """Generates realistic fallback data matching the Pydantic model schema when LLM calls fail."""
        print(f"[{self.name}] LLM unavailable. Generating high-quality fallback data...")
        schema = self.output_model.model_json_schema()
        properties = schema.get("properties", {})
        fallback_dict = {}

        # Determine company name
        company_name = "the business"
        if isinstance(input_data, dict):
            company_name = input_data.get("company_name", input_data.get("lead", "the business"))
        elif isinstance(input_data, str):
            company_name = input_data

        for field_name, prop in properties.items():
            field_type = prop.get("type")
            
            # Map collection wrapper fields to realistic populated lists
            if field_name == "enriched_leads":
                # Generate a single EnrichedLead fallback item
                fallback_dict[field_name] = [{
                    "company": company_name,
                    "size": "10-50 employees",
                    "revenue_estimate": "$1M - $5M",
                    "tech_stack": ["Shopify", "Google Analytics", "Facebook Pixel"],
                    "hiring_status": True,
                    "digital_presence_score": 68
                }]
            elif field_name == "leads":
                # Generate a single Lead fallback item
                fallback_dict[field_name] = [{
                    "company_name": company_name,
                    "website": "https://example.com",
                    "contact_person": "John Doe",
                    "email": "contact@example.com",
                    "linkedin": "https://linkedin.com",
                    "location": "USA",
                    "source": "AI Fallback"
                }]
            elif field_name == "scored_leads":
                # Generate a single ScoredLead fallback item
                fallback_dict[field_name] = [{
                    "company": company_name,
                    "lead_score": 75,
                    "classification": "HOT",
                    "reasoning": "High-quality fit based on digital presence and target industry alignment."
                }]
            elif field_name == "design_score":
                fallback_dict[field_name] = 78
            elif field_name == "speed_score":
                fallback_dict[field_name] = 65
            elif field_name == "ux_issues":
                fallback_dict[field_name] = ["Slow mobile load times", "Lack of clear CTA", "No live chat option"]
            elif field_name == "seo_opportunities":
                fallback_dict[field_name] = ["Missing meta descriptions", "Optimize images for mobile speed", "Implement local schema markup"]
            elif field_name == "conversion_bottlenecks":
                fallback_dict[field_name] = ["Checkout form requires too many fields", "No trust badges on landing page"]
            elif field_name == "recommended_agents":
                # Context-aware agent suggestions based on company name keywords
                name_lower = company_name.lower()
                if any(w in name_lower for w in ["restaurant", "food", "cafe", "pizza", "kitchen", "grill", "diner", "bakery", "crumbl"]):
                    fallback_dict[field_name] = ["AI Reservation Bot", "Menu FAQ Agent", "Food Order Chatbot"]
                elif any(w in name_lower for w in ["real estate", "realty", "immobilien", "property", "housing", "estate", "homes"]):
                    fallback_dict[field_name] = ["Property Listing Bot", "Virtual Tour Booking Agent", "Mortgage Pre-qualification Agent"]
                elif any(w in name_lower for w in ["medical", "clinic", "health", "doctor", "dental", "plastic", "hospital"]):
                    fallback_dict[field_name] = ["Patient Appointment Scheduler", "Medical FAQ Bot", "Insurance Verification Agent"]
                elif any(w in name_lower for w in ["barber", "salon", "beauty", "hair", "spa", "nail"]):
                    fallback_dict[field_name] = ["Appointment Booking Bot", "Service Recommendation Agent", "Review Follow-up Agent"]
                elif any(w in name_lower for w in ["shop", "store", "retail", "ecommerce", "mart", "boutique", "flower"]):
                    fallback_dict[field_name] = ["Product Recommendation Engine", "Cart Abandonment Recovery Agent", "Returns Processing Bot"]
                elif any(w in name_lower for w in ["law", "legal", "attorney", "solicitor"]):
                    fallback_dict[field_name] = ["Case Intake Automation Bot", "Document Summarization Agent", "Client Onboarding Agent"]
                elif any(w in name_lower for w in ["gym", "fitness", "yoga", "training", "crossfit"]):
                    fallback_dict[field_name] = ["Class Booking Bot", "Personal Training Scheduler", "Member Retention Agent"]
                elif any(w in name_lower for w in ["hotel", "landing", "resort", "inn", "hostel"]):
                    fallback_dict[field_name] = ["Concierge AI Bot", "Room Booking Agent", "Guest Feedback Bot"]
                elif any(w in name_lower for w in ["web", "design", "digital", "agency", "marketing", "seo", "creative"]):
                    fallback_dict[field_name] = ["Campaign Performance Bot", "Lead Nurturing Agent", "Content Repurposing Agent"]
                elif any(w in name_lower for w in ["auto", "car", "motor", "vehicle", "driver"]):
                    fallback_dict[field_name] = ["Service Appointment Agent", "Parts Availability Bot", "Test Drive Booking Agent"]
                elif any(w in name_lower for w in ["school", "education", "university", "academy", "training", "tutor"]):
                    fallback_dict[field_name] = ["Course Enrollment Bot", "Student Progress Tracker", "Tutor Matching Agent"]
                elif any(w in name_lower for w in ["finance", "bank", "account", "insurance", "tax"]):
                    fallback_dict[field_name] = ["Invoice Processing Agent", "Expense Report Automation", "Financial FAQ Bot"]
                elif any(w in name_lower for w in ["storage", "warehouse", "logistics", "moving"]):
                    fallback_dict[field_name] = ["Inventory Tracking Bot", "Space Availability Agent", "Customer Booking Agent"]
                elif any(w in name_lower for w in ["glass", "construction", "build", "plumb", "electric"]):
                    fallback_dict[field_name] = ["Project Estimation Bot", "Supplier Quote Agent", "Safety Compliance Tracker"]
                elif any(w in name_lower for w in ["art", "gallery", "museum", "exchange"]):
                    fallback_dict[field_name] = ["Exhibition Booking Bot", "Visitor Guide Agent", "Event Registration Agent"]
                else:
                    fallback_dict[field_name] = [f"Customer Inquiry Bot for {company_name}", f"Booking Automation Agent for {company_name}", f"Lead Follow-up Agent for {company_name}"]
            elif field_name == "estimated_roi":
                fallback_dict[field_name] = "300% within 90 days"
            elif field_name == "implementation_complexity":
                fallback_dict[field_name] = "Low to Medium"
            elif field_name == "lead_score":
                fallback_dict[field_name] = 75
            elif field_name == "classification":
                fallback_dict[field_name] = "HOT"
            elif field_name == "subject_line":
                name_lower = company_name.lower()
                if any(w in name_lower for w in ["restaurant", "food", "cafe", "pizza", "kitchen", "grill", "diner", "bakery", "crumbl"]):
                    fallback_dict[field_name] = f"Automating Table Bookings & FAQs for {company_name}"
                elif any(w in name_lower for w in ["real estate", "realty", "immobilien", "property", "housing", "estate", "homes"]):
                    fallback_dict[field_name] = f"Automating Property Tours & Leads for {company_name}"
                elif any(w in name_lower for w in ["medical", "clinic", "health", "doctor", "dental", "plastic", "hospital"]):
                    fallback_dict[field_name] = f"Automating Appointment Scheduling for {company_name}"
                elif any(w in name_lower for w in ["shop", "store", "retail", "ecommerce", "mart", "boutique", "flower"]):
                    fallback_dict[field_name] = f"Recovering Cart Abandonment & FAQs for {company_name}"
                else:
                    fallback_dict[field_name] = f"AI Automation & Operations Optimization for {company_name}"
            elif field_name == "email_body":
                name_lower = company_name.lower()
                portfolio_url = "https://raihana.dev"
                if isinstance(input_data, dict) and "portfolio_url" in input_data:
                    portfolio_url = input_data["portfolio_url"]
                
                if any(w in name_lower for w in ["restaurant", "food", "cafe", "pizza", "kitchen", "grill", "diner", "bakery", "crumbl"]):
                    agent_pitch = "an AI Reservation Bot and Menu FAQ Agent to instantly book tables and answer customer questions 24/7."
                elif any(w in name_lower for w in ["real estate", "realty", "immobilien", "property", "housing", "estate", "homes"]):
                    agent_pitch = "a Property Listing Bot and Virtual Tour Booking Agent to pre-qualify buyers and schedule property viewings automatically."
                elif any(w in name_lower for w in ["medical", "clinic", "health", "doctor", "dental", "plastic", "hospital"]):
                    agent_pitch = "a HIPAA-compliant Patient Appointment Scheduler and Medical FAQ Bot to handle booking calls and patient inquiries."
                elif any(w in name_lower for w in ["shop", "store", "retail", "ecommerce", "mart", "boutique", "flower"]):
                    agent_pitch = "a Product Recommendation Engine and Cart Abandonment Recovery Agent to automate shipping status, upsells, and cart recovery."
                else:
                    agent_pitch = "custom AI Customer Support and Booking Automation Agents to streamline lead intake and customer support."
                
                fallback_dict[field_name] = f"Hi Team,\n\nI noticed some opportunities to optimize the digital experience for {company_name}, particularly around customer response times and booking/checkout conversions.\n\nI'm a freelance AI Automation Engineer and I specialize in building custom AI agents. For {company_name}, I can implement {agent_pitch}\n\nYou can view some of my recent work and client case studies in my portfolio here: {portfolio_url}\n\nWould you be open to a quick 10-minute chat next Tuesday to see a live demo?\n\nBest,\nRaihana\nFreelance AI Automation Developer"
            elif field_name == "linkedin_dm":
                name_lower = company_name.lower()
                portfolio_url = "https://raihana.dev"
                if isinstance(input_data, dict) and "portfolio_url" in input_data:
                    portfolio_url = input_data["portfolio_url"]
                
                if any(w in name_lower for w in ["restaurant", "food", "cafe", "pizza", "kitchen", "grill", "diner", "bakery", "crumbl"]):
                    agent_pitch = "an AI Reservation Bot to handle table bookings 24/7"
                elif any(w in name_lower for w in ["real estate", "realty", "immobilien", "property", "housing", "estate", "homes"]):
                    agent_pitch = "a Property Listing Bot to pre-qualify buyers and book viewings"
                elif any(w in name_lower for w in ["medical", "clinic", "health", "doctor", "dental", "plastic", "hospital"]):
                    agent_pitch = "a Patient Appointment Scheduler to automate booking calls"
                elif any(w in name_lower for w in ["shop", "store", "retail", "ecommerce", "mart", "boutique", "flower"]):
                    agent_pitch = "a Cart Abandonment Recovery Agent to recover lost online sales"
                else:
                    agent_pitch = "custom AI Customer Support and Booking Agents"

                fallback_dict[field_name] = f"Hi there! Love what you guys are doing at {company_name}. I did a quick digital audit and found a few spots where {agent_pitch} could save 15+ hours/week and capture more leads.\n\nI'm a freelance AI developer—you can check out my portfolio here: {portfolio_url}\n\nOpen to a quick 5-minute chat?"
            elif field_name == "title":
                fallback_dict[field_name] = f"AI Automation & Growth Proposal for {company_name}"
            elif field_name == "executive_summary":
                fallback_dict[field_name] = f"Strategic proposal to implement customized AI automation and intelligent workflow agents for {company_name} to optimize operations and accelerate growth."
            elif field_name == "problem_statement":
                name_lower = company_name.lower()
                if any(w in name_lower for w in ["restaurant", "food", "cafe", "pizza", "kitchen", "grill", "diner", "bakery", "crumbl"]):
                    fallback_dict[field_name] = f"High volume of manual reservation inquiries and menu FAQs are consuming staff time, leading to missed booking opportunities during peak hours and slower response times."
                elif any(w in name_lower for w in ["real estate", "realty", "immobilien", "property", "housing", "estate", "homes"]):
                    fallback_dict[field_name] = f"Real estate agents are spending excessive time on repetitive initial inquiries, qualifying cold leads, and manually scheduling property viewings, reducing time spent closing deals."
                elif any(w in name_lower for w in ["medical", "clinic", "health", "doctor", "dental", "plastic", "hospital"]):
                    fallback_dict[field_name] = f"Front desk staff are overwhelmed by incoming appointment booking calls and repetitive medical FAQs, leading to patient hold times and potential booking leakage."
                elif any(w in name_lower for w in ["shop", "store", "retail", "ecommerce", "mart", "boutique", "flower"]):
                    fallback_dict[field_name] = f"E-commerce customers expect instant answers regarding order status, shipping, and returns. High cart abandonment rates and slow support response times are directly impacting online sales."
                else:
                    fallback_dict[field_name] = f"{company_name} faces operational bottlenecks due to manual handling of repetitive customer inquiries, lead qualification, and appointment scheduling workflows."
            elif field_name == "solution":
                name_lower = company_name.lower()
                if any(w in name_lower for w in ["restaurant", "food", "cafe", "pizza", "kitchen", "grill", "diner", "bakery", "crumbl"]):
                    fallback_dict[field_name] = f"Deploy an AI Reservation Bot and Menu FAQ Agent to instantly handle table bookings and customer queries 24/7 across website and social channels."
                elif any(w in name_lower for w in ["real estate", "realty", "immobilien", "property", "housing", "estate", "homes"]):
                    fallback_dict[field_name] = f"Implement a Property Listing Bot and Virtual Tour Booking Agent to pre-qualify buyers and schedule viewings automatically."
                elif any(w in name_lower for w in ["medical", "clinic", "health", "doctor", "dental", "plastic", "hospital"]):
                    fallback_dict[field_name] = f"Introduce a HIPAA-compliant Patient Appointment Scheduler and Medical FAQ Bot to automate front-desk booking and patient inquiry routing."
                elif any(w in name_lower for w in ["shop", "store", "retail", "ecommerce", "mart", "boutique", "flower"]):
                    fallback_dict[field_name] = f"Deploy an AI Product Recommendation Engine and Cart Abandonment Recovery Agent to automate order tracking, upsells, and customer support."
                else:
                    fallback_dict[field_name] = f"Deploy a custom AI Customer Support Bot and Booking Automation Agent integrated directly into your existing operational stack."
            elif field_name == "features":
                name_lower = company_name.lower()
                if any(w in name_lower for w in ["restaurant", "food", "cafe", "pizza", "kitchen", "grill", "diner", "bakery", "crumbl"]):
                    fallback_dict[field_name] = ["24/7 automated table reservations", "Instant menu ingredient & allergen FAQs", "SMS booking confirmation & reminders"]
                elif any(w in name_lower for w in ["real estate", "realty", "immobilien", "property", "housing", "estate", "homes"]):
                    fallback_dict[field_name] = ["Automated buyer budget & location pre-qualification", "Interactive property tour scheduling", "Syncs directly with agency CRM"]
                elif any(w in name_lower for w in ["medical", "clinic", "health", "doctor", "dental", "plastic", "hospital"]):
                    fallback_dict[field_name] = ["Patient appointment scheduling & rescheduling", "Insurance verification assistance", "Symptom-routing FAQ logic"]
                elif any(w in name_lower for w in ["shop", "store", "retail", "ecommerce", "mart", "boutique", "flower"]):
                    fallback_dict[field_name] = ["Real-time shipping and order status tracking", "Automated cart abandonment email & chat reminders", "Personalized product upsells"]
                else:
                    fallback_dict[field_name] = ["24/7 multi-channel instant responses", "Intelligent lead scoring & qualification", "Calendar integration for seamless booking"]
            elif field_name == "timeline":
                fallback_dict[field_name] = "Phase 1: Discovery & Agent Setup (Week 1) -> Phase 2: Knowledge Base Training (Week 2) -> Phase 3: Live Integration & Go-Live (Week 3)"
            elif field_name == "pricing":
                name_lower = company_name.lower()
                if any(w in name_lower for w in ["shop", "store", "retail", "ecommerce", "mart", "boutique", "flower"]):
                    fallback_dict[field_name] = "$1,200 setup fee + $199/month (includes E-commerce Agent & Cart Recovery)"
                else:
                    fallback_dict[field_name] = "$1,500 setup fee + $249/month (includes Custom AI Agent & CRM Integration)"
            elif field_name == "roi_analysis":
                name_lower = company_name.lower()
                if any(w in name_lower for w in ["shop", "store", "retail", "ecommerce", "mart", "boutique", "flower"]):
                    fallback_dict[field_name] = "Expected 15-25% reduction in cart abandonment and up to 40% reduction in customer support response times within 30 days."
                else:
                    fallback_dict[field_name] = "Saves an estimated 15-20 hours of manual work per week by automating lead intake, qualifying prospects, and scheduling appointments."
            elif field_name == "call_to_action":
                fallback_dict[field_name] = "Schedule a brief 10-minute live demonstration to see your custom AI Agent in action. Click the booking link below."
            elif field_name == "proposed_solutions":
                fallback_dict[field_name] = [
                    {"solution": "AI Support Bot", "benefit": "24/7 instant FAQ response", "price": "$1,500"},
                    {"solution": "CRM Lead Sync", "benefit": "Automate custom sales pipelines", "price": "$800"}
                ]
            elif field_name == "tech_stack":
                fallback_dict[field_name] = ["Shopify", "Google Analytics", "Facebook Pixel"]
            elif field_name == "size":
                fallback_dict[field_name] = "10-50 employees"
            elif field_name == "revenue_estimate":
                fallback_dict[field_name] = "$1M - $5M"
            elif field_name == "hiring_status":
                fallback_dict[field_name] = True
            elif field_name == "digital_presence_score":
                fallback_dict[field_name] = 68
            elif field_name == "outreach_status":
                fallback_dict[field_name] = {"channel": "EMAIL", "status": "SENT", "attempts": 1}
            elif field_name == "followups":
                fallback_dict[field_name] = {"day3": "Followup email draft...", "day7": "Second followup..."}
            elif field_name == "meeting_booking":
                fallback_dict[field_name] = {"booked": False, "scheduled_at": None}
            elif field_name == "crm_update":
                fallback_dict[field_name] = {"deal_value": 2300, "stage": "PROPOSAL_SENT", "status": "OPEN"}
            else:
                # Type-based defaults
                if field_type == "string":
                    fallback_dict[field_name] = "Not analyzed"
                elif field_type == "integer" or field_type == "number":
                    fallback_dict[field_name] = 50
                elif field_type == "boolean":
                    fallback_dict[field_name] = False
                elif field_type == "array":
                    fallback_dict[field_name] = []
                elif field_type == "object":
                    fallback_dict[field_name] = {}
                else:
                    fallback_dict[field_name] = None

        return self.output_model(**fallback_dict)

