"""Demo: Pipeline KAOS End-to-End — 8 nodos del DAG."""
import json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # .memory/_scripts

from lib.orchestrator import KAOSState, build_graph
from lib.agent_executor import (
    planner_node, aletheia_node, kosmos_node, metis_node,
    kratos_node, mnemosyne_node,
)
from lib.orchestrator import critic_node, _evaluator_node, route_after_strategy, route_after_critic

TOPIC = "implementar API REST con JWT y autenticacion en Python"
PROFILE = "standard"

print("=" * 72)
print("  KAOS PIPELINE DEMO — 8 NODOS LANGGRAPH DAG")
print("  Topic:", TOPIC)
print("  Profile:", PROFILE)
print("=" * 72)

state = KAOSState(topic=TOPIC, profile=PROFILE)

# ── NODO 1: Planner ──────────────────────────────────────────
print("\n┌─ 1. PLANNER ─────────────────────────────────────┐")
t = time.time()
state = planner_node(state)
plan = state.get("plan", {})
elapsed = time.time() - t
print(f"  Complejidad: {plan.get('complexity')}")
print(f"  Subtareas:   {[s['id'] for s in plan.get('subtasks',[])]}")
print(f"  Has code:    {plan.get('has_code')}")
print(f"  Tiempo:      {elapsed:.3f}s")
print("└────────────────────────────────────────────────────┘")

# ── NODO 2: Aletheia ────────────────────────────────────────
print("\n┌─ 2. ALETHEIA (Investigación) ─────────────────────┐")
t = time.time()
state = aletheia_node(state)
elapsed = time.time() - t
output = state.get("aletheia_output", "")
print(f"  Output:      {output[:70]}...")
print(f"  Lines:       {len(output.split(chr(10)))}")
print(f"  Tiempo:      {elapsed:.3f}s")
print("└────────────────────────────────────────────────────┘")

# ── NODO 3: Kosmos ──────────────────────────────────────────
print("\n┌─ 3. KOSMOS (Arquitectura) ────────────────────────┐")
t = time.time()
state = kosmos_node(state)
elapsed = time.time() - t
output = state.get("kosmos_output", "")
print(f"  Output:      {output[:70]}...")
print(f"  Tiempo:      {elapsed:.3f}s")
print("└────────────────────────────────────────────────────┘")

# ── NODO 4: Metis ───────────────────────────────────────────
print("\n┌─ 4. METIS (Estrategia) ───────────────────────────┐")
t = time.time()
state = metis_node(state)
elapsed = time.time() - t
output = state.get("metis_output", "")
print(f"  Output:      {output[:70]}...")
print(f"  Tiempo:      {elapsed:.3f}s")
print(f"  Routing:     {route_after_strategy(state)} → kratos")
print("└────────────────────────────────────────────────────┘")

# ── NODO 5: Kratos ──────────────────────────────────────────
print("\n┌─ 5. KRATOS (Implementación) ──────────────────────┐")
t = time.time()
state = kratos_node(state)
elapsed = time.time() - t
output = state.get("kratos_output", "")
print(f"  Output:      {output[:70]}...")
print(f"  Decision:    {state.get('kratos_decision')}")
print(f"  Tiempo:      {elapsed:.3f}s")
print("└────────────────────────────────────────────────────┘")

# ── NODO 6: Mnemosyne ───────────────────────────────────────
print("\n┌─ 6. MNEMOSYNE (Curación) ─────────────────────────┐")
t = time.time()
state = mnemosyne_node(state)
elapsed = time.time() - t
output = state.get("mnemosyne_output", "")
print(f"  Output:      {output[:70]}...")
print(f"  Tiempo:      {elapsed:.3f}s")
print("└────────────────────────────────────────────────────┘")

# ── NODO 7: Critic ──────────────────────────────────────────
print("\n┌─ 7. CRITIC (Feedback Loop) ───────────────────────┐")
t = time.time()
state = critic_node(state)
elapsed = time.time() - t
print(f"  Score:       {state.get('critic_score')}/100")
print(f"  Feedback:    {state.get('critic_feedback')}")
print(f"  Iteración:   {state.get('iteration')}/{3}")
route = route_after_critic(state)
print(f"  Routing:     {route} {'✓' if route == 'advance' else '→ refine'}")
print(f"  Tiempo:      {elapsed:.3f}s")
print("└────────────────────────────────────────────────────┘")

# ── NODO 8: Evaluator ───────────────────────────────────────
print("\n┌─ 8. KOSMOS EVALUATOR (System Health) ─────────────┐")
t = time.time()
state = _evaluator_node(state)
elapsed = time.time() - t
ev = state.get("evaluation", {})
print(f"  System Health:  {ev.get('system_health', '?')}/100")
print(f"  Pipeline Score: {ev.get('pipeline_score', '?')}/100")
print(f"  Composite:      {ev.get('composite', '?')}/100")
n_components = len(ev.get("system_components", {}))
print(f"  Componentes:    {n_components} escaneados")
for agent, e in ev.get("pipeline_evaluation", {}).items():
    score = e.get("score", "N/A")
    status = "✅" if e.get("passed") else "❌"
    print(f"    {agent:12s} {score:>5}/100 {status}")
print(f"  Tiempo:      {elapsed:.3f}s")
print("└────────────────────────────────────────────────────┘")

# ── Archivos generados ──────────────────────────────────────
raw_dir = Path(__file__).resolve().parent.parent / "_pipeline" / "raw"
plan_path = Path(__file__).resolve().parent.parent / "_pipeline" / "plan.json"
ctx_path = Path(__file__).resolve().parent.parent / "_pipeline" / "context.json"
eval_path = Path(__file__).resolve().parent.parent / "_pipeline" / "evaluation.json"

print("\n" + "=" * 72)
print("  ARCHIVOS GENERADOS")
print("=" * 72)
files = list(raw_dir.glob("*.md"))
for f in sorted(files):
    print(f"  📄 {f.name}  ({f.stat().st_size} bytes)")
for path, label in [(plan_path, "plan.json"), (ctx_path, "context.json"), (eval_path, "evaluation.json")]:
    if path.exists():
        print(f"  📄 {label}  ({path.stat().st_size} bytes)")

# ── DAG ─────────────────────────────────────────────────────
print("\n" + "=" * 72)
print("  DAG: 8 NODOS — LangGraph Orchestrator")
print("=" * 72)
print("""
  Planner ─→ Aletheia ─→ Kosmos ─→ Metis ─→ Kratos ─→ Mnemosyne
                                                              │
                                                              v
                                                          Critic
                                                              │
                                              ┌───────────────┤
                                              │               │
                                          refine          advance
                                          (max 3)            │
                                              │               v
                                              └── Aletheia  Evaluator → END

  Routing:
    Metis  ─?→ Kratos  (si has_code_subtasks o keywords code)
    Critic ─?→ refine  (si score < 60 y iterations < 3)
""")

print("=" * 72)
print("  DEMO COMPLETA — 8/8 nodos ejecutados")
print(f"  Pipeline Score: {state.get('evaluation',{}).get('composite', '?')}/100")
print("=" * 72)
