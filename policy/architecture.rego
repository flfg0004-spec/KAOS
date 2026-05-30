# KAOS Architecture Governance Policies
package kaos.architecture

deny[msg] {
    adr := input.kosmos_adr
    code := input.kratos_code
    required := adr.required_pattern
    not contains(code, required)
    msg := sprintf("Code violates ADR '%v': missing required pattern '%v'", [adr.title, required])
}

deny[msg] {
    pattern := input.architecture_pattern
    approved := {"microservices", "modular-monolith", "event-driven", "layered", "hexagonal", "cqrs", "clean-architecture"}
    not pattern in approved
    msg := sprintf("Architecture pattern '%v' is not in approved list", [pattern])
}

deny[msg] {
    dep := input.dependency
    dep.source == dep.target
    msg := sprintf("Self-dependency detected: '%v' depends on itself", [dep.source])
}

deny[msg] {
    adr := input.adr
    required_fields := {"title", "context", "decision", "consequences", "status"}
    missing := required_fields - {k | k := object.keys(adr)[_]}
    count(missing) > 0
    msg := sprintf("ADR is missing required fields: %v", [concat(", ", missing)])
}

deny[msg] {
    concept := input.concept
    concept.min_confidence > 0
    concept.confidence < concept.min_confidence
    msg := sprintf("Concept '%v' confidence (%v) below threshold (%v)", [concept.name, concept.confidence, concept.min_confidence])
}

deny[msg] {
    bridge := input.cross_agent_bridge
    bridge.expected == true
    bridge.value == ""
    msg := sprintf("Cross-agent bridge '%v' is empty but expected to be populated", [bridge.name])
}
