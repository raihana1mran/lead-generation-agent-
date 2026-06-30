from memory.bus import memory_bus
from agents.all_agents import (
    BusinessUnderstandingAgent, MarketIntelligenceAgent,
    LeadDiscoveryAgent, LeadEnrichmentAgent, LeadScoringAgent,
    ProposalGenerationAgent, OutreachAutomationAgent,
    FollowupOptimizationAgent, AnalyticsAgent
)
from models.shared import PriorityEnum, ClassificationEnum

class Orchestrator:
    def __init__(self):
        print("[Orchestrator] Initializing agents...")
        self.agent_bus = BusinessUnderstandingAgent()
        self.agent_mkt = MarketIntelligenceAgent()
        self.agent_disc = LeadDiscoveryAgent()
        self.agent_enrich = LeadEnrichmentAgent()
        self.agent_score = LeadScoringAgent()
        self.agent_prop = ProposalGenerationAgent()
        self.agent_outreach = OutreachAutomationAgent()
        self.agent_followup = FollowupOptimizationAgent()
        self.agent_analytics = AnalyticsAgent()

    def run_pipeline(self, business_input: dict):
        print("\n=== STARTING LEADFORGE AI PIPELINE ===")
        
        # 1. Business Understanding
        print("\n--- STEP 1: Business Understanding ---")
        biz_context = self.agent_bus.run(business_input)
        memory_bus.write("business_context_memory", biz_context.model_dump())
        print(f"ICP Extracted: {biz_context.icp.industry} / {biz_context.icp.company_size}")

        # 2. Market Intelligence
        print("\n--- STEP 2: Market Intelligence ---")
        mkt_intel = self.agent_mkt.run(biz_context)
        memory_bus.write("campaign_memory", mkt_intel.model_dump())
        print(f"Top Competitors: {', '.join(mkt_intel.competitors)}")

        # 3. Lead Discovery
        print("\n--- STEP 3: Lead Discovery ---")
        leads_out = self.agent_disc.run(mkt_intel)
        memory_bus.write("leads_memory", [l.model_dump() for l in leads_out.leads])
        print(f"Discovered {len(leads_out.leads)} raw leads.")

        # 4. Lead Enrichment
        print("\n--- STEP 4: Lead Enrichment ---")
        enriched_out = self.agent_enrich.run(leads_out)
        print(f"Enriched {len(enriched_out.enriched_leads)} leads.")

        # 5. Lead Scoring
        print("\n--- STEP 5: Lead Scoring ---")
        scored_out = self.agent_score.run(enriched_out)
        
        hot_leads = []
        for lead in scored_out.scored_leads:
            print(f"Lead: {lead.company} | Score: {lead.lead_score} | Class: {lead.classification}")
            if lead.lead_score >= 70:
                hot_leads.append(lead)

        print(f"\nFound {len(hot_leads)} leads with score >= 70.")

        # 6. Proposals & Outreach for Hot Leads
        proposals_sent = 0
        for lead in hot_leads:
            print(f"\n--- STEP 6: Proposal Generation for {lead.company} ---")
            prop_input = {
                "lead_profile": lead.model_dump(),
                "business_context": memory_bus.read("business_context_memory")
            }
            proposal = self.agent_prop.run(prop_input)
            
            # Save to memory
            props = memory_bus.read("proposal_memory")
            if not isinstance(props, dict):
                props = {}
            props[lead.company] = proposal.model_dump()
            memory_bus.write("proposal_memory", props)

            print(f"\n--- STEP 7: Outreach Automation for {lead.company} ---")
            outreach = self.agent_outreach.run(proposal)
            proposals_sent += 1
            
            print(f"\n--- STEP 8: Follow-up Optimization for {lead.company} ---")
            # Simulate no reply within 48h
            followups = self.agent_followup.run({"outreach_status": outreach.model_dump(), "reply_received": False})
            print(f"Queued follow-up step 1 for {lead.company}.")

        # 9. Analytics
        print("\n--- STEP 9: Analytics ---")
        analytics_input = {
            "total_leads_discovered": len(leads_out.leads),
            "hot_leads_found": len(hot_leads),
            "proposals_sent": proposals_sent
        }
        analytics = self.agent_analytics.run(analytics_input)
        memory_bus.write("analytics_memory", analytics.model_dump())
        print(f"\n=== PIPELINE COMPLETE ===")
        print(f"Analytics: Total Leads={analytics.total_leads}, Hot={analytics.hot_leads}, Proposals={analytics.proposals_sent}")
