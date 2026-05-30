import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["KAOS_TESTING"] = "1"

import strategy_feedback


def test_dispatch_creates_file(tmp_path):
    strategy_feedback.TRANSFERS_DIR = tmp_path
    result = strategy_feedback.dispatch_strategy("T-OKR1", "Test initiative", {"latency": "<100ms"})
    assert result is not None
    transfer_file = tmp_path / "T-OKR1.json"
    assert transfer_file.exists()
    data = json.loads(transfer_file.read_text(encoding="utf-8"))
    assert data["okr_id"] == "T-OKR1"
    assert data["initiative_title"] == "Test initiative"
    assert data["status"] == "dispatched"


def test_poll_pending(tmp_path):
    strategy_feedback.TRANSFERS_DIR = tmp_path
    strategy_feedback.dispatch_strategy("T-OKR2", "Pending initiative")
    state = strategy_feedback.poll_feedback("T-OKR2")
    assert state is None


def test_feedback_updates_status(tmp_path):
    strategy_feedback.TRANSFERS_DIR = tmp_path
    strategy_feedback.dispatch_strategy("T-OKR3", "Feedback initiative", {"coverage": ">80%"})
    strategy_feedback.submit_feedback("T-OKR3", "completed", {"coverage": 85, "latency": 150})
    state = strategy_feedback.poll_feedback("T-OKR3")
    assert state is not None
    assert state.get("completion", {}).get("status") == "completed"
    assert state["status"] == "feedback_received"


def test_generate_report_returns_md(tmp_path):
    strategy_feedback.TRANSFERS_DIR = tmp_path
    strategy_feedback.dispatch_strategy("T-OKR4", "Report initiative")
    strategy_feedback.submit_feedback("T-OKR4", "partial", {"coverage": 60})
    report = strategy_feedback.generate_report("T-OKR4")
    assert report.startswith("# Strategy Feedback Report")
    assert "T-OKR4" in report
    assert "Report initiative" in report


def test_list_initiatives(tmp_path):
    strategy_feedback.TRANSFERS_DIR = tmp_path
    strategy_feedback.dispatch_strategy("T-OKR5", "List initiative A")
    strategy_feedback.dispatch_strategy("T-OKR6", "List initiative B")
    items = strategy_feedback.list_initiatives()
    assert len(items) >= 2
    titles = [i["initiative"] for i in items]
    assert "List initiative A" in titles
    assert "List initiative B" in titles


def test_cli_help():
    try:
        strategy_feedback.main()
    except SystemExit as e:
        assert e.code in (0, 2)
    except Exception:
        pass
