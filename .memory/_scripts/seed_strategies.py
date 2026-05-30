import sys, json, sqlite3, random
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent))
from strategy_memory import StrategicMemoryBank

STRATEGIES = [
    {
        "plan_type": "okr",
        "context": {"industry": "cloud-gpu", "region": "global", "team_size": 15},
        "content": {"objective": "Expand market share 15% to 25% in 12 months", "key_results": [{"name": "KR1: Increase market share", "target": "25%", "baseline": "15%"}, {"name": "KR2: Launch in 3 new regions", "target": "3", "baseline": "0"}]},
        "outcome_score": 8.2,
        "feedback": "KR execution successful, market share reached 27%. Strong team alignment."
    },
    {
        "plan_type": "okr",
        "context": {"industry": "ai-llm", "region": "na", "team_size": 8},
        "content": {"objective": "Reduce inference latency by 40% in Q2", "key_results": [{"name": "KR1: Reduce p50 latency", "target": "40%", "baseline": "120ms"}, {"name": "KR2: Achieve 99.9% uptime", "target": "99.9%", "baseline": "99.5%"}]},
        "outcome_score": 3.2,
        "feedback": "Infrastructure bottlenecks underestimated. Latency reduction only reached 18%."
    },
    {
        "plan_type": "roadmap",
        "context": {"industry": "cloud-infra", "region": "eu", "team_size": 25},
        "content": {"horizons": {"h1": {"focus": "Cost optimization", "initiatives": ["Migrate to ARM instances", "Implement spot instances"]}, "h2": {"focus": "Global expansion", "initiatives": ["EU data centers", "Asia-Pac PoPs"]}, "h3": {"focus": "Edge computing", "initiatives": ["Edge CDN", "IoT gateway"]}}, "risks": [{"risk": "Vendor lock-in", "probability": "medium"}]},
        "outcome_score": 7.5,
        "feedback": "Roadmap executed well. H1 savings exceeded targets by 15%."
    },
    {
        "plan_type": "foda",
        "context": {"industry": "saas", "region": "latam", "team_size": 10},
        "content": {"matrix": {"strengths": ["Strong brand in Brazil", "API-first architecture"], "weaknesses": ["Limited offline capability", "High churn in SMB segment"], "opportunities": ["Open banking regulation", "WhatsApp commerce growth"], "threats": ["New fintech entrants", "Currency volatility"]}},
        "outcome_score": 6.0,
        "feedback": "FODA identified churn risk correctly. Mitigation plan deployed."
    },
    {
        "plan_type": "strategic_analysis",
        "context": {"industry": "fintech", "region": "latam", "team_size": 20},
        "content": {"market": {"tam": 50000000000, "sam": 12000000000, "som": 3000000000}, "competitors": [{"name": "Nubank", "market_share": 0.35}, {"name": "Mercado Pago", "market_share": 0.25}], "trends": ["Embedded finance", "BNPL growth", "Real-time payments"]},
        "outcome_score": 2.1,
        "feedback": "Analysis too optimistic. Did not anticipate Brazilian credit regulation changes."
    },
    {
        "plan_type": "competitive_intel",
        "context": {"industry": "ai-llm", "region": "global", "team_size": 6},
        "content": {"competitors": [{"name": "OpenAI", "models": ["GPT-4o", "GPT-4-turbo"], "pricing": {"input": "$2.50", "output": "$10.00"}}, {"name": "Anthropic", "models": ["Claude 3 Opus", "Claude 3 Sonnet"], "pricing": {"input": "$15.00", "output": "$75.00"}}], "insights": ["OpenAI lowering prices aggressively", "Anthropic focusing on enterprise safety"]},
        "outcome_score": 9.0,
        "feedback": "Intel precisa. Pricing analysis enabled competitive response strategy."
    },
    {
        "plan_type": "okr",
        "context": {"industry": "healthtech", "region": "na", "team_size": 12},
        "content": {"objective": "Achieve HIPAA compliance and launch telehealth platform", "key_results": [{"name": "KR1: Pass HIPAA audit", "target": "100%", "baseline": "0%"}, {"name": "KR2: Onboard 50 clinics", "target": "50", "baseline": "5"}]},
        "outcome_score": 1.5,
        "feedback": "HIPAA audit failed twice. Timeline unrealistic for compliance requirements."
    },
    {
        "plan_type": "roadmap",
        "context": {"industry": "edtech", "region": "global", "team_size": 18},
        "content": {"horizons": {"h1": {"focus": "Content localization", "initiatives": ["Translate to 10 languages", "Regional curriculum adaptation"]}, "h2": {"focus": "AI tutoring", "initiatives": ["Personalized learning paths", "Automated grading"]}, "h3": {"focus": "VR classrooms", "initiatives": ["VR lab simulations", "Virtual campus"]}}},
        "outcome_score": 6.8,
        "feedback": "Localization successful. AI tutoring behind schedule due to data quality issues."
    },
    {
        "plan_type": "foda",
        "context": {"industry": "cloud-gpu", "region": "global", "team_size": 30},
        "content": {"matrix": {"strengths": ["NVIDIA partnership", "Lowest pricing per TFLOPS"], "weaknesses": ["Limited regions", "No spot instance market"], "opportunities": ["AI startup boom", "GPU shortage driving premium"], "threats": ["AWS/GCP entering bare metal GPU", "ASIC competitors"]}},
        "outcome_score": 8.5,
        "feedback": "FODA insights used to secure 3-year NVIDIA deal before competitor lock-in."
    },
    {
        "plan_type": "strategic_analysis",
        "context": {"industry": "saas", "region": "eu", "team_size": 15},
        "content": {"market_analysis": {"growth_rate": 0.18, "maturity": "growth", "consolidation_trend": True}, "recommendations": ["Focus on GDPR compliance as moat", "B2B vs B2C rebalancing needed", "Expand to DACH region"]},
        "outcome_score": 4.0,
        "feedback": "GDPR focus was correct but missed SMB pricing sensitivity. Churn increased."
    },
    {
        "plan_type": "competitive_intel",
        "context": {"industry": "fintech", "region": "eu", "team_size": 5},
        "content": {"competitors": [{"name": "Revolut", "features": ["Trading", "Crypto", "Budgeting"], "funding": {"round": "Series E", "valuation": 33000000000}}, {"name": "Wise", "features": ["Multi-currency", "Borderless", "API"], "funding": {"round": "Public", "market_cap": 11000000000}}], "key_findings": ["Revolut expanding into SME lending", "Wise deepening API for enterprise"]},
        "outcome_score": 7.0,
        "feedback": "Intel enabled product pivot to SME lending ahead of competitors."
    },
    {
        "plan_type": "okr",
        "context": {"industry": "cloud-infra", "region": "ap", "team_size": 22},
        "content": {"objective": "Reduce carbon footprint 50% by 2027", "key_results": [{"name": "KR1: Transition to 100% renewable energy", "target": "100%", "baseline": "35%"}, {"name": "KR2: Improve PUE from 1.4 to 1.1", "target": "1.1", "baseline": "1.4"}]},
        "outcome_score": 5.5,
        "feedback": "Renewable transition on track. PUE improvement slower than expected."
    },
    {
        "plan_type": "foda",
        "context": {"industry": "healthtech", "region": "eu", "team_size": 8},
        "content": {"matrix": {"strengths": ["Strong clinical validation", "EU MDR certified"], "weaknesses": ["High patient acquisition cost", "Limited insurance integrations"], "opportunities": ["Digital health reimbursement expanding", "Aging population in EU"], "threats": ["Big tech entering health", "Strict data sovereignty laws"]}},
        "outcome_score": 3.5,
        "feedback": "Missed threat of UK NHS data strategy change. Compliance costs doubled."
    },
    {
        "plan_type": "strategic_analysis",
        "context": {"industry": "edtech", "region": "latam", "team_size": 10},
        "content": {"market_sizing": {"tam": 8500000000, "sam": 2100000000, "som": 450000000}, "barriers": ["Internet penetration 67%", "Credit card adoption 35%", "Smartphone penetration 78%"], "opportunity": "Mobile-first micro-learning for underbanked populations"},
        "outcome_score": 8.0,
        "feedback": "Mobile-first strategy validated. User acquisition cost 40% below projection."
    },
    {
        "plan_type": "competitive_intel",
        "context": {"industry": "cloud-gpu", "region": "na", "team_size": 4},
        "content": {"players": [{"name": "CoreWeave", "differentiator": "Kubernetes-native GPU cloud", "pricing": "$2.10/GPU-hour"}, {"name": "Lambda Labs", "differentiator": "Deep learning focused", "pricing": "$1.90/GPU-hour"}, {"name": "Vast.ai", "differentiator": "Decentralized GPU marketplace", "pricing": "$1.50/GPU-hour"}], "trends": ["H100 supply constraints easing", "Demand shifting to H200/B200"]},
        "outcome_score": 2.8,
        "feedback": "Pricing intel was outdated by 3 weeks. Market moved faster than analysis cycle."
    },
    {
        "plan_type": "okr",
        "context": {"industry": "saas", "region": "global", "team_size": 40},
        "content": {"objective": "Achieve $100M ARR by end of fiscal year", "key_results": [{"name": "KR1: Grow from $65M to $100M ARR", "target": "$100M", "baseline": "$65M"}, {"name": "KR2: Reduce churn from 5% to 2% monthly", "target": "2%", "baseline": "5%"}]},
        "outcome_score": 9.5,
        "feedback": "ARR reached $108M. Churn reduced to 1.8%. All KRs exceeded targets."
    },
    {
        "plan_type": "roadmap",
        "context": {"industry": "fintech", "region": "latam", "team_size": 35},
        "content": {"horizons": {"h1": {"focus": "Payment infrastructure modernization", "initiatives": ["Pix instant payments integration", "QR code payment rollout"]}, "h2": {"focus": "Credit products expansion", "initiatives": ["Buy now pay later", "Personal loans"]}, "h3": {"focus": "Digital banking ecosystem", "initiatives": ["Digital account", "Insurance products"]}}},
        "outcome_score": 7.8,
        "feedback": "Pix integration ahead of schedule. BNPL launch delayed 2 months."
    },
    {
        "plan_type": "foda",
        "context": {"industry": "ai-llm", "region": "global", "team_size": 50},
        "content": {"matrix": {"strengths": ["Proprietary training data", "Distributed training infra"], "weaknesses": ["Smaller context window than rivals", "No multimodal capability"], "opportunities": ["Enterprise fine-tuning demand", "On-premise LLM deployment"], "threats": ["Open source models (Llama 3, Mistral)", "Regulation on AI safety"]}},
        "outcome_score": 5.0,
        "feedback": "Accurate SWOT. Decision to double down on enterprise fine-tuning. Neutral impact."
    },
    {
        "plan_type": "strategic_analysis",
        "context": {"industry": "cloud-infra", "region": "global", "team_size": 60},
        "content": {"analysis": {"margin_by_segment": {"compute": 0.35, "storage": 0.55, "network": 0.25}, "growth_drivers": ["AI workload migration", "Multi-cloud adoption"]}, "recommendation": "Invest in managed AI services layer above raw compute"},
        "outcome_score": 4.5,
        "feedback": "Analysis correct but execution too slow. Competitor launched similar service first."
    },
    {
        "plan_type": "competitive_intel",
        "context": {"industry": "healthtech", "region": "global", "team_size": 4},
        "content": {"report": {"period": "2026-Q1", "competitors_map": [{"name": "Teladoc", "revenue": "$2.4B", "focus": "Virtual primary care"}, {"name": "Amwell", "revenue": "$0.8B", "focus": "Hybrid care platform"}, {"name": "Babylon", "revenue": "$0.5B", "focus": "AI-powered triage"}], "insight": "Market consolidating around integrated platforms over point solutions"}},
        "outcome_score": 8.8,
        "feedback": "Intel validated M&A strategy for platform consolidation."
    },
    {
        "plan_type": "okr",
        "context": {"industry": "edtech", "region": "ap", "team_size": 14},
        "content": {"objective": "Become #1 online learning platform in Southeast Asia", "key_results": [{"name": "KR1: Reach 5M MAU from 1.5M MAU", "target": "5M", "baseline": "1.5M"}, {"name": "KR2: Achieve NPS of 60+", "target": "60", "baseline": "42"}]},
        "outcome_score": 6.2,
        "feedback": "MAU reached 4.2M. NPS hit 58. Close but not meeting stretch targets."
    },
]

bank = StrategicMemoryBank()
for s in STRATEGIES:
    bank.store(s["context"], s["content"], s["plan_type"], s["outcome_score"], s["feedback"])

seed_dir = Path(__file__).resolve().parent
conn = sqlite3.connect(str(seed_dir / "strategy_memory.db"))
cur = conn.cursor()
cur.execute("SELECT id FROM strategies ORDER BY id")
ids = [row[0] for row in cur.fetchall()]
for sid in ids:
    days_ago = random.randint(0, 90)
    hours_ago = random.randint(0, 23)
    mins_ago = random.randint(0, 59)
    ts = (datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=mins_ago)).isoformat()
    cur.execute("UPDATE strategies SET timestamp = ? WHERE id = ?", (ts, sid))
conn.commit()
conn.close()

print(f"Seeded {len(STRATEGIES)} strategies with distributed timestamps")
