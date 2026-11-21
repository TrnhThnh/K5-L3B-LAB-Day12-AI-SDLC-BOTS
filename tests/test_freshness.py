"""Contract v1.2 boundary and reservation checks through the headless CLI."""
import unittest

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


def fish(ident, fresh):
    return {"id": ident, "kind": "ca_loc", "fresh": fresh}


def customer(ident, table, **overrides):
    return {"id": ident, "dish_id": "ca_loc_nuong_trui", "table_id": table, **overrides}


class Freshness(unittest.TestCase):
    def simulate(self, mode, block, ticks, inputs=(), expected=0):
        with Workdir() as w:
            code, err = run_headless("--mode", mode, "--seed", "7", "--ticks", str(ticks),
                "--snapshot-every", "1", "--scenario", write_json(w.path("s"), {mode: block}),
                "--inputs", write_json(w.path("i"), {"frames": list(inputs)}), "--out", w.path("o"))
            self.assertEqual(code, expected, err)
            return read_jsonl(w.path("o")) if code == 0 else []

    def test_threshold_is_strict_one_event_per_item(self):
        rows = self.simulate("gather", {"hold": [fish("I10", 30), fish("I2", 30), fish("I3", 30 + 1/120)],
            "monsters": [], "random_fish": False}, 3)
        self.assertEqual([(e["tick"], e["data"]["item_id"]) for e in events(rows, "spoiled")],
                         [(1, "I2"), (1, "I10"), (2, "I3")])
        self.assertEqual(snapshots(rows)[1]["hold"][2]["fresh"], 30)

    def test_spoiled_reservations_reallocated_before_cooking(self):
        stock = [fish("I10", 30), fish("I2", 30), fish("I9", 80)]
        customers = [customer("C1", "T1", reserved=["I10"], order_tick=1),
                     customer("C2", "T2", reserved=["I2"], order_tick=0)]
        rows = self.simulate("quan", {"stock": stock, "customers": customers, "player": {"pos": [2, 8]}},
                             1, [{"tick": 0, "interact": True}])
        self.assertEqual([e["name"] for e in events(rows)], ["spoiled", "spoiled", "cook_started"])
        cook = events(rows)[-1]["data"]
        self.assertEqual((cook["order_id"], cook["items"][0]["id"]), ("C2", "I9"))
        self.assertEqual(snapshots(rows)[-1]["customers"][0]["order_status"], "unfulfillable")

    def test_automatic_reservations_and_conflicts(self):
        stock = [fish("I2", 95), fish("I1", 95), fish("I3", 80)]
        customers = [customer("C1", "T2"), customer("C2", "T1")]
        snap = snapshots(self.simulate("quan", {"stock": stock, "customers": customers}, 0))[0]
        self.assertEqual([c["reserved"] for c in snap["customers"]], [["I2"], ["I1"]])
        for bad in (["I2", "I2"], ["missing"], ["I1"]):
            conflict = [customer("C1", "T1", reserved=["I1"]), customer("C2", "T2", reserved=bad)]
            self.simulate("quan", {"stock": stock, "customers": conflict}, 0, expected=2)

    def test_invalid_inventory_files_exit_two(self):
        for items in ({"ca_loc": 1}, [fish("I1", 101)], [fish("I1", 30), fish("I1", 90)],
                      [fish("", 50)], [fish("I1", float("nan"))], [dict(fish("I1", 50), kind="x")]):
            with Workdir() as w:
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                    "--inventory", write_json(w.path("inv"), {"items": items}), "--out", w.path("o"))
                self.assertEqual(code, 2)

    def test_price_locks_at_cook_start_and_uses_each_ingredient(self):
        dish = "goi_bong_sung"
        stock = [dict(fish("I10", 80 + 1/240), kind="bong_sung"),
                 dict(fish("I2", 70 + 1/240), kind="bong_sung")]
        rows = self.simulate("quan", {"stock": stock, "player": {"pos": [2, 8]},
            "customers": [customer("C1", "T1", dish_id=dish)], "random_customers": False},
            241, [{"tick": 0, "interact": True}])
        cooked = events(rows, "cook_started")[0]["data"]
        self.assertEqual([i["id"] for i in cooked["items"]], ["I2", "I10"])
        self.assertEqual(cooked["base_price"], 30)
        self.assertEqual(snapshots(rows)[-1]["stoves"][0]["dish"]["base_price"], 30)
