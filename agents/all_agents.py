from .base_agent import BaseAgent
from database.models import BusinessProfile
from models.shared import (
    BusinessContext, MarketIntelligence, Lead, EnrichedLead,
    ScoredLead, Proposal, OutreachStatus, Followup, Analytics,
    WebsiteAudit, AIOpportunity, PersonalizedMessage, MeetingBooking, 
    CRMUpdate, LeadsOutput, EnrichedLeadsOutput, ScoredLeadsOutput
)
from pydantic import BaseModel
from typing import List
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
import json

# Output Wrappers for Agents returning lists
class LeadsOutput(BaseModel):
    leads: List[Lead]

class EnrichedLeadsOutput(BaseModel):
    enriched_leads: List[EnrichedLead]

class ScoredLeadsOutput(BaseModel):
    scored_leads: List[ScoredLead]

class OutreachOutput(BaseModel):
    outreach_status: List[OutreachStatus]

class FollowupOutput(BaseModel):
    followups: List[Followup]

class BusinessUnderstandingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Business Understanding Agent",
            system_prompt="""You are the Business Understanding Agent. Your purpose is to understand the client business deeply.
Never assume the business model. Always extract the Ideal Customer Profile (ICP) clearly. Focus on buying triggers (VERY IMPORTANT).""",
            output_model=BusinessContext
        )

class MarketIntelligenceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Market Intelligence Agent",
            system_prompt="""You are the Market Intelligence Agent. Your purpose is to analyze market demand and competitor landscape.
Identify top competitors, detect market demand signals, find high-conversion industries, and suggest best regions.""",
            output_model=MarketIntelligence
        )

class LeadDiscoveryAgent:
    """
    Scrapes leads from DuckDuckGo search results directly — NO LLM needed.
    Extracts company name, website, source platform from search snippets.
    Supports: LinkedIn, Instagram, TikTok, Quora, Pinterest, Google.
    """

    PLATFORM_MAP = {
        "linkedin.com":  "LinkedIn",
        "instagram.com": "Instagram",
        "tiktok.com":    "TikTok",
        "quora.com":     "Quora",
        "pinterest.com": "Pinterest",
        "google.com/maps": "Google Maps",
        "google.co.uk/maps": "Google Maps",
        "google.ca/maps": "Google Maps",
    }

    TIER_COUNTRIES = {
        "tier1": ["USA", "UK", "Canada", "Australia", "Germany"],
        "tier2": ["India", "UAE", "Singapore", "Brazil", "Netherlands", "France"],
        "tier3": ["Philippines", "Nigeria", "Kenya", "Pakistan", "South Africa"],
    }

    def _detect_source(self, url: str) -> str:
        if "/maps" in url or "google.com/maps" in url:
            return "Google Maps"
        for domain, name in self.PLATFORM_MAP.items():
            if domain in url:
                return name
        return "Google"

    def _extract_company_name(self, title: str, url: str, source: str) -> str:
        import re
        # Direct Shopify storefront domain name parsing
        if "myshopify.com" in url:
            try:
                domain_part = url.split("myshopify.com")[0].replace("https://", "").replace("http://", "").replace("www.", "").strip("/.")
                if domain_part:
                    return " ".join([w.capitalize() for w in domain_part.split("-") if w])
            except Exception:
                pass

        # LinkedIn: "Company Name | LinkedIn" or "Company Name - LinkedIn"
        if source == "LinkedIn":
            name = re.split(r"[|\-–]", title)[0].strip()
            return name if len(name) > 2 else title
        # Instagram: "Company Name (@handle) • Instagram"
        if source == "Instagram":
            m = re.match(r"^(.+?)\s*(?:\(@|\.)", title)
            return m.group(1).strip() if m else title.split("•")[0].strip()
        # TikTok: "Company (@handle) | TikTok"
        if source == "TikTok":
            return title.split("(@")[0].strip() or title.split("|")[0].strip()
        # Pinterest: "Company on Pinterest"
        if source == "Pinterest":
            return title.replace(" on Pinterest", "").replace(" | Pinterest", "").strip()
        # Quora: extract from title
        if source == "Quora":
            return re.split(r"[|:]", title)[0].strip()
        # Generic fallback: take first meaningful part of title
        return re.split(r"[|\-–]", title)[0].strip() or title

    def _extract_website(self, url: str, source: str) -> str:
        """Try to infer the company website from search snippet URL."""
        if source == "Google":
            return url
        # For social platforms, the URL IS the profile
        return url.split("?")[0]  # strip query params

    def _build_queries(self, query_str: str, countries: list, platforms: list) -> list:
        """Build platform x country search queries specifically designed to find real product-selling businesses."""
        platform_sites = {
            "linkedin":  "site:linkedin.com/company",
            "instagram": "site:instagram.com",
            "tiktok":    "site:tiktok.com",
            "quora":     "site:quora.com",
            "pinterest": "site:pinterest.com",
            "googlemaps": "site:google.com/maps/place",
        }
        import re
        
        # Clean user query and strip map-specific requests
        clean = re.sub(
            r"(get leads who|automatically generate leads|leads from|leads who|without website|without a website|without online|businesses who|businesses that|scrape from|from google maps|google maps|googlemaps|google map|gmaps)",
            "", query_str, flags=re.I
        ).strip()
        clean = re.sub(r"\b(instagram|tiktok|pinterest|linkedin|quora|facebook)\b", "", clean, flags=re.I).strip()
        clean = re.sub(r"\s+", " ", clean).strip()

        if not clean:
            clean = "ecommerce store"

        # Check for e-commerce/retail intent
        is_ecommerce = any(w in query_str.lower() for w in ["ecommerce", "shop", "store", "product", "sell", "brand", "retail", "clothing", "apparel", "beauty"])

        country_filter = " OR ".join(countries[:5])
        queries = []

        for platform in platforms:
            site = platform_sites.get(platform.lower())
            if not site:
                continue
            
            # Formulate platform-specific footprints to target actual shops/stores
            if platform.lower() == "linkedin":
                if is_ecommerce:
                    queries.append(f'{site} "{clean}" ("ecommerce" OR "d2c" OR "brand" OR "retail" OR "shop") ({country_filter})')
                else:
                    queries.append(f'{site} "{clean}" ({country_filter})')
            elif platform.lower() in ["instagram", "tiktok", "pinterest"]:
                if is_ecommerce:
                    queries.append(f'{site} "{clean}" ("linkin.bio" OR "linktr.ee" OR "shop" OR "store" OR "checkout" OR "buy") ({country_filter})')
                else:
                    queries.append(f'{site} "{clean}" ({country_filter})')
            else:
                queries.append(f'{site} "{clean}" ({country_filter})')

        # Generic web search footprints to find direct store websites (if not maps only)
        if "googlemaps" not in platforms or len(platforms) > 1:
            if is_ecommerce:
                # 1. Target direct Shopify stores
                queries.append(f'site:myshopify.com "{clean}" ({country_filter})')
                # 2. General web search focusing on checkout features
                queries.append(f'"{clean}" ("add to cart" OR "checkout" OR "buy online" OR "store" OR "shop") ({country_filter})')
            else:
                queries.append(f'"{clean}" company ({country_filter})')

        return queries

    def run(self, input_data: dict):
        from database.database import SessionLocal
        from database.models import GeographyConfig
        import re

        query_str = input_data.get("query", "businesses who need website")

        # ── Check for explicit google maps request ───────────────────────────
        is_googlemaps_request = any(w in query_str.lower() for w in ["google maps", "googlemaps", "google map", "gmaps"])

        # ── Load Geography Config from DB ────────────────────────────────────
        db = SessionLocal()
        try:
            geo = db.query(GeographyConfig).filter_by(workspace_id="default").first()
            if geo:
                active_tiers  = geo.active_tiers or ["tier1"]
                active_platforms = ["googlemaps"] if is_googlemaps_request else (geo.platforms or ["linkedin", "instagram", "tiktok", "quora", "pinterest", "googlemaps"])
                countries = []
                if "tier1" in active_tiers: countries += (geo.tier1_countries or self.TIER_COUNTRIES["tier1"])
                if "tier2" in active_tiers: countries += (geo.tier2_countries or self.TIER_COUNTRIES["tier2"])
                if "tier3" in active_tiers: countries += (geo.tier3_countries or self.TIER_COUNTRIES["tier3"])
            else:
                countries         = self.TIER_COUNTRIES["tier1"]
                active_platforms  = ["googlemaps"] if is_googlemaps_request else ["linkedin", "instagram", "tiktok", "quora", "pinterest", "googlemaps"]
        finally:
            db.close()

        queries = self._build_queries(query_str, countries, active_platforms)
        leads   = []
        seen    = set()

        try:
            with DDGS() as ddgs:
                for search_term in queries:
                    print(f"[LeadDiscoveryAgent] >> Searching: {search_term[:80]}")
                    try:
                        results = list(ddgs.text(search_term, max_results=20))
                    except Exception as e:
                        print(f"[LeadDiscoveryAgent] Search failed for query: {e}")
                        continue

                    for r in results:
                        url    = r.get("href", "")
                        title  = r.get("title", "")
                        body   = r.get("body", "")

                        if not url or not title:
                            continue

                        # Deduplicate by URL
                        if url in seen:
                            continue
                        seen.add(url)

                        source       = self._detect_source(url)
                        company_name = self._extract_company_name(title, url, source)
                        website      = self._extract_website(url, source)

                        # Skip generic/article/blog results
                        skip_keywords = (
                            "what is", "how to", "definition", "guide", "tutorial",
                            "best ", "top ", "vs ", " review", "builder", "platform",
                            "shopify", "woocommerce", "amazon", "google", "facebook"
                        )
                        if any(kw in company_name.lower() for kw in skip_keywords):
                            continue
                        if len(company_name) < 3 or company_name.lower() in ("home", "index", "search", "results"):
                            continue

                        leads.append({
                            "company_name":   company_name,
                            "website":        website,
                            "source":         source,
                            "contact_person": None,
                            "email":          None,
                            "linkedin":       url if source == "LinkedIn" else None,
                            "location":       next((c for c in countries if c.lower() in body.lower()), countries[0]),
                        })

                        print(f"[LeadDiscoveryAgent] + Found: {company_name} ({source})")

        except Exception as e:
            print(f"[LeadDiscoveryAgent] ERROR: {e}")

        print(f"[LeadDiscoveryAgent] DONE. Total leads scraped: {len(leads)}")

        # Return as a simple object with .leads attribute
        class LeadsResult:
            def __init__(self, leads_list):
                self.leads = type('obj', (object,), {f: None for f in []})
                self._leads = leads_list

            @property
            def leads(self):
                return self._leads

            @leads.setter
            def leads(self, v):
                self._leads = v

        result = LeadsResult([])
        result.leads = [
            type('Lead', (), l)() for l in leads
        ]
        # Also allow dict-style access for the route
        result._raw = leads
        return result

class LeadEnrichmentAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Lead Enrichment Agent",
            system_prompt="""You are the Lead Enrichment Agent. Your purpose is to enhance raw leads with intelligence.
Provide enrichment data like company size, revenue estimate, tech stack, hiring activity, and digital presence score.""",
            output_model=EnrichedLeadsOutput
        )

class LeadScoringAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Lead Scoring Agent",
            system_prompt="""You are the Lead Scoring Agent. Score the lead from 0-100 based on their tech stack, growth, and digital footprint.
Classification: 80-100 (HOT), 60-79 (WARM), 0-59 (COLD).
""",
            output_model=ScoredLeadsOutput
        )

# --- Phase 5 Agents: Deep Intelligence ---

class WebsiteAuditAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Website Audit Agent",
            system_prompt="""You are the Website Audit Agent.
Analyze the provided company description and infer potential website flaws they might have.
Output design scores, speed scores, UX issues, SEO opportunities, and conversion bottlenecks.
Be critical but realistic.""",
            output_model=WebsiteAudit
        )

class AIOpportunityDetectorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="AI Opportunity Detector Agent",
            system_prompt="""You are the AI Opportunity Detector specializing in identifying AI automation opportunities tailored to each unique business.

CRITICAL RULES:
- NEVER suggest generic agents. Every recommendation must be SPECIFIC to the exact business type.
- Analyze the company name, website, location, and source platform to infer what they do.
- Think: "What industry is this? What operations do they have? What pain points do businesses in this industry face?"

INDUSTRY-SPECIFIC AGENT EXAMPLES:
- Restaurant/Food/Cafe: AI Reservation Bot, Menu FAQ Agent, Food Order Chatbot
- Retail/Ecommerce/Shop: Product Recommendation Engine, Cart Abandonment Recovery Agent, Returns Processing Bot
- Real Estate: Property Listing Bot, Virtual Tour Booking Agent, Mortgage Pre-qualification Agent
- Healthcare/Medical/Clinic: Patient Appointment Scheduler, Medical FAQ Bot, Insurance Verification Agent
- Legal/Law Firm: Case Intake Automation Bot, Document Summarization Agent, Client Onboarding Agent
- Fitness/Gym/Yoga: Class Booking Bot, Personal Training Scheduler, Member Retention Agent
- Barber/Salon/Beauty: Appointment Booking Bot, Service Recommendation Agent, Review Follow-up Agent
- Finance/Accounting: Invoice Processing Agent, Expense Report Automation, Financial FAQ Bot
- Education/Training: Course Enrollment Bot, Student Progress Tracker, Tutor Matching Agent
- SaaS/Tech: Customer Onboarding Bot, Technical Support Agent, Churn Prevention Agent
- Marketing/Agency: Campaign Performance Bot, Lead Nurturing Agent, Content Repurposing Agent
- Hotel/Hospitality: Concierge AI Bot, Room Booking Agent, Guest Feedback Bot
- Automotive: Service Appointment Agent, Parts Availability Bot, Test Drive Booking Agent
- Construction: Project Estimation Bot, Supplier Quote Agent, Safety Compliance Tracker

Use these as inspiration but CREATE agents specific to the actual business you are analyzing.

Respond ONLY with valid JSON matching the schema. No explanation outside JSON.""",
            output_model=AIOpportunity
        )

# --- Phase 6 Agents: Hyper-Personalization ---

class PersonalizationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Personalization Agent",
            system_prompt="""You are the Hyper-Personalization Agent.
Write a highly personalized, non-generic Cold Email and LinkedIn DM.
Use the lead's Website Audit flaws and AI Opportunities to pitch a custom solution.
Mention specific pain points you found.""",
            output_model=PersonalizedMessage
        )

class ProposalGenerationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Proposal Generation Agent",
            system_prompt="""You are the Proposal Generation Agent. Your purpose is to generate highly personalized sales proposals.
RULES:
- Must personalize per lead
- Must include ROI logic
- Must reference lead-specific pain points
- Must NOT be generic
Generate a detailed proposal for the specified HOT lead.""",
            output_model=Proposal
        )

class OutreachAutomationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Outreach Automation Agent",
            system_prompt="""You are the Outreach Automation Agent. Your purpose is to simulate sending proposals and messages.
RULES:
- Must personalize message per lead
- Must attach proposal link
- Must log delivery status""",
            output_model=OutreachStatus
        )

class FollowupOptimizationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Followup Optimization Agent",
            system_prompt="""You are the Followup Optimization Agent. Your purpose is to maximize reply rate.
Strategy: Day 1 (Proposal), Day 3 (Reminder), Day 7 (Case study), Day 14 (Value offer), Day 21 (Final).""",
            output_model=Followup
        )

class MeetingBookingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Meeting Booking Agent",
            system_prompt="""You are the Meeting Booking Agent.
Your job is to parse incoming lead responses to qualify them, estimate their budget based on their size/needs, and schedule a meeting if qualified.""",
            output_model=MeetingBooking
        )

class CRMAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="CRM Agent",
            system_prompt="""You are the CRM Agent.
Update the pipeline stage for the lead: Lead Found -> Qualified -> Contacted -> Replied -> Meeting Scheduled -> Proposal Sent -> Won/Lost.
Calculate the probability to close (0-100) based on all interactions.""",
            output_model=CRMUpdate
        )

class AnalyticsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Analytics Agent",
            system_prompt="""You are the Analytics Agent. Your purpose is to track system performance and output metrics based on recent activity.""",
            output_model=Analytics
        )
