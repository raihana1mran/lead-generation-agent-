from agents.all_agents import LeadDiscoveryAgent
agent = LeadDiscoveryAgent()
result = agent.run({"query": "ecommerce businesses without website instagram tiktok"})
print(f"Total scraped: {len(result._raw)}")
for l in result._raw[:5]:
    print(f"  - {l['company_name']} ({l['source']}) -> {l['website']}")
