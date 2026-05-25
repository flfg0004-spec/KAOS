import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from crewai import Agent, Task, Crew, LLM
from crewai.memory.unified_memory import Memory
from lib.config import OPENCODE_GO_ENDPOINT, OPENCODE_GO_KEY, VAULT_ROOT
from lib.crew_memory import KAOSStorageBackend
from lib.dsol import TokenTracker

class KAOSEmbeddingFunction:
    """
    Función de embedding compatible con Chroma/CrewAI utilizando BAAI/bge-small-en-v1.5 de fastembed,
    manteniendo consistencia con la base de datos sqlite-vec de KAOS.
    """
    def __init__(self) -> None:
        from fastembed import TextEmbedding
        self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    def __call__(self, input: list[str]) -> list[list[float]]:
        # Genera embeddings locales sin llamadas externas
        return [list(map(float, vec)) for vec in self.model.embed(input)]


def get_crewai_llm(model_name: str = "gemini-3.5-flash", temperature: float = 0.2) -> LLM:
    """
    Retorna una instancia de LLM de CrewAI configurada para OpenCode Go.
    """
    return LLM(
        model=f"openai/{model_name}",
        base_url=OPENCODE_GO_ENDPOINT,
        api_key=OPENCODE_GO_KEY,
        temperature=temperature
    )


def run_research_crew(topic: str) -> str:
    """
    Configura y ejecuta una Micro-Crew de investigación técnica (estilo Aletheia).
    """
    llm = get_crewai_llm(model_name="gemini-3.5-flash", temperature=0.2)
    
    # 1. Definición de Agentes con Backstory y Roles
    researcher = Agent(
        role="Investigador Senior de KAOS",
        goal="Investigar exhaustivamente y sintetizar información técnica confiable sobre {topic}.",
        backstory=(
            "Eres el principal agente de investigación de KAOS. Tu enfoque es "
            "la rigurosidad, la verificación de fuentes y el análisis profundo. "
            "Siempre citas referencias y presentas hallazgos estructurados en markdown."
        ),
        llm=llm,
        verbose=True,
        max_iter=3
    )
    
    writer = Agent(
        role="Redactor Estratégico de KAOS",
        goal="Redactar informes de síntesis técnica claros, concisos y accionables basados en la investigación de {topic}.",
        backstory=(
            "Eres un escritor técnico y analista de KAOS. Tu talento es "
            "estructurar ideas complejas en resúmenes ejecutivos claros "
            "y elegantes, con wikilinks cuando es necesario."
        ),
        llm=llm,
        verbose=True,
        max_iter=3
    )

    # 2. Definición de Tareas
    research_task = Task(
        description=(
            "Realiza una investigación detallada sobre: {topic}.\n"
            "Identifica conceptos clave, tecnologías emergentes y cualquier fuente relevante.\n"
            "Establece una base sólida de hechos."
        ),
        expected_output="Un documento de notas de investigación crudo y estructurado con hallazgos clave.",
        agent=researcher
    )

    writing_task = Task(
        description=(
            "Utiliza las notas de investigación para escribir un informe ejecutivo sobre: {topic}.\n"
            "El formato debe ser Markdown limpio y profesional.\n"
            "Debe incluir: Resumen Ejecutivo, Hallazgos Detallados, Próximos Pasos o Recomendaciones."
        ),
        expected_output="Un informe ejecutivo técnico formal en formato markdown con secciones claras.",
        agent=writer
    )

    # 3. Configuración de Memoria Personalizada (KAOS Storage Backend)
    storage_backend = KAOSStorageBackend()
    embedder = KAOSEmbeddingFunction()
    
    custom_memory = Memory(
        llm=llm,
        storage=storage_backend,
        embedder=embedder
    )

    # 4. Ensamble de la Crew
    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        verbose=True,
        memory=True,
        # Inyecta nuestra instancia de memoria unificada de KAOS
    )
    # Reemplazamos la memoria privada por nuestra memoria configurada con backend personalizado
    crew._memory = custom_memory

    # 5. Ejecución de la Crew con monitoreo de tokens
    result = crew.kickoff(inputs={"topic": topic})

    # 6. Extracción y registro de métricas de tokens en TokenTracker de KAOS
    try:
        metrics = result.token_usage
        if metrics:
            tt = TokenTracker()
            # Mapeamos los hits y fallos de caché de la respuesta
            cache_hit = metrics.cached_prompt_tokens
            # Los prompt tokens reportados por CrewAI suelen incluir los cacheados
            cache_miss = max(0, metrics.prompt_tokens - cache_hit)
            
            tt.track(
                agent="crewai",
                prompt_tokens=metrics.prompt_tokens,
                completion_tokens=metrics.completion_tokens,
                cache_hit=cache_hit,
                cache_miss=cache_miss,
                reasoning=metrics.reasoning_tokens,
                model="gemini-3.5-flash",
                task="crewai-research",
            )
    except Exception as e:
        print(f"  ⚠️ Error registrando tokens de CrewAI: {e}")

    return result.raw


def run_crew(crew_name: str, topic: str) -> str:
    """
    Entry point para ejecutar Crews por nombre desde la CLI.
    """
    crews = {
        "research": run_research_crew
    }
    
    executor = crews.get(crew_name)
    if not executor:
        raise ValueError(f"Crew desconocida: '{crew_name}'. Disponibles: {list(crews.keys())}")
        
    return executor(topic)
