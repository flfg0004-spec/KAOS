"""KratosDecision enum — canonical decision values for Kratos agent output.

Provides typed enum with str-equality for backward compatibility with
existing consumers that compare against raw strings like "complete".
"""

from enum import Enum
from typing import Union


class KratosDecision(str, Enum):
    """Decision values for Kratos agent output.

    Every invocation of kratos_node produces one of these values,
    serializable as a plain string in JSON output.
    """

    COMPLETE = "complete"
    NEEDS_CURATION = "needs_curation"
    FAILED = "failed"
    REJECTED_BY_GOV = "rejected_by_gov"
    EARLY_EXIT = "early_exit"

    def __eq__(self, other: Union[str, "KratosDecision"]) -> bool:  # type: ignore[override]
        """Compare with another KratosDecision or a plain string."""
        if isinstance(other, KratosDecision):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

    def __str__(self) -> str:
        """Serialize to string for JSON output."""
        return self.value
