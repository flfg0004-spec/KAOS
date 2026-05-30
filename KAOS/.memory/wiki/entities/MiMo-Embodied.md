---
type: model-family
name: MiMo-Embodied
role: embodied-ai
description: "Sub-familia de modelos MiMo especializados en robótica y vehículos — percepción, planificación motora, navegación autónoma y control en tiempo real"
status: active
vendor: Xiaomi
tags: [xiaomi, mimo, embodied, robotics, autonomous-driving, su7, cyberdog]
aliases: [MiMo Embodied, Xiaomi Embodied AI, MiMo Robotics]
created: 2026-05-26
modified: 2026-05-26
confidence: medium
sources:
  - Anuncios oficiales Xiaomi (2025-2026)
---

# MiMo-Embodied — Modelos para Robótica y Vehículos

## Descripción

**MiMo-Embodied** es la sub-familia de modelos de la familia [[MiMo]] especializada en inteligencia artificial corporizada (embodied AI). Diseñada para operar en sistemas físicos que interactúan con el mundo real: robots, vehículos autónomos y dispositivos IoT avanzados.

## Modelos Incluidos

| Modelo | Tipo | Aplicación |
|--------|------|------------|
| [[XLA-Cognitive-Model|XLA Cognitive Model]] | Conducción autónoma | [[xiaomi-su7|Xiaomi SU7]] |
| *MiMo-CyberDog* | Robótica móvil | CyberDog 2 (robot cuadrúpedo) |
| *MiMo-Manipulation* | Manipulación | Brazos robóticos, fabricación |

> Nota: *MiMo-CyberDog* y *MiMo-Manipulation* son extensiones especuladas de la familia; requieren verificación adicional.

## Capacidades Clave

- **Percepción espacio-temporal**: Comprensión 3D del entorno en tiempo real
- **Planificación motora**: Control de actuadores, trayectorias y manipuladores
- **Navegación autónoma**: SLAM, evitación de obstáculos, path planning
- **Fusión sensorial**: Integración de cámaras, LiDAR, IMU, ultrasonido
- **Baja latencia**: Inferencia en dispositivo con requisitos de tiempo real

## Aplicaciones

```
MiMo-Embodied
    │
    ├──► XLA Cognitive Model ──► Xiaomi SU7 (conducción autónoma)
    │
    ├──► CyberDog ──► Robot cuadrúpedo (navegación, interacción)
    │
    └──► Smart Factory ──► Robots de fabricación (manipulación, control)
```

## Relaciones

- [[MiMo]] — Familia principal
- [[XLA-Cognitive-Model|XLA Cognitive Model]] — Modelo de conducción autónoma
- [[MiMo-V2-Omni]] — Base de procesamiento multimodal para percepción
- [[Miclaw]] — Interfaz de usuario para vehículos

## Fuentes
- Anuncios oficiales Xiaomi (CyberDog 2, SU7, Smart Factory)
- Xiaomi AI Lab — Robotics Division publications
