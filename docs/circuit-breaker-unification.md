# CircuitBreaker Unification Plan

## Current State

| Location | Lines | Purpose | Features |
|----------|-------|---------|----------|
| `lib/ether/circuit.py` | 157 | Per-model + per-provider CB | Persistence, thread-safe, differential config, Prometheus metrics |
| `lib/self_healing.py` | 139 | Per-agent CB with backoff | Signal-based escalation, healing log, exponential backoff |

## Overlap
Both implement the same state machine: `closed → open → half-open`. Different thresholds, different persistence, different use cases.

## Migration Plan

### Phase 1 (Week 3): Analysis Complete ✅
- Both CBs identified and documented
- Feature flag `use_unified_circuit_breaker` exists in `lib/feature_flags.py`

### Phase 2 (Week 4): Make `self_healing.py` delegate to `ether/circuit.py`
- Replace `self_healing.CircuitBreaker` with a thin wrapper around `ether.circuit.CircuitBreaker`
- Keep `SelfHealingGraph` API intact (get, record_success, record_failure)
- Add `agent_name` as a provider identifier in ether CB
- Use `use_unified_circuit_breaker` flag, default OFF

### Phase 3 (Week 5): Remove duplicate code
- Delete `self_healing.CircuitBreaker` class
- `SelfHealingGraph` directly uses `ether.circuit`
- All `from lib.self_healing import ...` imports still work via delegation

### Phase 4 (Week 6): Cleanup
- Remove feature flag once stable
- Delete unused imports
- Document the unified CB in ADR

## Risk
- Low: `SelfHealingGraph` API is simple (3 methods), easy to wrap
- Medium: `ether/circuit.py` uses per-model keys while `self_healing` uses per-agent keys — need consistent naming
