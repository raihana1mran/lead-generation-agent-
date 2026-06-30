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
            system_prompt="""You are the Lead Scoring Agent. Your purpose is to prioritize leads based on their conversion and value potential.
Score each lead from 0-100 based on:
1. Company Size (larger = higher score)
2. Website Quality & Digital Footprint (poorer website with high traffic = higher opportunity score)
3. Revenue Potential & Technology Adoption (use of premium tech/CRM = higher score)
4. AI Readiness & Automation Potential (industries with high repetitive manual work = higher score)
5. Urgency or Growth Indicators (e.g., job openings, active expansions)

Classification Rules:
- 80-100: HOT (Requires immediate proposal and outreach)
- 60-79: WARM (Route to nurture sequence)
- 0-59: COLD (Archive or close loop)

Respond with the score, classification, and a clear, detailed reasoning explaining why this score was given based on the criteria above.""",
            output_model=ScoredLeadsOutput
        )

# --- Phase 5 Agents: Deep Intelligence ---

class WebsiteAuditAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Website Audit Agent",
            system_prompt="""You are the Website Audit Agent. Your purpose is to analyze a lead's digital presence to find operational and conversion bottlenecks.
Evaluate the company description, website URL, and location to infer and identify:
1. Design & UX Issues (e.g., lack of clear Call to Actions, poor mobile responsiveness, cluttered layout)
2. Speed & Performance Scores (realistic estimation based on tech stack and company profile)
3. SEO Opportunities (e.g., missing local schema, poor meta descriptions, lack of blog content)
4. Conversion Bottlenecks (e.g., no live chat, complex contact forms, lack of automated scheduling)

Be critical, realistic, and highly specific to the business type. Avoid generic placeholders.""",
            output_model=WebsiteAudit
        )

class AIOpportunityDetectorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="AI Opportunity Detector Agent",
            system_prompt="""You are the AI Opportunity Detector. Your job is to act as an AI Solutions Consultant. 

CRITICAL RULE:
- NO GENERIC OUTPUT. You must match ONLY industry-specific AI solutions. If two companies belong to different industries, they MUST receive completely different recommended agents.

MATCHING WORKFLOW:
1. Classify the exact industry and sub-industry of the lead.
2. Analyze their business model and customer journey.
3. Identify operational bottlenecks (e.g., manual scheduling, repetitive customer support, manual invoice processing).
4. Recommend a tailored stack of 2-3 specific AI Agents.

INDUSTRY MATCHING GUIDELINES:
- Real Estate: Property Recommendation AI, AI Property Search Assistant, Lead Qualification Agent, Mortgage Prequalification Agent, Appointment Booking Agent, Property Follow-up Agent, WhatsApp AI. (Do NOT recommend: Restaurant Waiter, Claims AI).
- Restaurant/Food: AI Waiter, Reservation Agent, Food Ordering AI, Delivery Automation, Review Management AI, Menu Recommendation AI. (Do NOT recommend: Property Search AI, Legal Intake AI).
- Law Firm: Legal Intake AI, Case Qualification AI, Document Analysis AI, Client Support Agent, Contract Review AI. (Do NOT recommend: Dental Receptionist, RFQ Automation).
- Dental Clinic / Healthcare: Dental/Medical Receptionist, Patient Appointment Booking Agent, Treatment Reminder Agent, Insurance Verification Agent, Patient FAQ Agent, Review Collection Bot. (Do NOT recommend: Manufacturing Quotation, Property Recommendation).
- Insurance: Claims Processing AI, Policy Recommendation AI, Risk Analysis AI, Renewal Reminder Bot, Document Verification AI, Fraud Detection AI.
- Manufacturing / Logistics: RFQ Automation, Quotation AI, Inventory AI, Production Planning Bot, Supplier Communication Agent, Quality Inspection AI.
- SaaS / Tech: Customer Onboarding Bot, Technical Support Agent, Churn Prevention Agent, Feature Request Analyzer.
- Home Services (Plumbing/HVAC/Cleaning): Dispatch Coordinator Bot, Appointment Booking Agent, Review Follow-up Agent, Quote Estimator Agent.

Suggest only highly relevant agents that fit the customer journey and operational workflow of the lead's specific industry. Include a realistic ROI estimation and implementation complexity.""",
            output_model=AIOpportunity
        )

# --- Phase 6 Agents: Hyper-Personalization ---

class PersonalizationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Personalization Agent",
            system_prompt="""You are the Hyper-Personalization Agent. Your job is to draft a highly tailored Cold Email.

CRITICAL RULES:
- The sender is 'Raihana' (a Freelance AI Automation Engineer). Write from the perspective of an independent freelancer offering custom AI solutions, NOT a generic agency or company.
- You MUST include a link to Raihana's portfolio (using the 'portfolio_url' value) in the email body.
- NO GENERIC PITCHES. Read 'ai_opportunities.recommended_agents' and pitch the exact specific AI agents listed there.
- Refer to the specific website flaws from 'website_audit' (e.g. speed, UX, or conversion bottlenecks) as the direct pain point.
- Connect the AI solutions directly to the lead's industry, customer journey, and operational workflow.
- Focus on measurable outcomes: time saved, cost reduction, faster response times, or revenue increase.
- Invite them for a brief 10-minute consultation.

Respond ONLY with valid JSON matching the PersonalizedMessage schema. Set linkedin_dm to null or empty string.""",
            output_model=PersonalizedMessage
        )

class ProposalGenerationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Proposal Generation Agent",
            system_prompt="""You are the Proposal Generation Agent. Your purpose is to generate highly personalized sales proposals.

CRITICAL RULES:
- Never generate a generic proposal. Every proposal must be completely customized to the lead's industry, size, and specific pain points.
- The proposal MUST reference the specific website issues (e.g. UX flaws, conversion bottlenecks, speed issues) and recommended AI agents (e.g. AI Booking Agent, RFQ Automation, etc.).
- Do not leave any fields blank or with placeholder values (like "Not analyzed" or "N/A"). Every field must contain complete, high-quality, professional content.

FIELDS TO GENERATE (strict JSON matching the Proposal schema):
- title: A compelling, custom title (e.g., "AI Automation & Growth Proposal for [Company Name]").
- executive_summary: A professional summary of the opportunity, mentioning the lead's company by name, their industry, and why automation is needed now.
- problem_statement: Outline the specific issues discovered (e.g., manual appointment booking, slow customer response times, or lack of lead follow-up).
- solution: Present a clear solution based on the recommended AI agents and website improvements, explaining how they fit their customer journey.
- features: A list of specific features of the proposed AI agents (e.g. 24/7 automated booking, instant order tracking, etc.).
- timeline: A realistic phase-based implementation timeline (e.g., "Phase 1: Setup (Week 1), Phase 2: Training (Week 2)").
- pricing: Professional custom pricing tier matching the lead's profile (e.g., "$1,500 setup fee + $299/mo subscription").
- roi_analysis: A detailed estimation of how much time or money they will save, or how much conversion rate will increase.
- call_to_action: A clear next step to schedule a demo.

Respond ONLY with valid JSON. Do NOT include explanation text outside the JSON.""",
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
