from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from src.core.task_contracts import RunPlan, TaskStep
from src.core.task_runner import RunnerCallbacks, TaskRunner


class TaskWorker(QThread):
    log_signal = pyqtSignal(str)
    step_progress = pyqtSignal(int, int, str)
    total_progress = pyqtSignal(int)
    status_changed = pyqtSignal(str, str)
    finished = pyqtSignal(bool, str, str)

    def __init__(self, config_manager, run_plan: RunPlan):
        super().__init__()
        self.runner = TaskRunner(config_manager, run_plan)

    def stop(self):
        self.runner.cancel()

    def run(self):
        callbacks = RunnerCallbacks(
            log=self.log_signal.emit,
            step_progress=self.step_progress.emit,
            total_progress=self.total_progress.emit,
            status_changed=self._emit_status,
        )
        report = self.runner.run(callbacks)
        self.finished.emit(report.overall_success, report.message, report.report_body)

    def _emit_status(self, step: TaskStep, status):
        self.status_changed.emit(step.value, status.value)
