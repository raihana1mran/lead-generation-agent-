import os
from engine.orchestrator import Orchestrator
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    if not os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") == "your_openrouter_api_key_here":
        print("ERROR: Please set your OPENROUTER_API_KEY in the .env file.")
        return

    print("Starting LeadForge AI...")
    print(f"Using Model: {os.getenv('OPENROUTER_MODEL')}")

    # Mock Business Input to trigger the engine
    business_input = {
        "company_name": "SaaS Growth Partners",
        "industry": "B2B SaaS Consulting",
        "services": ["Go-to-market strategy", "Sales funnels", "Lead generation"],
        "target_customers": "Series A and Series B B2B SaaS companies",
        "pricing": "$10,000/mo retainer",
        "geography": "North America and UK"
    }

    orchestrator = Orchestrator()
    try:
        orchestrator.run_pipeline(business_input)
    except Exception as e:
        print(f"\nPipeline failed: {e}")

if __name__ == "__main__":
    main()
