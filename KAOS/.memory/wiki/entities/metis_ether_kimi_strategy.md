---
entity: Metis
type: strategic_plan
date: 2026-05-26
title: Estrategia Ether + Kimi — Plan Táctico Integral
status: approved
tags: [ether, kimi, routing, cost-optimization, multimodal]
agents_involved: [metis, kratos, kronos]
total_effort_hours: 20
timeline_days: 5
---

## Resumen

Plan táctico para implementar routing adaptativo 4-dimensional para Kimi K2.5/K2.6 en el módulo Ether de KAOS.
Objetivo: reducir costo semanal de $4.36 a &lt;$3.90 (10%+) mediante rebalance de tráfico (Kimi 5%→15%),
routing por contexto &gt;100K, routing multimodal, y budget-aware fallbacks.

## Work Packages

| WP | Nombre | Esfuerzo | Archivos |
|----|--------|----------|----------|
| WP-001 | Config Rebalance | 0.5h | config.py |
| WP-002 | Router Context-Aware | 2.5h | router.py |
| WP-003 | Budget Tracking | 1.5h | tracker.py |
| WP-004 | CB Diferencial | 2h | circuit.py |
| WP-005 | Rate Limiter Per-Model | 1h | limiter.py |
| WP-006 | Multimodal Pipeline | 3h | client.py |
| WP-007 | Adaptive Routing | 3h | router.py |
| WP-008 | Compression Tandem | 3h | client.py, router.py |
| WP-009 | Test Suite | 2h | test_kimi_routing.py |
| WP-010 | Rollout Scripts | 1h | .tools/scripts/ |
| WP-011 | Verification | 1.5h | client.py |

## Feature Flags

- ETHER_KIMI_ENABLED (master switch)
- ETHER_CONTEXT_ROUTING (&gt;100K → Kimi)
- ETHER_COST_AWARE_ROUTING (budget fallback)
- ETHER_CIRCUIT_DIFFERENTIAL (thresholds por modelo)
- ETHER_RATE_LIMIT_PER_MODEL (límites por modelo)
- ETHER_MULTIMODAL (imágenes → Kimi)
- ETHER_ADAPTIVE_ROUTING (complejidad → Kimi/Flash)
- ETHER_KIMI_COMPRESSION (K2.6 compression)

## Métricas Clave

- % tráfico Kimi: 5% → 15% target
- Costo semanal: $4.36 → &lt;$3.90 target
- Contexto &gt;100K: 0% → 100% a Kimi
- Budget excedidos: Sin control → 0
- Score Ether: 53 → &gt;70/100
