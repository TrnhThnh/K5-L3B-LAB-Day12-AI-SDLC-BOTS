"""Test bench_cmd (Ticket-04 mục 1): chạy qua lệnh khai trong game.contract.json, kiểm 5 trường của bench.json.
Chạy ngắn (--duration 1) để test nhanh; số đo thật lưu ở docs/proof/phase-4/bench.json.
"""

import json
import os
import shlex
import subprocess
import unittest

from helpers import ROOT, Workdir


def contract():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


class Bench(unittest.TestCase):
    def test_contract_declares_v13_commands(self):
        c = contract()
        self.assertEqual(c["contract_version"], "1.3")
        for key in ("bench_cmd", "soak_cmd", "run_cmd", "headless_cmd", "build_cmd"):
            self.assertTrue(c.get(key), key)

    def test_bench_writes_five_fields(self):
        with Workdir() as w:
            out = w.path("bench.json")
            png = w.path("frame.png")
            cmd = [*shlex.split(contract()["bench_cmd"]), "--seed", "42", "--duration", "1", "--out", out,
                   "--frame-out", png]
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as f:
                b = json.load(f)
            self.assertEqual(set(b), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
            self.assertGreater(b["frames"], 0)
            self.assertAlmostEqual(b["measured_s"], 1.0, delta=0.2)
            # avg_fps phải tính lại được từ đúng hai trường đã ghi (chỉ lệch do làm tròn 2 chữ số)
            self.assertAlmostEqual(b["avg_fps"], b["frames"] / b["measured_s"], delta=0.006)
            self.assertLessEqual(b["p1_low_fps"], b["avg_fps"] + 0.01, "1% low không thể nhanh hơn trung bình")
            self.assertGreaterEqual(b["load_ms"], 0)
            with open(png, "rb") as f:
                self.assertEqual(f.read(8), b"\x89PNG\r\n\x1a\n", "khung render được ghi ra PNG")

    def test_bad_duration_exit_2(self):
        with Workdir() as w:
            cmd = [*shlex.split(contract()["bench_cmd"]), "--seed", "1", "--duration", "0", "--out", w.path("b.json")]
            self.assertEqual(subprocess.run(cmd, cwd=ROOT, capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
