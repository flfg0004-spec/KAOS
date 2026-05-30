# Quality Engine Diagnosis

## Files Involved

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `lib/quality.py` | 389 | 7 vault metrics + agent sub-dimensions | Active, refactored (removed subprocess) |
| `lib/kosmos_quality.py` | 132 | DeepEval agent output evaluation + heuristic fallback | Active, optional DeepEval |
| `lib/smell_pipeline.py` | 81 | Static scanning + optional LLM-as-Judge | Active, optional DeepEval |
| `lib/atdi.py` | 33 | ATDI calculation from smell results | Active, depends on smell_pipeline |

## Identified Overlaps

### 1. Agent Score Calculation (DUPLICATED)
- `quality.py` lines 150-271: `_calculate_agent_subdimensions()` with 5 agent-specific heuristic scores
- `kosmos_quality.py` lines 31-49: `_heuristic_fallback()` with different methodology (veracidad, coherencia, completitud, reproducibilidad, utilidad)
- **Problem**: Two completely different heuristic systems for evaluating agent output quality

### 2. DeepEval Dependency Pattern (DUPLICATED)
- `kosmos_quality.py` lines 22-28: `_HAS_DEEPEVAL` try/except import
- `smell_pipeline.py` lines 8-14: Same `_HAS_DEEPEVAL` try/except import
- **Problem**: Both degrade silently when DeepEval is unavailable

### 3. Composite Score Calculation (SOLAPADO)
- `quality.py`: Uses `sum(d.values()) / len(d)` for agent sub-dimensions
- `kosmos_quality.py`: Uses `sum(dims.values()) / max(1, len(dims))` for heuristic fallback
- **Problem**: Nearly identical logic, different locations

### 4. Timeseries Storage (DUPLICATED)
- `quality.py` lines 323-341: `_save_timeseries()` with daily.jsonl capped at 365 entries
- `kosmos_quality.py` lines 82-104: `record()` with verification-scores.json capped at 10k entries
- **Problem**: Two separate persistence mechanisms for quality scores

### 5. Signal/Alerts (INCONSISTENTE)
- `kosmos_quality.py` lines 99-103: Writes quality_critical signals to `bridge/signals/`
- `quality.py`: No alert mechanism
- **Problem**: Alerts only from one path

## Synthetic Metrics (no DeepEval)

When DeepEval is unavailable, `kosmos_quality.py` uses:
```python
veracidad = 80 if text else 0
coherencia = min(100, len(lines) * 5 + 20)
completitud = 0 + 40 if has_titles + 20 if has_lists + 40 if len > 200
reproducibilidad = 60 + 30 if wikilinks + 10 if len > 50
utilidad = min(100, len(words) // 2 + 20)
```

These values are **arbitrary** and do not represent actual quality. For example, any text with titles, lists, >200 chars, and wikilinks gets a baseline of ~72/100 regardless of actual quality.

## Recommendation

1. **Merge** `quality.py` + `kosmos_quality.py` into `quality/` package:
   - `quality/__init__.py` — facade (current API)
   - `quality/vault.py` — vault metrics (from quality.py)
   - `quality/agent.py` — agent evaluation (from kosmos_quality.py)
   - `quality/smell.py` — smell detection (from smell_pipeline.py)
   - `quality/atdi.py` — debt index (from atdi.py, already clean)

2. **Make DeepEval required**: Remove `_HAS_DEEPEVAL` pattern; add to `requirements.txt`

3. **Unify persistence**: Single timeseries format, single signal mechanism

4. **Remove heuristic fallback**: Replace with minimum-score-based "insufficient data" instead of synthetic scores
