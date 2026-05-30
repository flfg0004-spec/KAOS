# Per-Agent Governance Policies
package kaos.agents

deny[msg] {
    input.agent == "aletheia"
    output := input.output
    not contains(output, "[[")
    msg := "Aletheia research output must contain wikilinks to sources"
}

deny[msg] {
    input.agent == "kosmos"
    output := input.output
    not contains(output, "ADR")
    not contains(output, "# ")
    msg := "Kosmos architecture analysis must reference ADR and have structure"
}

deny[msg] {
    input.agent == "metis"
    output := input.output
    not contains(output, "OKR")
    not contains(output, "objective")
    msg := "Metis strategy output must contain OKRs or objectives"
}

deny[msg] {
    input.agent == "kratos"
    output := input.output
    not contains(output, "```")
    msg := "Kratos code output must contain code blocks"
}

deny[msg] {
    input.agent == "mnemosyne"
    output := input.output
    not contains(output, "[[")
    msg := "Mnemosyne curation must contain wikilinks to concepts"
}

deny[msg] {
    output := input.output
    count(output) < 50
    msg := sprintf("Agent '%v' output too short (%v chars, minimum 50)", [input.agent, count(output)])
}
