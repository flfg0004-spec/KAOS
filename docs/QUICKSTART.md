# QUICKSTART — KAOS en 5 minutos

## Requisitos
- Python 3.10+
- agy (Antigravity CLI) autenticado

## 1. Instalar dependencias
```bash
pip install -r .memory/_scripts/requirements.txt
```

## 2. Verificar salud del sistema
```bash
py .memory/_scripts/vault.py health --auto
py .memory/_scripts/vault.py lint run
py .memory/_scripts/vault.py quality
```

## 3. Exploración rápida (Gemini Flash, gratis)
```bash
agy -p "explora el concepto de memoria persistente en sistemas multiagente"
```

O desde OpenCode: usa `agy_ask_flash()` con tu prompt.

## 4. Pipeline de conocimiento (DeepSeek)
```bash
py .memory/_scripts/vault.py pipeline init --topic "tu tema de investigación"
py .memory/_scripts/vault.py hydrate --agent aletheia
# ... trabaja ...
py .memory/_scripts/vault.py pipeline step-done --agent aletheia
```

## 5. Generar visualizaciones
```bash
py .memory/_scripts/vault.py viz
# Abre .memory/VIZ_GRAPH.md para ver el grafo de conocimiento
```

## 6. Correr tests
```bash
py .memory/_scripts/tests/run.py --fast  # 81 tests en ~7s
```

## Comandos útiles

| Comando | Qué hace |
|---------|----------|
| `vault.py health` | Health check del vault |
| `vault.py lint run` | Busca wikilinks rotos, orphans, stale |
| `vault.py lint coverage` | Coverage de raw + matriz de confianza |
| `vault.py consolidate` | DBSCAN consolidation + quality |
| `vault.py improve lint` | Lint + report |
| `vault.py improve wikilinks` | Sugerencias de cross-linking |
| `vault.py speed` | Métricas del sistema DUAL |
| `vault.py archive` | Archivar raw/ >30 días sin curar |
