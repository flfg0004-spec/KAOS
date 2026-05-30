"""Quality Gates Pipeline — modular package.

Re-exports all public symbols for backward compatibility.
"""

from lib.quality_gate._toolchain import detect_toolchain
from lib.quality_gate.gates import register_gate, get_gate, list_gates
from lib.quality_gate.gates.syntax import gate_syntax, gate_syntax_multi
from lib.quality_gate.gates.compilation import gate_compilation, gate_compilation_multi
from lib.quality_gate.gates.lint import gate_lint, gate_lint_multi
from lib.quality_gate.gates.types import gate_types
from lib.quality_gate.gates.structure import gate_structure
from lib.quality_gate.gates.security import gate_security
from lib.quality_gate.gates.coverage import gate_coverage
from lib.quality_gate.gates.style import gate_style
from lib.quality_gate._evaluate import evaluate, evaluate_parallel

# Auto-register all Python gates
_gates = [
    ("syntax", gate_syntax, 0.15, ["python"]),
    ("compilation", gate_compilation, 0.10, ["python"]),
    ("lint", gate_lint, 0.15, ["python"]),
    ("types", gate_types, 0.15, ["python"]),
    ("structure", gate_structure, 0.15, ["python"]),
    ("security", gate_security, 0.15, ["python"]),
    ("coverage", gate_coverage, 0.15, ["python"]),
    ("style", gate_style, 0.10, ["python"]),
    ("syntax_multi", gate_syntax_multi, 0.0, ["rust", "typescript", "go"]),
    ("compilation_multi", gate_compilation_multi, 0.0, ["rust", "typescript", "go"]),
    ("lint_multi", gate_lint_multi, 0.0, ["rust", "typescript", "go"]),
]
for name, func, weight, langs in _gates:
    register_gate(name, func, weight, langs)

# Legacy alias for backward compat
_detect_toolchain = detect_toolchain
_find_file = None
_detect_languages = None

__all__ = [
    "evaluate", "evaluate_parallel",
    "gate_syntax", "gate_syntax_multi",
    "gate_compilation", "gate_compilation_multi",
    "gate_lint", "gate_lint_multi",
    "gate_types", "gate_structure", "gate_security",
    "gate_coverage", "gate_style",
    "detect_toolchain", "register_gate", "get_gate", "list_gates",
]
