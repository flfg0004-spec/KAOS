"""LangSmith evaluation dataset — baseline for pipeline quality.

Provides test cases for evaluating pipeline execution.
Each case has a topic, expected outputs, and tags for filtering.
"""

EVAL_CASES = [
    {
        "topic": "investigar arquitectura de microservicios con event-sourcing",
        "profile": "desarrollo",
        "expected": ["aletheia_output", "kosmos_output", "metis_output"],
        "tags": ["architecture", "research"],
    },
    {
        "topic": "implementar API REST con JWT en Python",
        "profile": "desarrollo",
        "expected": ["aletheia_output", "kosmos_output", "metis_output", "kratos_output"],
        "tags": ["code", "python", "api"],
    },
    {
        "topic": "analizar deuda técnica del proyecto KAOS",
        "profile": "produccion",
        "expected": ["aletheia_output", "kosmos_output", "metis_output"],
        "tags": ["strategy", "analysis"],
    },
    {
        "topic": "comparar patrones CQRS vs Event Sourcing",
        "profile": "desarrollo",
        "expected": ["aletheia_output", "kosmos_output"],
        "tags": ["research", "architecture"],
    },
    {
        "topic": "generar plan de pruebas unitarias para modulo de autenticacion",
        "profile": "desarrollo",
        "expected": ["aletheia_output", "kratos_output"],
        "tags": ["code", "testing"],
    },
]


def get_dataset() -> list[dict]:
    return EVAL_CASES


def get_dataset_by_tag(tag: str) -> list[dict]:
    return [c for c in EVAL_CASES if tag in c["tags"]]
