"""Genera datos sintéticos para benchmark de txtai.

Crea N documentos con estructura markdown realista
(secciones, listas, wikilinks) similares al vault de KAOS.
"""
import json
import random
import time
from pathlib import Path

random.seed(42)

TOPICS = [
    "machine learning", "deep learning", "neural networks", "transformers",
    "attention mechanism", "reinforcement learning", "computer vision",
    "natural language processing", "speech recognition", "knowledge graphs",
    "vector databases", "embeddings", "tokenization", "prompt engineering",
    "chain of thought", "RAG architecture", "multi-agent systems",
    "agent orchestration", "tool calling", "MCP protocol",
    "A2A protocol", "memory systems", "sleep cycle", "Hebbian learning",
    "DBSCAN clustering", "LLM distillation", "knowledge curation",
    "quality scoring", "verification chain", "compile then query",
]


def generate_doc(topic: str, i: int) -> str:
    """Genera un documento markdown realista."""
    subtopics = random.sample(TOPICS, min(5, len(TOPICS)))
    sections = [
        f"# {topic.title()} - Documento {i}",
        "",
        f"## Resumen",
        f"Este documento analiza {topic} en el contexto de sistemas multi-agente. "
        f"Se discuten {random.randint(3, 7)} aspectos clave relacionados con "
        f"{', '.join(subtopics[:3])}.",
        "",
        "## Introduccion",
        f"El estudio de {topic} ha cobrado relevancia en los ultimos anos. "
        f"Investigaciones recientes muestran que {random.choice([
            'la integracion con agentes mejora los resultados',
            'el enfoque hibrido supera a los metodos tradicionales',
            'la escalabilidad sigue siendo un desafio abierto',
            'los sistemas multi-agente se benefician de esta tecnica',
        ])}.",
        "",
        f"## {subtopics[0].title()}",
        f"### Conceptos Clave",
        *[f"- {c}: descripcion del concepto {c} en relacion con {topic}" 
          for c in random.sample(TOPICS, 4)],
        "",
        f"### [[{topic.replace(' ', '-')}]] y [[{subtopics[1].replace(' ', '-')}]]",
        f"La relacion entre {topic} y {subtopics[1]} es fundamental. "
        f"Estudios recientes en [[{topic.split()[0]}]] demuestran que...",
        "",
        f"## {subtopics[2].title()}",
        "### Metodologia",
        f"1. Primero, se analiza el estado del arte en {topic}",
        f"2. Luego, se aplican tecnicas de {subtopics[3]}",
        f"3. Finalmente, se evaluan los resultados contra {subtopics[4]}",
        "",
        "### Resultados",
        f"| Metrica | Valor | Baseline |",
        f"|---------|-------|----------|",
        f"| Precision | {random.uniform(0.75, 0.99):.2f} | {random.uniform(0.5, 0.7):.2f} |",
        f"| Recall | {random.uniform(0.7, 0.95):.2f} | {random.uniform(0.4, 0.6):.2f} |",
        f"| F1 | {random.uniform(0.72, 0.97):.2f} | {random.uniform(0.45, 0.65):.2f} |",
        "",
        f"## Conclusiones",
        f"El analisis muestra que {topic} tiene un impacto significativo en "
        f"el rendimiento de sistemas multi-agente. Se recomienda {random.choice([
            'profundizar en la integracion',
            'explorar variantes del metodo',
            'considerar alternativas mas eficientes',
            'implementar un piloto en produccion',
        ])}.",
        "",
        f"## Referencias",
        f"- Fuente: https://arxiv.org/abs/{random.randint(2000, 2600)}.{random.randint(10000, 99999)}",
        f"- Fuente: https://github.com/ejemplo/{topic.replace(' ', '-')}",
    ]
    return "\n".join(sections)


def generate_dataset(output_dir: Path, total: int):
    """Genera total documentos en output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    topics_cycle = [TOPICS[i % len(TOPICS)] for i in range(total)]

    for i in range(total):
        topic = topics_cycle[i]
        doc = generate_doc(topic, i)
        fname = f"bench-{i:05d}-{topic.replace(' ', '-')[:30]}.md"
        (output_dir / fname).write_text(doc, encoding="utf-8")

    print(f"Generados {total} documentos en {output_dir}")


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    out = Path(__file__).resolve().parent / "bench_data"
    generate_dataset(out, n)
