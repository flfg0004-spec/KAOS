import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from crewai.memory.storage.backend import MemoryRecord
from lib.crew_memory import KAOSStorageBackend
from lib.crew_orchestrator import KAOSEmbeddingFunction, get_crewai_llm


def test_kaos_embedding_function():
    """
    Verifica que KAOSEmbeddingFunction se inicialice y devuelva embeddings con formato correcto.
    """
    embedder = KAOSEmbeddingFunction()
    test_texts = ["Hola KAOS", "CrewAI integration test"]
    embeddings = embedder(test_texts)
    
    assert isinstance(embeddings, list)
    assert len(embeddings) == len(test_texts)
    for emb in embeddings:
        assert isinstance(emb, list)
        assert len(emb) == 384  # Dimensión de BAAI/bge-small-en-v1.5
        assert all(isinstance(val, float) for val in emb)


def test_kaos_storage_backend_save():
    """
    Verifica que KAOSStorageBackend guarde registros localmente y emita señales en el bridge.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Instancia el backend apuntando al directorio temporal
        backend = KAOSStorageBackend(path=tmp_path / "crew_mem")
        
        # Sobrescribe el bridge dir para no ensuciar el real
        test_bridge_dir = tmp_path / "bridge" / "signals"
        backend.bridge_dir = test_bridge_dir
        backend.bridge_dir.mkdir(parents=True, exist_ok=True)
        
        record = MemoryRecord(
            content="Este es un recuerdo de prueba para el puente de KAOS",
            scope="/test/scope",
            categories=["test", "unit-test"],
            importance=0.9,
            source="test-runner"
        )
        
        # Guardar en el backend
        backend.save([record])
        
        # Verificar que la señal en bridge se haya creado y contenga los datos esperados
        signal_file = test_bridge_dir / f"crewai_mem_{record.id}.json"
        assert signal_file.exists()
        
        import json
        data = json.loads(signal_file.read_text(encoding="utf-8"))
        assert data["id"] == record.id
        assert data["content"] == record.content
        assert data["scope"] == record.scope
        assert "crewai" in data["origin_system"]


def test_get_crewai_llm():
    """
    Verifica que get_crewai_llm retorne una instancia de LLM configurada correctamente.
    """
    llm = get_crewai_llm(model_name="gemini-3.5-flash", temperature=0.1)
    assert llm.model == "openai/gemini-3.5-flash"
    assert llm.temperature == 0.1
    assert "opencode.ai" in llm.base_url


@patch("crewai.Crew.kickoff")
def test_run_crew_kickoff(mock_kickoff):
    """
    Verifica el flujo general de ejecución y registro de tokens de CrewAI con mocking.
    """
    from lib.crew_orchestrator import run_research_crew
    
    # Mock de la respuesta de kickoff
    mock_response = MagicMock()
    mock_response.raw = "Resultado simulado de la investigación."
    
    mock_metrics = MagicMock()
    mock_metrics.prompt_tokens = 100
    mock_metrics.cached_prompt_tokens = 40
    mock_metrics.completion_tokens = 50
    mock_metrics.reasoning_tokens = 10
    
    mock_response.token_usage = mock_metrics
    mock_kickoff.return_value = mock_response
    
    # Ejecuta el flujo
    result = run_research_crew(topic="test-topic")
    
    assert result == "Resultado simulado de la investigación."
    assert mock_kickoff.called
