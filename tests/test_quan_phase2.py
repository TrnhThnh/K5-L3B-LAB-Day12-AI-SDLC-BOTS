"""Ca kiểm quán Phase 2 (TICKET-02 §1.3) của Thịnh (TrnhThnh), chuyển sang Test Contract v1.2 khi gộp
nhánh `thinh/phase-2-quan-qa` vào main. Bản gốc gọi helper của `test_quan_rules.py` riêng trên nhánh đó
(kho đếm v1.1); bản này chạy hộp đen qua headless_cmd với kho cá thể.

Ca "lọc menu theo kế hoạch Ngày" của bản gốc đã có ở tests/test_day.py::DayLoop.test_plan_filters_menu.
"""

import json
import unittest

from helpers import Workdir, events, frames, individuals, read_jsonl, run_headless, snapshots, write_json


def T():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


def run(w, block, n, inputs=None):
    args = ["--mode", "quan", "--seed", "1", "--ticks", str(n), "--snapshot-every", "1",
            "--scenario", write_json(w.path("sc.json"), {"quan": block}), "--out", w.path("o.jsonl")]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


def customer(cid="C1", table="T1", dish="ca_loc_nuong_trui", order_tick=0):
    return {"id": cid, "table_id": table, "dish_id": dish, "order_tick": order_tick}


class EveningIntegration(unittest.TestCase):
    def test_layout_and_all_six_recipes(self):
        q, menu = T()["quan"], T()["menu"]
        with Workdir() as w:
            snap = snapshots(run(w, {"random_customers": False}, 0))[0]
        self.assertEqual([s["pos"] for s in snap["stoves"]], [s["pos"] for s in q["stoves"]])
        self.assertEqual([t["pos"] for t in snap["tables"]], [t["pos"] for t in q["tables"]])
        self.assertEqual(len(menu), 6)
        b2 = q["stoves"][1]
        for dish, item in menu.items():
            with Workdir() as w:
                rows = run(w, {"random_customers": False, "stock": individuals(item["recipe"]),
                               "customers": [customer(dish=dish)], "player": {"pos": b2["pos"]}},
                           1, [{"tick": 0, "interact": True}])
            cs = events(rows, "cook_started")
            self.assertEqual(len(cs), 1, dish)
            self.assertEqual(cs[0]["data"]["stove_id"], b2["id"], dish)
            self.assertEqual(snapshots(rows)[-1]["stock"], [], dish)

    def test_oldest_order_then_lowest_table(self):
        b1 = T()["quan"]["stoves"][0]
        for tick, expected in ((0, "C2"), (1, "C1")):
            with Workdir() as w:
                rows = run(w, {"random_customers": False, "stock": individuals({"ca_loc": 2}),
                               "customers": [customer(order_tick=1), customer("C2", "T2", order_tick=tick)],
                               "player": {"pos": b1["pos"]}}, 1, [{"tick": 0, "interact": True}])
            self.assertEqual(events(rows, "cook_started")[0]["data"]["order_id"], expected, tick)


if __name__ == "__main__":
    unittest.main()
