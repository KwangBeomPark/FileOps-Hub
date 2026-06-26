import unittest
from unittest.mock import patch

from src.core.task_contracts import RunPlan, SyncGroupConfig, SyncRunConfig, TaskStep
from src.core.task_runner import TaskRunner


class FakeConfig:
    def get(self, _key, default=None):
        return default


class FakeSyncManagerSuccess:
    def __init__(self, folders, move_to_deleted=True):
        self.folders = folders
        self.move_to_deleted = move_to_deleted

    def analyze_sync(self):
        return [{"filename": "a.txt"}]

    def execute_sync(self, _actions):
        return 1, 0, []


class FakeSyncManagerPartial(FakeSyncManagerSuccess):
    def execute_sync(self, _actions):
        return 0, 1, ["copy failed"]


class TaskRunnerTests(unittest.TestCase):
    def test_sync_success_report(self):
        plan = RunPlan({TaskStep.SYNC: SyncRunConfig([SyncGroupConfig("g", ["a", "b"])])})
        with patch("src.core.task_runner.SyncManager", FakeSyncManagerSuccess):
            report = TaskRunner(FakeConfig(), plan).run()

        self.assertTrue(report.overall_success)
        self.assertIn("Folder Sync", report.report_body)
        self.assertIn("1 / 1", report.report_body)

    def test_sync_partial_failure_report(self):
        plan = RunPlan({TaskStep.SYNC: SyncRunConfig([SyncGroupConfig("g", ["a", "b"])])})
        with patch("src.core.task_runner.SyncManager", FakeSyncManagerPartial):
            report = TaskRunner(FakeConfig(), plan).run()

        self.assertFalse(report.overall_success)
        self.assertIn("일부 실패", report.report_body)
        self.assertIn("copy failed", "\n".join(report.results[TaskStep.SYNC].details))


if __name__ == "__main__":
    unittest.main()
