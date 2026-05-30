"""Tests for Parallel Workers — task management, execution, integration."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_worker_initialization():
    from lib.parallel_worker import ParallelWorker
    worker = ParallelWorker(max_workers=2, branch="main")
    assert worker.max_workers == 2
    assert worker.branch == "main"
    assert len(worker.tasks) == 0


def test_add_task():
    from lib.parallel_worker import ParallelWorker
    worker = ParallelWorker()
    task = worker.add_task("src/test.py", "Test task", "Write a test")
    assert task.task_id == "task-1"
    assert "src" in str(task.file_path) and "test.py" in str(task.file_path)
    assert len(worker.tasks) == 1


def test_add_multiple_tasks():
    from lib.parallel_worker import ParallelWorker
    worker = ParallelWorker()
    worker.add_task("a.py", "Task A", "Code A")
    worker.add_task("b.py", "Task B", "Code B")
    worker.add_task("c.py", "Task C", "Code C")
    assert len(worker.tasks) == 3


def test_status_empty():
    from lib.parallel_worker import ParallelWorker
    worker = ParallelWorker()
    s = worker.status()
    assert s["total_tasks"] == 0
    assert s["max_workers"] == 3


def test_status_with_tasks():
    from lib.parallel_worker import ParallelWorker
    worker = ParallelWorker(max_workers=2)
    worker.add_task("f1.py", "Task 1", "Code 1")
    s = worker.status()
    assert s["total_tasks"] == 1
    assert s["max_workers"] == 2


def test_worker_task_attributes():
    from lib.parallel_worker import WorkerTask
    task = WorkerTask(
        task_id="test-1",
        file_path="/tmp/test.py",
        description="Test description",
        prompt="Write test code"
    )
    assert task.task_id == "test-1"
    assert task.description == "Test description"
    assert task.prompt == "Write test code"
    assert task.result is None
    assert task.error is None
    assert task.duration == 0.0
