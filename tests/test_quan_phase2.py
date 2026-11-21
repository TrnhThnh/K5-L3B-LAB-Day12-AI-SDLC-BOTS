"""Integration checks for TICKET-02 evening configuration and day menu."""
import unittest

from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim
import test_quan_rules as rules
from test_quan_rules import CUSTOMER, TUNING
from helpers import events, snapshots


class EveningIntegration(unittest.TestCase):
    simulate = rules.QuanRules.simulate

    def test_layout_and_all_six_recipes(self):
        rows = self.simulate({}, 1)
        snap = snapshots(rows)[0]
        self.assertEqual([s["pos"] for s in snap["stoves"]], [[2, 8], [5, 8]])
        self.assertEqual([t["pos"] for t in snap["tables"]], [[9, 2], [13, 2], [9, 6], [13, 6]])
        self.assertEqual(len(TUNING["menu"]), 6)
        for dish, item in TUNING["menu"].items():
            rows = self.simulate({"stock": item["recipe"], "customers": [dict(CUSTOMER, dish_id=dish)],
                                  "player": {"pos": [5, 8]}}, 1, [{"tick": 0, "interact": True}])
            self.assertEqual(events(rows, "cook_started")[0]["data"]["stove_id"], "B2")
            self.assertFalse(snapshots(rows)[-1]["stock"])

    def test_oldest_order_then_lowest_table(self):
        for tick, expected in ((0, "C2"), (1, "C7")):
            rows = self.simulate({"stock": {"ca_loc": 2}, "customers": [
                dict(CUSTOMER, order_tick=1), dict(CUSTOMER, id="C2", table_id="T2", order_tick=tick)],
                "player": {"pos": [2, 8]}}, 1, [{"tick": 0, "interact": True}])
            self.assertEqual(events(rows, "cook_started")[0]["data"]["customer_id"], expected)

    def test_daily_plan_filters_orders_but_does_not_cap_servings(self):
        plan = {"dishes": {"ca_keo_nuong": 1}}
        sim = QuanSim(TUNING, {}, Streams(1), IdAllocator(), {"ca_keo": 4, "ca_loc": 4}, day_plan=plan)
        for _ in range(3):
            log = []
            sim._arrive(log)
        self.assertEqual([c["dish_id"] for c in sim.customers], ["ca_keo_nuong"] * 2)
        self.assertEqual(log[0][0], "no_dish")
        with self.assertRaises(BadInput):
            QuanSim(TUNING, {"customers": [CUSTOMER]}, Streams(1), IdAllocator(), {"ca_loc": 1}, day_plan=plan)
