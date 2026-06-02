"""Workflow templates as data. Seed these into workflow_templates.steps (JSONB).

A step is: {agent_type, input?, requires_approval?}. The engine runs them in order,
threading RunContext between them. Note the Control Agent appears twice — once pre,
once post — by passing control_phase via input.
"""

EXECUTIVE_BRIEFING = {
    "name": "Executive Briefing",
    "description": "Grounded, cited executive briefing with cost + hallucination governance.",
    "required_agents": [
        "document_research", "token_hallucination_control",
        "executive_briefing",
    ],
    "steps": [
        {"agent_type": "document_research"},
        {"agent_type": "token_hallucination_control",
         "input": {"control_phase": "pre"}},
        {"agent_type": "executive_briefing"},
        {"agent_type": "token_hallucination_control",
         "input": {"control_phase": "post"},
         "requires_approval": False},  # flip to True for a human gate before finalizing
    ],
}

RISK_REVIEW = {
    "name": "Risk Review",
    "description": "Severity-ranked, source-cited risk register.",
    "required_agents": [
        "document_research", "token_hallucination_control", "risk_analysis",
    ],
    "steps": [
        {"agent_type": "document_research"},
        {"agent_type": "token_hallucination_control", "input": {"control_phase": "pre"}},
        {"agent_type": "risk_analysis"},
        {"agent_type": "token_hallucination_control", "input": {"control_phase": "post"}},
    ],
}

INVESTOR_MEMO = {
    "name": "Investor Memo",
    "description": "Thesis, market, traction, risks, asks — grounded and cited.",
    "required_agents": [
        "document_research", "token_hallucination_control",
        "executive_briefing", "risk_analysis",
    ],
    "steps": [
        {"agent_type": "document_research"},
        {"agent_type": "token_hallucination_control", "input": {"control_phase": "pre"}},
        {"agent_type": "executive_briefing", "input": {"focus": "Draft an investor memo."}},
        {"agent_type": "risk_analysis"},
        {"agent_type": "token_hallucination_control", "input": {"control_phase": "post"}},
    ],
}

ALL_TEMPLATES = [EXECUTIVE_BRIEFING, RISK_REVIEW, INVESTOR_MEMO]