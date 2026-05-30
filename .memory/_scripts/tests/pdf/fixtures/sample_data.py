"""Sample data fixtures for PDF report tests.

Pre-built data dictionaries for each KAOS agent to avoid duplicating
test data across multiple test files.
"""

SAMPLE_ALETHEIA_DATA = {
    "title": "Research: AI Trends",
    "subtitle": "Aletheia Research Agent",
    "sections": [
        {"title": "Executive Summary", "content": "This report covers the latest AI trends in 2026."},
        {
            "title": "Key Findings",
            "content": "- **Trend 1**: Agentic AI is accelerating\n- **Trend 2**: Multimodal models dominate",
        },
    ],
    "charts": [
        {
            "id": "sources_by_type",
            "type": "pie",
            "title": "Sources by Type",
            "data": {"labels": ["arxiv", "news", "blog"], "values": [15, 8, 3]},
        },
    ],
    "extra": {
        "findings": [
            {"title": "Agentic AI", "description": "Autonomous agents are becoming mainstream."},
            {"title": "Multimodal", "description": "Vision-language models lead SOTA."},
        ],
        "sources": [
            {"title": "arXiv Paper", "type": "arxiv", "url": "https://arxiv.org/abs/2401.00001"},
            {"title": "Tech Blog", "type": "blog", "url": "https://example.com/blog"},
        ],
    },
}

SAMPLE_KOSMOS_DATA = {
    "title": "Architecture Review: Microservices Migration",
    "subtitle": "Kosmos Architecture Agent",
    "sections": [
        {
            "title": "Architecture Decision Record",
            "content": "ADR-001: Adopt event-driven architecture for order processing.",
        },
    ],
    "charts": [
        {
            "id": "quality_radar",
            "type": "radar",
            "title": "Architecture Quality",
            "data": {
                "labels": ["Scalability", "Maintainability", "Security", "Performance", "Cost"],
                "values": [85, 72, 90, 78, 65],
            },
        },
    ],
    "extra": {
        "adr_content": "ADR-001: Event-driven architecture adopted.",
    },
}

SAMPLE_METIS_DATA = {
    "title": "Strategic Analysis: Market Expansion",
    "subtitle": "Metis Strategy Agent",
    "sections": [
        {"title": "Strategy Overview", "content": "Expand into APAC markets with a phased approach."},
        {
            "title": "Risks",
            "content": "- **Regulatory**: Different compliance requirements\n- **Competition**: Established local players",
        },
    ],
    "charts": [
        {
            "id": "okr_progress",
            "type": "bar",
            "title": "OKR Progress",
            "data": {"x": ["Market Entry", "Product Localization", "Team Hiring"], "y": [65, 40, 30]},
        },
        {
            "id": "risk_matrix",
            "type": "pie",
            "title": "Risk Distribution",
            "data": {"labels": ["high", "medium", "low"], "values": [2, 5, 3]},
        },
    ],
    "extra": {
        "okrs": [
            {"name": "Market Entry", "progress": 65},
            {"name": "Product Localization", "progress": 40},
            {"name": "Team Hiring", "progress": 30},
        ],
        "risks": [
            {"name": "Regulatory", "impact": "High", "level": "high"},
            {"name": "Competition", "impact": "Medium", "level": "medium"},
        ],
    },
}

SAMPLE_KRATOS_DATA = {
    "title": "Code Quality Report: Payment Module",
    "subtitle": "Kratos Code Agent",
    "sections": [
        {
            "title": "Code Metrics",
            "content": "- **Lines of Code**: 4500\n- **Test Coverage**: 87%\n- **Complexity**: 42",
        },
    ],
    "charts": [
        {
            "id": "code_metrics",
            "type": "bar",
            "title": "Code Metrics",
            "data": {"x": ["LOC", "Coverage", "Complexity", "Bugs"], "y": [4500, 87, 42, 3]},
        },
    ],
    "extra": {},
}

SAMPLE_MNEMOSYNE_DATA = {
    "title": "Curation Report: Knowledge Base Health",
    "subtitle": "Mnemosyne Memory Guardian",
    "sections": [
        {"title": "Curation Summary", "content": "Quality Score: **85/100**"},
    ],
    "charts": [
        {"id": "quality_gauge", "type": "gauge", "title": "Quality Score", "data": {"value": 85}},
        {
            "id": "phases_bar",
            "type": "bar",
            "title": "Curation Phases",
            "data": {"x": ["Deduplication", "Wikilink", "Archival"], "y": [120, 85, 45]},
        },
    ],
    "extra": {},
}

SAMPLE_KRONOS_DATA = {
    "title": "Pipeline Performance Report",
    "subtitle": "Kronos Orchestrator",
    "sections": [
        {
            "title": "Pipeline Metrics",
            "content": "- **Total Runs**: 245\n- **Avg Duration**: 12.4s\n- **Success Rate**: 94%",
        },
    ],
    "charts": [
        {
            "id": "costs_bar",
            "type": "bar",
            "title": "Cost Breakdown",
            "data": {"x": ["OpenAI", "Playwright", "Storage"], "y": [124.50, 32.00, 8.75]},
        },
    ],
    "extra": {
        "pipeline_metrics": {"Total Runs": 245, "Avg Duration": "12.4s", "Success Rate": "94%"},
        "costs": {"OpenAI": 124.50, "Playwright": 32.00, "Storage": 8.75},
    },
}

SAMPLE_PIPELINE_STATE = {
    "topic": "Full KAOS Pipeline Test",
    "aletheia_output": "Research on topic completed successfully.",
    "kosmos_output": "Architecture review documented.",
    "metis_output": "Strategy analysis delivered.",
    "kratos_output": "Code quality verified.",
    "mnemosyne_output": "Knowledge base curated.",
}
