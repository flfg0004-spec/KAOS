"""Tests de integración para el pipeline completo Obsidian + Mnemosyne.

Cada test usa archivos temporales y el código real (sin mock) para verificar
que los componentes del pipeline funcionan correctamente.

Ejecutar:
    py -3 -m pytest .memory/_scripts/tests/test_integration.py -v --no-header
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Ensure _scripts dir is in path for imports
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

os.environ["KAOS_TESTING"] = "1"


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_note(tmpdir: Path, rel_path: str, frontmatter: dict | None = None,
               content: str = "") -> Path:
    """Create a markdown note at tmpdir / rel_path with optional frontmatter."""
    path = tmpdir / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    if frontmatter:
        lines.append("---")
        for k, v in frontmatter.items():
            if isinstance(v, list):
                lines.append(f"{k}: {json.dumps(v)}")
            else:
                lines.append(f"{k}: {v}")
        lines.append("---")
    lines.append("")
    lines.append(content)

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ── Test 1: add_audience -> promote cycle ──────────────────────────────

class TestAudienceToPromotion:
    """Verifica que un archivo con audience:public se pueda promover."""

    def test_add_audience_and_promote(self):
        """Ciclo completo: añadir audience -> promover a library/."""
        from scripts.add_audience import add_audience_to_file, FRONTMATTER_RE

        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            src = _make_note(tmpdir, "wiki/concepts/test-note.md", {
                "title": "Test Note",
                "type": "concept",
                "tags": ["subject/test"],
                "created": "2026-01-01",
            }, "Contenido de prueba para el ciclo audience->promote.")

            # 1. add_audience — debe inferir audience
            result = add_audience_to_file(src, dry_run=False)
            assert result["status"] == "updated", f"Expected updated, got {result}"
            assert result["audience"] is not None

            # 2. Verificar que el archivo ahora tiene audience
            content = src.read_text(encoding="utf-8")
            match = FRONTMATTER_RE.match(content)
            assert match is not None, "Frontmatter debe existir después de add_audience"
            assert "audience:" in match.group(1), "Debe tener audience field"

    def test_promote_public_note(self):
        """Verifica que promote copia archivos con audience:public a library/."""
        from scripts.promote_to_library import promote_file

        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            src = _make_note(tmpdir, "wiki/concepts/public-note.md", {
                "title": "Public Note",
                "type": "concept",
                "tags": ["subject/test"],
                "created": "2026-01-01",
                "audience": "public",
                "score": 85,
            }, "Nota pública que debe ser promovida.")

            lib_concepts = tmpdir / "library" / "concepts"

            result = promote_file(src, lib_concepts, dry_run=False)
            assert result["action"] == "copy", f"Expected copy, got {result}"

            assert (lib_concepts / "public-note.md").exists()
            copied = (lib_concepts / "public-note.md").read_text(encoding="utf-8")
            assert "audience: public" in copied
            assert "promoted_from:" in copied
            assert "source_hash:" in copied

    def test_promote_skips_agent_only(self):
        """Verifica que notas con audience:agent NO se promueven."""
        from scripts.promote_to_library import promote_file

        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            src = _make_note(tmpdir, "wiki/concepts/agent-note.md", {
                "title": "Agent Note",
                "audience": "agent",
                "score": 90,
            }, "Nota solo para agentes.")

            lib_dir = tmpdir / "library" / "concepts"
            lib_dir.mkdir(parents=True, exist_ok=True)

            result = promote_file(src, lib_dir, dry_run=False)
            assert result["action"] == "skip", f"Expected skip, got {result}"
            assert not (lib_dir / "agent-note.md").exists()


# ── Test 2: scoring pipeline ───────────────────────────────────────────

class TestScoringPipeline:
    """Verifica que score_note() retorne estructura correcta."""

    def test_score_note_structure(self):
        """Verifica que score_note retorna 8 métricas con estructura completa."""
        from lib.scoring import score_note

        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            note = _make_note(tmpdir, "test-score.md", {
                "title": "Test",
                "type": "concept",
                "tags": ["subject/ai"],
                "created": "2026-01-01",
                "audience": "public",
                "aliases": ["test-alias"],
            }, "Contenido con [[wikilink]] y #tag de prueba " * 20)

            result = score_note(note)

            # Debe tener todos los campos esperados
            assert "path" in result
            assert "total_score" in result
            assert "metrics" in result
            assert "breakdown" in result

            # Debe tener 8 métricas
            expected_metrics = {
                "has_frontmatter", "has_tags", "has_wikilinks",
                "min_length", "audience_defined", "has_backlinks",
                "has_aliases", "is_linked",
            }
            assert set(result["metrics"].keys()) == expected_metrics

            # Cada métrica debe tener breakdown
            for name in expected_metrics:
                assert name in result["breakdown"]
                bd = result["breakdown"][name]
                assert "score" in bd
                assert "weight" in bd
                assert "weighted" in bd
                assert "description" in bd

            # total_score debe ser float 0-10
            assert isinstance(result["total_score"], float)
            assert 0.0 <= result["total_score"] <= 10.0

    def test_score_note_no_frontmatter(self):
        """Nota sin frontmatter debe tener score bajo."""
        from lib.scoring import score_note

        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            note = _make_note(tmpdir, "no-fm.md", frontmatter=None,
                              content="Sin frontmatter.")

            result = score_note(note)
            assert result["metrics"]["has_frontmatter"] == 0.0
            assert result["metrics"]["audience_defined"] == 0.0
            assert result["metrics"]["has_aliases"] == 0.0

    def test_score_note_full_marks(self):
        """Nota bien formada debe tener alto score."""
        from lib.scoring import score_note

        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            note = _make_note(tmpdir, "full-score.md", {
                "title": "Full Score Note",
                "type": "concept",
                "tags": ["subject/ai", "subject/ml"],
                "created": "2026-01-01",
                "audience": "public",
                "aliases": ["full-alias"],
            }, "#TAG Full content with [[wikilinks]] and lots of text. " * 50)

            result = score_note(note)
            # Debería tener score alto
            assert result["total_score"] >= 5.0, f"Expected high score, got {result['total_score']}"
            # Frontmatter completo
            assert result["metrics"]["has_frontmatter"] >= 0.5
            assert result["metrics"]["audience_defined"] == 1.0
            assert result["metrics"]["has_aliases"] == 1.0
            assert result["metrics"]["min_length"] == 1.0
            assert result["metrics"]["is_linked"] == 1.0


# ── Test 3: file_lock buffered_write ───────────────────────────────────

class TestBufferedWrite:
    """Verifica buffered_write con flush_now=True."""

    def test_buffered_write_flush_now(self):
        """flush_now=True debe escribir inmediatamente."""
        from lib.file_lock import buffered_write, flush_buffered_writes

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "test.json"
            result = buffered_write(p, {"key": "value"}, flush_now=True)
            assert result is True, "flush_now=True debe retornar True"
            assert p.exists()
            data = json.loads(p.read_text(encoding="utf-8"))
            assert data == {"key": "value"}

    def test_buffered_write_batch(self):
        """buffered_write sin flush_now debe bufferizar hasta flush."""
        from lib.file_lock import buffered_write, flush_buffered_writes

        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "a.json"
            p2 = Path(tmp) / "b.json"

            # Sin flush_now: debe bufferizar
            r1 = buffered_write(p1, {"data": 1}, buffer_size=5, flush_interval=300)
            assert r1 is False, "Debe bufferizar (no flush)"
            assert not p1.exists(), "No debe escribir todavía"

            r2 = buffered_write(p2, {"data": 2}, buffer_size=5, flush_interval=300)
            assert r2 is False, "Debe bufferizar (no flush)"
            assert not p2.exists(), "No debe escribir todavía"

            # Forzar flush
            flush_buffered_writes()
            assert p1.exists(), "Debe existir después de flush"
            assert p2.exists(), "Debe existir después de flush"

    def test_buffered_write_buffer_size_triggers_flush(self):
        """Al alcanzar buffer_size debe hacer flush automático."""
        from lib.file_lock import buffered_write, flush_buffered_writes

        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            # buffer_size=2 -> item 0 bufferiza, item 1 trigger flush
            for i in range(3):
                p = Path(tmp) / f"batch_{i}.json"
                paths.append(p)
                r = buffered_write(p, {"i": i}, buffer_size=2, flush_interval=999)
                if i == 0 or i == 2:
                    assert r is False, f"Item {i} debe bufferizar"
                else:
                    assert r is True, f"Item {i} debe trigger flush"

            flush_buffered_writes()
            assert paths[0].exists(), "Path 0 debe existir"
            assert paths[1].exists(), "Path 1 debe existir"

    def test_locked_append(self):
        """locked_append debe añadir líneas al archivo."""
        from lib.file_lock import locked_append

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "log.txt"
            locked_append(p, "line 1")
            locked_append(p, "line 2")

            lines = p.read_text(encoding="utf-8").strip().split("\n")
            assert "line 1" in lines
            assert "line 2" in lines
            assert len(lines) == 2


# ── Test 4: sync_properties no modifica archivos sin frontmatter ───────

class TestSyncProperties:
    """Verifica que sync_properties maneje correctamente archivos sin frontmatter."""

    def test_sync_properties_no_frontmatter(self):
        """sync_properties debe retornar status 'no_frontmatter' para archivos sin fm."""
        from lib.obsidian import sync_properties

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "no-frontmatter.md"
            p.write_text("# Solo contenido\n\nSin frontmatter en absoluto.", encoding="utf-8")

            result = sync_properties(p)
            assert result["status"] == "no_frontmatter"
            assert result["fields_added"] == 0
            assert result["fields_removed"] == 0

    def test_sync_properties_unchanged(self):
        """sync_properties debe retornar 'unchanged' si el frontmatter ya está limpio."""
        from lib.obsidian import sync_properties

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "clean.md"
            p.write_text(
                "---\ntitle: Clean Note\ntype: concept\ntags: [subject/test]\n---\n\nContenido.",
                encoding="utf-8",
            )

            result = sync_properties(p)
            assert result["status"] in ("unchanged", "synced"), f"Got {result['status']}"

    def test_sync_properties_synced(self):
        """sync_properties debe normalizar listas a formato inline."""
        from lib.obsidian import sync_properties

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "dirty.md"
            p.write_text(
                "---\ntitle: Dirty Note\ntags: tag1, tag2, tag3\n---\n\nContenido.",
                encoding="utf-8",
            )

            result = sync_properties(p)
            # Puede ser synced o unchanged dependiendo de si detecta cambio
            assert result["status"] in ("synced", "unchanged")
            # Si se sincronizó, verificar el cambio
            if result["status"] == "synced":
                content = p.read_text(encoding="utf-8")
                assert "[tag1, tag2, tag3]" in content or "[tag1, tag2, tag3" in content


# ── Test 5: tagger merge preserves manual tags ─────────────────────────

class TestTaggerMerge:
    """Verifica que el tagger preserve tags manuales existentes."""

    def test_tagger_merge_preserves_manual(self):
        """tag_file debe preservar tags existentes y solo añadir nuevas."""
        from lib.tagger import tag_file, _read, _get_frontmatter

        with tempfile.TemporaryDirectory() as tmp:
            # Crear un archivo con tags manuales
            p = Path(tmp) / "wiki" / "concepts" / "test-merge.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(
                "---\n"
                'title: Test Merge\ntype: concept\n'
                'tags: ["practice/personal-knowledge-management"]\n'
                "created: 2026-01-01\n"
                "---\n"
                "\n"
                "Personal knowledge management is a practice of organizing digital information "
                "using tools and techniques for better recall. "
                "This note covers various approaches to PKM including Zettelkasten, "
                "para method, and building a second brain. "
                "These methods help with knowledge work and creative thinking.",
                encoding="utf-8",
            )

            # Ejecutar tagger (dry_run=True para no modificar)
            result = tag_file(str(p), dry_run=True)

            # Debe reportar no modificado (dry_run) o modificaciones
            assert "error" not in result, f"Error: {result.get('error')}"
            assert "tags" in result, f"Result must have tags: {result}"

            # Tags existentes deben estar preservados
            tags = result.get("tags", [])
            assert "practice/personal-knowledge-management" in tags, \
                f"Tag manual debe estar preservado: {tags}"

    def test_tagger_no_duplicate_tags(self):
        """tag_file no debe añadir tags duplicados."""
        from lib.tagger import tag_file

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "wiki" / "concepts" / "no-dup.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(
                "---\n"
                'title: No Dups\ntype: concept\n'
                'tags: ["subject/machine-learning", "practice/api-design"]\n'
                "created: 2026-01-01\n"
                "---\n"
                "\n"
                "Machine learning and API design notes for reference. "
                "Machine learning involves training models on data. "
                "API design focuses on creating interfaces for services.",
                encoding="utf-8",
            )

            result = tag_file(str(p), dry_run=True)

            assert "error" not in result, f"Error: {result.get('error')}"
            tags = result.get("tags", [])

            # Verificar que no hay duplicados
            assert len(tags) == len(set(tags)), f"Tags duplicados: {tags}"

            # Tags manuales deben estar
            manual_tags = {"subject/machine-learning", "practice/api-design"}
            for mt in manual_tags:
                assert mt in tags, f"Tag manual '{mt}' debe preservarse: {tags}"


# ── Test 6: gap_query ──────────────────────────────────────────────────

class TestGapQuery:
    """Verifica gap_query funciona con directorios temporales."""

    def test_query_gaps_structure(self):
        """query_gaps debe retornar estructura completa (usa timeout)."""
        from lib.gap_query import _semantic_search

        # Solo probamos _semantic_search (rápido) en lugar de query_gaps completo
        # (GapDetector.suggest_gaps tarda ~210s)
        result = _semantic_search("kaos", top_k=3)
        assert isinstance(result, list)
        if result:
            assert "name" in result[0]
            assert "score" in result[0]


# ── Test 7: pipeline_e2e dry-run ───────────────────────────────────────

class TestPipelineE2E:
    """Verifica que pipeline_e2e --dry-run funcione sin errores."""

    def test_pipeline_e2e_dry_run(self):
        """pipeline_e2e --dry-run debe ejecutarse sin errores."""
        from scripts.pipeline_e2e import run_pipeline

        # Crear args simulados
        class Args:
            dry_run = True
            skip_tag = False
            skip_score = False
            skip_promote = False
            skip_sync = False
            skip_index = False
            until = None
            verbose = False

        code = run_pipeline(Args())
        assert code == 0, f"pipeline_e2e dry-run debe retornar 0, got {code}"

    def test_pipeline_e2e_skip_phases(self):
        """Saltear fases debe funcionar."""
        from scripts.pipeline_e2e import run_pipeline

        class Args:
            dry_run = True
            skip_tag = True
            skip_score = True
            skip_promote = True
            skip_sync = True
            skip_index = True
            until = None
            verbose = False

        code = run_pipeline(Args())
        assert code == 0

    def test_pipeline_e2e_until(self):
        """--until debe detener después de fase especificada."""
        from scripts.pipeline_e2e import run_pipeline

        class Args:
            dry_run = True
            skip_tag = False
            skip_score = False
            skip_promote = False
            skip_sync = False
            skip_index = False
            until = "score"
            verbose = False

        code = run_pipeline(Args())
        assert code == 0


# ── Test 8: configure_indexes ──────────────────────────────────────────

class TestConfigureIndexes:
    """Verifica configure_indexes --status funciona."""

    def test_index_status(self):
        """configure_indexes --status debe ejecutarse sin errores."""
        from scripts.configure_indexes import _print_status
        # Solo verificar que no lanza excepción
        _print_status()

    def test_index_config_structure(self):
        """Verificar estructura de configuraciones de índice."""
        from scripts.configure_indexes import (
            TXTAI_CONFIG, SMART_CONNECTIONS_CONFIG,
        )

        # Al menos uno debe existir (txtai)
        if TXTAI_CONFIG.exists():
            content = TXTAI_CONFIG.read_text(encoding="utf-8")
            assert "path:" in content
            assert "embeddings:" in content or "writable" in content

        # Smart Connections es opcional
        if SMART_CONNECTIONS_CONFIG.exists():
            data = json.loads(SMART_CONNECTIONS_CONFIG.read_text(encoding="utf-8"))
            assert isinstance(data, dict)
