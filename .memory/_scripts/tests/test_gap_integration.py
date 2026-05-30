"""Tests de integración Metis↔Aletheia para gap detection."""
import json, sys, tempfile, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".memory" / "_scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".memory" / "_scripts" / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".tools"))

from gap_service import dispatch, ingest_response, _load_gaps, Gap
import gap_service


def test_gap_service_dispatch_creates_file():
    gaps = [Gap("¿Cuál es el market share de X?", "análisis competitivo", "alta")]
    with tempfile.TemporaryDirectory() as tmp:
        gap_service.CACHE_DIR = Path(tmp)
        dispatch(gaps)
        json_files = list(Path(tmp).glob("dispatch_*.json"))
        assert len(json_files) >= 1, "dispatch should create a JSON file"
        data = json.loads(json_files[0].read_text(encoding="utf-8"))
        assert data["type"] == "gap_detection"
        assert len(data["gaps"]) == 1
        assert data["gaps"][0]["question"] == "¿Cuál es el market share de X?"
        assert data["gaps"][0]["priority"] == "alta"


def test_gap_service_ingest_resolves_gaps():
    gaps = [Gap("¿Cuál es el market share de X?", "análisis competitivo", "alta")]
    with tempfile.TemporaryDirectory() as tmp:
        gap_service.CACHE_DIR = Path(tmp)
        dispatch(gaps)
        response = {
            "type": "gap_detection_response",
            "session_id": "test",
            "responses": [{"question": "¿Cuál es el market share de X?", "answer": "X tiene 23%", "sources": ["src1"], "confidence": "alta"}]
        }
        response_file = Path(tmp) / "response.json"
        response_file.write_text(json.dumps(response), encoding="utf-8")
        count = ingest_response(response_file.read_text(encoding="utf-8"))
        assert count >= 1, "ingest should resolve at least one gap"
        records = _load_gaps()
        resolved = [r for r in records if r.get("status") == "resolved"]
        assert len(resolved) >= 1, "at least one gap should be resolved"


def test_gap_service_contract_matches_schema():
    gaps = [Gap("¿Cuál es el market share de X?", "análisis competitivo", "alta")]
    with tempfile.TemporaryDirectory() as tmp:
        gap_service.CACHE_DIR = Path(tmp)
        dispatch(gaps)
        json_files = list(Path(tmp).glob("dispatch_*.json"))
        data = json.loads(json_files[0].read_text(encoding="utf-8"))
        assert "type" in data
        assert "session_id" in data
        assert "gaps" in data
        assert isinstance(data["gaps"], list)
        for g in data["gaps"]:
            assert "question" in g
            assert "priority" in g
            assert g["priority"] in ("alta", "media", "baja")


def test_gap_service_dispatch_no_gaps():
    with tempfile.TemporaryDirectory() as tmp:
        gap_service.CACHE_DIR = Path(tmp)
        dispatch([])
        json_files = list(Path(tmp).glob("dispatch_*.json"))
        assert len(json_files) >= 1, "dispatch should create file even with 0 gaps"
        data = json.loads(json_files[0].read_text(encoding="utf-8"))
        assert len(data["gaps"]) == 0


def test_gap_service_ingest_no_match():
    gaps = [Gap("pregunta A", "contexto", "media")]
    with tempfile.TemporaryDirectory() as tmp:
        gap_service.CACHE_DIR = Path(tmp)
        dispatch(gaps)
        response = {
            "type": "gap_detection_response",
            "session_id": "test",
            "responses": [{"question": "pregunta B", "answer": "respuesta", "sources": [], "confidence": "media"}]
        }
        count = ingest_response(json.dumps(response))
        assert count == 0, "no gaps should match unrelated questions"
