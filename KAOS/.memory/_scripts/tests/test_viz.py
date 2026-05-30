"""Tests for lib.viz — Mermaid visualization generation."""
import sys, os
import tempfile
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_viz_module_loads():
    import lib.viz
    assert hasattr(lib.viz, "generate_all")


def test_viz_generate_all():
    from lib.viz import generate_all
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        result = generate_all(output_dir=tmp_path)
        assert isinstance(result, list)
        for f in result:
            assert os.path.exists(f)
            assert str(f).endswith(".md")


def test_viz_output_content():
    from lib.viz import generate_all
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        result = generate_all(output_dir=tmp_path)
        for fpath in result:
            content = open(fpath, encoding="utf-8").read()
            assert "```mermaid" in content
