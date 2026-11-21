"""Soak command contract and ten-day progression checks."""

import json
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from chonoi.soak import main


class SoakCommand(unittest.TestCase):
    def test_ten_days_repeat_plan_and_emit_required_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "soak.json"
            code = main(["--seed", "7", "--days", "10", "--out", str(out)])
            self.assertEqual(code, 0)
            report = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(set(report), {"days", "days_completed", "crashes", "results", "duration_s"})
        self.assertEqual((report["days"], report["days_completed"], report["crashes"]), (10, 10, 0))
        self.assertEqual([result["day"] for result in report["results"]], list(range(1, 11)))
        for result in report["results"]:
            self.assertEqual(set(result), {"day", "earned", "reputation", "score"})
        self.assertGreaterEqual(report["duration_s"], 0)

    def test_days_must_be_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            error = StringIO()
            with redirect_stderr(error), self.assertRaises(SystemExit) as raised:
                main(["--seed", "7", "--days", "0", "--out", str(Path(tmp) / "soak.json")])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
