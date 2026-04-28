import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "sync_metrics_streaks.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "metrics.yml"


def load_module():
    spec = importlib.util.spec_from_file_location("sync_metrics_streaks", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SyncMetricsStreaksTests(unittest.TestCase):
    def test_metrics_workflow_runs_streak_sync_script(self):
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("Sync metrics streak summary", workflow_text)
        self.assertIn("python3 scripts/sync_metrics_streaks.py github-metrics.svg", workflow_text)

    def test_compute_streak_counts_consecutive_non_zero_days(self):
        module = load_module()

        streak = module.compute_streak(
            [
                {"date": "2026-04-16", "contributionCount": 0},
                {"date": "2026-04-17", "contributionCount": 22},
                {"date": "2026-04-18", "contributionCount": 19},
                {"date": "2026-04-19", "contributionCount": 8},
                {"date": "2026-04-20", "contributionCount": 2},
                {"date": "2026-04-21", "contributionCount": 11},
                {"date": "2026-04-22", "contributionCount": 6},
                {"date": "2026-04-23", "contributionCount": 2},
            ]
        )

        self.assertEqual(streak["current"], 7)
        self.assertEqual(streak["max"], 7)

    def test_sync_streak_labels_rewrites_only_streak_values(self):
        module = load_module()
        sample_svg = """
<h3 class="field">Commits streaks</h3>
<div class="field">Current streak 7 days</div>
<div class="field">Best streak 20 days</div>
<div class="field">Highest in a day at 80</div>
"""

        updated_svg = module.sync_streak_labels(sample_svg, current_streak=11, max_streak=20)

        self.assertIn("Current streak 11 days", updated_svg)
        self.assertIn("Best streak 20 days", updated_svg)
        self.assertIn("Highest in a day at 80", updated_svg)


if __name__ == "__main__":
    unittest.main()
