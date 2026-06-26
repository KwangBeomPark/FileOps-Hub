"""Compatibility exports for the pure task runner.

The QThread adapter lives in src.ui.task_worker. Core execution must remain
PyQt-free so it can be tested and reused by CLI diagnostics.
"""

from src.core.task_runner import RunnerCallbacks, TaskRunner

__all__ = ["RunnerCallbacks", "TaskRunner"]
