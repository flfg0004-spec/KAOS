# Roadmap de Implementación Multi-Modelo

## Fase 1: Inmediata (Semanas 1-2)

### Objetivo: Router funcional + Aletheia en Pro + Metis en Kimi

| Tarea | Responsable | Dependencia | Validación |
|-------|-------------|-------------|------------|
| Implementar Router en dsol.py (TASK_MODEL_MAP, resolve_model, CircuitBreaker, chat) | Kratos | Ninguna | pytest test_dsol.py |
| AGENT_MODELS actualizado en llm.py | Kratos | Router implementado | pytest test_llm_quality.py |
| chat() funcionando para research→go-pro, strategy→go-kimi-latest | Kratos | Router + llm.py | Smoke test manual |
| Verificación cruzada: agentes usan modelos diferentes | Kratos | Router | Verificar en logs |
| ADR-015 creado y revisado | Metis | Ninguna | Documento firmado |
| Documento de arquitectura del router | Kosmos | Ninguna | Revisión técnica |

### Riesgos Fase 1
- **Bug de tool_call.id en Kimi K2.6**: Si aparece, limitar multi-turno a 2 rondas con Kimi
- **Throttling de OpenCode Go**: Monitorear response times

## Fase 2: Corto Plazo (Semanas 3-4)

### Objetivo: Dashboard de diversidad + agentes actualizados

| Tarea | Responsable | Dependencia | Validación |
|-------|-------------|-------------|------------|
| TokenTracker.get_model_breakdown() implementado | Kratos | Router | Verificar reporte |
| Dashboard de métricas multi-modelo | Metis | TokenTracker | Dashboard visible |
| Agentes actualizados para usar task_type | Cada agente | chat() funcional | Código revisado |
| Tests de integración del router | Kratos | Router estable | pytest test_router.py |
| Documentar prompt engineering por modelo | Mnemosyne | Experiencia de uso | Documento wiki |

## Fase 3: Mediano Plazo (Semanas 5-8)

### Objetivo: Optimización + monitoreo de nuevos modelos

| Tarea | Responsable | Dependencia | Validación |
|-------|-------------|-------------|------------|
| Evaluar Qwen 3.7-Max (esperar baja de precio post-lanzamiento) | Aletheia | Investigación | Informe de precios |
| Evaluar GLM 5.1 para self-hosting (licencia MIT) | Kosmos | Investigación | ADR de decisión |
| Auto-tuning del router basado en métricas reales | Kronos | Dashboard funcional | % tráfico óptimo |
| Revisión trimestral de la estrategia | Metis | Todas las fases | Documento de revisión |
