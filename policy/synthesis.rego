package kaos.synthesis

default allow = false

allow {
    input.dry_run == true
}

allow {
    input.diff_ratio <= input.max_diff_ratio
    input.score >= 10
    input.level != "CANONICAL"
}

deny["CANONICAL documents cannot be auto-synthesized"] {
    input.level == "CANONICAL"
}

deny["Score below minimum threshold for synthesis"] {
    input.score < 10
}

deny["Diff ratio exceeds maximum allowed"] {
    input.diff_ratio > input.max_diff_ratio
}
