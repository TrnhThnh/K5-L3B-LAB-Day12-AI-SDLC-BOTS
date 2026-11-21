"""Black-box checks for the evening shift."""
import json
import unittest
from pathlib import Path

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json

TUNING = json.loads(Path("game.contract.json").read_text(encoding="utf8"))["tuning"]
Q = TUNING["quan"]
DISH = "ca_loc_nuong_trui"
ITEM = TUNING["menu"][DISH]
CUSTOMER = {"id": "C7", "table_id": "T1", "dish_id": DISH}


class QuanRules(unittest.TestCase):
    def simulate(self, block, ticks, inputs=(), expected=0):
        with Workdir() as w:
            output = w.path("log")
            code, err = run_headless("--mode", "quan", "--seed", "7", "--ticks", str(ticks),
                "--scenario", write_json(w.path("scenario"), {"quan": block}),
                "--inputs", write_json(w.path("inputs"), frames(*inputs)), "--out", output)
            self.assertEqual(code, expected, err)
            return read_jsonl(output) if expected == 0 else []

    def test_arrival_schedule_and_no_dish(self):
        first = Q["first_customer_tick"]
        second = first + round(Q["customer_interval_s"] * 60)
        rows = self.simulate({}, second)
        self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [first, second])
        rows = self.simulate({"stock": ITEM["recipe"]}, second)
        self.assertEqual(len(snapshots(rows)[-1]["customers"]), 1)
        self.assertEqual(snapshots(rows)[-1]["customers"][0]["reserved"], ITEM["recipe"])

    def test_expiry_releases_stock_for_next_customer(self):
        first = Q["first_customer_tick"]
        rows = self.simulate({"stock": ITEM["recipe"], "reputation": Q["reputation_min"],
            "customers": [dict(CUSTOMER, patience_ticks_left=first)]}, first)
        self.assertEqual(events(rows, "customer_left")[0]["tick"], first)
        end = snapshots(rows)[-1]
        self.assertEqual(end["customers"][0]["id"], "C8")
        self.assertEqual(end["reputation"], Q["reputation_min"])
        self.assertEqual(end["stock"], ITEM["recipe"])

    def test_cook_ready_pick_serve_pay_and_close(self):
        cook = round(ITEM["cook_s"] * 60)
        serve = cook + 25
        end = serve + 1 + round(Q["eat_s"] * 60)
        block = {"random_customers": False, "customers": [CUSTOMER], "stock": ITEM["recipe"],
                 "player": {"pos": [2, 8]}, "tables": [{"id": "T1", "pos": [4, 8]}],
                 "time_left_ticks": end}
        inputs = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                  {"tick": cook, "interact": True}, {"tick": cook + 1, "interact": False, "move": [1, 0]},
                  {"tick": serve, "interact": True, "move": [0, 0]}]
        rows = self.simulate(block, end, inputs)
        self.assertEqual([(e["name"], e["tick"]) for e in events(rows)], [
            ("cook_started", 1), ("dish_ready", cook + 1), ("dish_picked", cook + 1),
            ("served", serve + 1), ("paid", end), ("quan_end", end)])
        amount = ITEM["price"] + round(ITEM["price"] * Q["tip_rate"])
        data = events(rows, "quan_end")[0]["data"]
        for key in ("earned", "shift_earned", "money"):
            self.assertEqual(data[key], amount)
        self.assertEqual(data["reputation"], Q["reputation_initial"] + Q["tip_reputation"])
        self.assertEqual(snapshots(rows)[-1]["stock"], {})

    def test_tip_boundary(self):
        threshold = round(Q["patience_s"] * 60 * Q["tip_min_patience_ratio"])
        for patience, qualifies in ((threshold, False), (threshold + 1, True)):
            with self.subTest(patience=patience):
                rows = self.simulate({"hand": DISH, "player": {"pos": Q["tables"][0]["pos"]},
                    "customers": [dict(CUSTOMER, state="assigned", patience_ticks_left=patience)]},
                    1, [{"tick": 0, "interact": True}])
                tip = snapshots(rows)[-1]["customers"][0]["tip"]
                self.assertEqual(tip, round(ITEM["price"] * Q["tip_rate"]) if qualifies else 0)

    def test_tie_selects_stove_and_distance_limits_interact(self):
        for pos, starts in (([2, 8], 1), ([8, 5], 0)):
            rows = self.simulate({"stock": ITEM["recipe"], "customers": [CUSTOMER],
                "tables": [{"id": "T1", "pos": [2, 8]}], "player": {"pos": pos}},
                1, [{"tick": 0, "interact": True}])
            self.assertEqual(len(events(rows)), starts)
            self.assertEqual(len(events(rows, "cook_started")), starts)

    def test_close_pays_eaters_and_releases_waiting_orders(self):
        rows = self.simulate({"time_left_ticks": 1, "customers": [
            dict(CUSTOMER, state="eating", eat_ticks_left=50, price=60, tip=12)]}, 1)
        self.assertEqual([e["name"] for e in events(rows)], ["paid", "quan_end"])
        self.assertEqual(snapshots(rows)[-1]["shift_earned"], 72)
        for patience in (1, 50):
            rows = self.simulate({"time_left_ticks": 1, "stock": ITEM["recipe"],
                "customers": [dict(CUSTOMER, patience_ticks_left=patience)]}, 1)
            end = snapshots(rows)[-1]
            self.assertEqual(end["customers"], [])
            self.assertEqual(end["available_stock"], ITEM["recipe"])
            self.assertEqual(end["reputation"], Q["reputation_initial"])

    def test_close_discards_assigned_dish(self):
        for source in ({"hand": DISH}, {"stoves": [{"id": "B1", "state": "ready", "dish": DISH}]}):
            rows = self.simulate(dict(source, time_left_ticks=1,
                customers=[dict(CUSTOMER, state="assigned")]), 1)
            end = snapshots(rows)[-1]
            self.assertIsNone(end["hand"])
            self.assertEqual(end["stoves"][0]["state"], "idle")
            self.assertFalse(end["customers"])

    def test_invalid_scenario_returns_two(self):
        for c in (CUSTOMER, dict(CUSTOMER, state="assigned"), dict(CUSTOMER, state="eating")):
            with self.subTest(customer=c):
                self.simulate({"customers": [c]}, 1, expected=2)
