"""Test luật quán (PRD-0 mục F "Quán"), kiểu HỘP ĐEN qua headless_cmd. Số đọc từ game.contract.json.
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_quan_rules -v
"""

import json
import math
import unittest

from helpers import individuals

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def T():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


def Q():
    return T()["quan"]


def ticks(s):
    return int(round(s * 60))


def run(w, block, n, inputs=None, every=1):
    args = ["--mode", "quan", "--seed", "3", "--ticks", str(n), "--snapshot-every", str(every),
            "--scenario", write_json(w.path("sc.json"), {"quan": block}), "--out", w.path("o.jsonl")]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    assert code == 0, err
    rows = read_jsonl(w.path("o.jsonl"))
    return rows, {s["tick"]: s for s in snapshots(rows)}


def code_of(w, block):
    return run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--out", w.path("o.jsonl"),
                        "--scenario", write_json(w.path("sc.json"), {"quan": block}))[0]


STOVE = Q()["stoves"][0]
TABLE = Q()["tables"][0]
DISH = "ca_loc_nuong_trui"


def payload(order_id="C1"):
    return {"order_id": order_id, "dish_id": DISH, "base_price": T()["menu"][DISH]["price"]}


class Customers(unittest.TestCase):
    def test_first_customer_reserves_recipe(self):
        first = Q()["first_customer_tick"]
        with Workdir() as w:
            rows, s = run(w, {"stock": individuals({"bong_sung": 2})}, first + 1, every=first)
            ev = events(rows, "customer_arrived")
            self.assertEqual([e["tick"] for e in ev], [first])
            self.assertEqual(ev[0]["data"], {"order_id": "C1", "table_id": TABLE["id"], "dish_id": "goi_bong_sung"})
            c = s[first]["customers"][0]
            self.assertEqual((c["order_status"], c["reserved"], c["order_tick"]), ("reserved", ["I1", "I2"], first))
            self.assertEqual(c["patience_ticks_left"], ticks(Q()["patience_s"]))
            self.assertEqual(s[first]["tables"][0]["customer_id"], "C1")
            self.assertEqual(s[first + 1]["customers"][0]["patience_ticks_left"], ticks(Q()["patience_s"]) - 1)

    def test_no_dish_when_nothing_cookable(self):
        first = Q()["first_customer_tick"]
        with Workdir() as w:
            rows, s = run(w, {}, first, every=first)
            self.assertEqual([(e["tick"], e["data"]) for e in events(rows)], [(first, {})])
            self.assertEqual(events(rows)[0]["name"], "no_dish")
            self.assertEqual(s[first]["customers"], [])

    def test_no_free_table_skips_turn(self):
        first = Q()["first_customer_tick"]
        tables = Q()["tables"]
        custs = [{"id": f"C{i}", "table_id": tb["id"], "dish_id": "goi_bong_sung"} for i, tb in enumerate(tables, 1)]
        with Workdir() as w:
            rows, _ = run(w, {"stock": individuals({"bong_sung": 2 * len(tables) + 2}), "customers": custs}, first, every=first)
            self.assertEqual(events(rows), [], "mọi bàn đều có khách thì bỏ lượt")

    def test_second_customer_takes_next_table(self):
        first, every = Q()["first_customer_tick"], ticks(Q()["customer_interval_s"])
        with Workdir() as w:
            rows, _ = run(w, {"stock": individuals({"bong_sung": 4})}, first + every, every=first + every)
            ev = events(rows, "customer_arrived")
            self.assertEqual([(e["tick"], e["data"]["table_id"]) for e in ev],
                             [(first, Q()["tables"][0]["id"]), (first + every, Q()["tables"][1]["id"])])

    def test_patience_runs_out(self):
        with Workdir() as w:
            sc = {"stock": individuals({"ca_loc": 1}), "random_customers": False,
                  "customers": [{"id": "C1", "table_id": TABLE["id"], "dish_id": DISH, "patience_ticks_left": 5}]}
            rows, s = run(w, sc, 6)
            ev = events(rows, "customer_left")
            want_rep = Q()["reputation_initial"] + Q()["left_reputation_delta"]
            self.assertEqual([(e["tick"], e["data"]) for e in ev],
                             [(5, {"order_id": "C1", "table_id": TABLE["id"], "reason": "patience", "reputation": want_rep})])
            self.assertEqual(s[5]["customers"], [])
            self.assertEqual(s[5]["stock"], individuals(["ca_loc"], 100 - 5 / 240), "phần giữ được nhả, kho vật lý giữ nguyên")


class Kitchen(unittest.TestCase):
    def test_cook_ready_pick(self):
        cook = ticks(T()["menu"][DISH]["cook_s"])
        with Workdir() as w:
            sc = {"stock": individuals({"ca_loc": 1}), "random_customers": False, "player": {"pos": STOVE["pos"]},
                  "customers": [{"id": "C1", "table_id": TABLE["id"], "dish_id": DISH}]}
            inputs = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}, {"tick": cook + 5, "interact": True}]
            rows, s = run(w, sc, cook + 7, inputs=inputs)
            cs = events(rows, "cook_started")[0]
            self.assertEqual(cs["data"], {"stove_id": STOVE["id"], "order_id": "C1", "dish_id": DISH,
                                          "items": individuals(["ca_loc"], 100 - 1 / 240), "base_price": T()["menu"][DISH]["price"] - 1})
            self.assertEqual(s[1]["stock"], [], "nguyên liệu giữ đã tiêu")
            self.assertEqual(s[1]["customers"][0]["order_status"], "assigned")
            self.assertEqual(s[1]["stoves"][0]["cook_ticks_left"], cook)
            self.assertEqual([e["tick"] for e in events(rows, "dish_ready")], [1 + cook])
            self.assertEqual(s[cook + 5]["stoves"][0]["ready_ticks"], 4)
            self.assertEqual([e["tick"] for e in events(rows, "dish_picked")], [cook + 6])
            self.assertEqual(s[cook + 6]["hand"], dict(payload(), base_price=T()["menu"][DISH]["price"] - 1))
            self.assertEqual(s[cook + 6]["stoves"][0]["state"], "idle")

    def test_idle_stove_without_order_does_nothing(self):
        with Workdir() as w:
            rows, _ = run(w, {"random_customers": False, "player": {"pos": STOVE["pos"]}}, 1,
                          inputs=[{"tick": 0, "interact": True}])
            self.assertEqual(events(rows), [])


class Serving(unittest.TestCase):
    def served_scn(self, patience):
        return {"random_customers": False, "player": {"pos": TABLE["pos"]}, "hand": payload(),
                "customers": [{"id": "C1", "table_id": TABLE["id"], "dish_id": DISH, "order_status": "assigned",
                               "patience_ticks_left": patience}]}

    def test_serve_eat_pay_with_tip(self):
        price = T()["menu"][DISH]["price"]
        tip = math.floor(price * Q()["tip_rate"])
        eat = ticks(Q()["eat_s"])
        full = ticks(Q()["patience_s"])
        with Workdir() as w:
            rows, s = run(w, self.served_scn(full), eat + 2, inputs=[{"tick": 0, "interact": True}])
            sv = events(rows, "served")[0]
            self.assertEqual(sv["data"], {"order_id": "C1", "table_id": TABLE["id"], "dish_id": DISH,
                                          "patience_ticks_left": full - 1, "base_price": price, "tip": tip})
            self.assertIsNone(s[1]["hand"])
            paid = events(rows, "paid")[0]
            self.assertEqual(paid["tick"], 1 + eat)
            self.assertEqual(paid["data"], {"order_id": "C1", "table_id": TABLE["id"], "base_price": price,
                                            "tip": tip, "amount": price + tip, "reason": "finished_eating"})
            end = s[1 + eat]
            rep = Q()["reputation_initial"] + Q()["tip_reputation"]
            self.assertEqual((end["money"], end["earned"]), (price + tip, price + tip))
            self.assertAlmostEqual(end["reputation"], rep, places=2)
            self.assertEqual(end["score"], price + tip + T()["score"]["reputation_multiplier"] * math.floor(rep))
            self.assertEqual(end["customers"], [])

    def test_no_tip_below_ratio(self):
        full = ticks(Q()["patience_s"])
        low = int(full * Q()["tip_min_patience_ratio"])  # sau bước 1 còn low - 1 < ngưỡng
        with Workdir() as w:
            rows, _ = run(w, self.served_scn(low), 1, inputs=[{"tick": 0, "interact": True}])
            self.assertEqual(events(rows, "served")[0]["data"]["tip"], 0)

    def test_hand_without_matching_order_exit_2(self):
        sc = self.served_scn(100)
        sc["hand"] = payload("C9")
        with Workdir() as w:
            self.assertEqual(code_of(w, sc), 2, "món trên tay không khớp đơn nào là mâu thuẫn")


class Closing(unittest.TestCase):
    def test_closing_pays_eaters_and_releases_waiters(self):
        price = T()["menu"][DISH]["price"]
        tables = Q()["tables"]
        sc = {"random_customers": False, "time_left_ticks": 3, "stock": individuals({"ca_loc": 1}),
              "customers": [{"id": "C1", "table_id": tables[0]["id"], "dish_id": DISH, "state": "eating",
                             "order_status": "served", "eat_ticks_left": 500, "base_price": price, "tip": 0}]}
        with Workdir() as w:
            rows, _ = run(w, sc, 10)
            self.assertEqual([e["name"] for e in events(rows)], ["paid", "quan_end"])
            self.assertEqual(events(rows, "paid")[0]["data"]["reason"], "closing")
            self.assertEqual(events(rows, "quan_end")[0]["data"],
                             {"reason": "time", "money": price, "earned": price, "shift_earned": price,
                              "reputation": Q()["reputation_initial"]})
            self.assertEqual(rows[-1]["reason"], "time")

    def test_waiting_customer_leaves_without_penalty_at_close(self):
        sc = {"random_customers": False, "time_left_ticks": 2, "stock": individuals({"ca_loc": 1}),
              "customers": [{"id": "C1", "table_id": TABLE["id"], "dish_id": DISH}]}
        with Workdir() as w:
            rows, _ = run(w, sc, 5)
            left = events(rows, "customer_left")[0]["data"]
            self.assertEqual((left["reason"], left["reputation"]), ("closing", Q()["reputation_initial"]))


class Fixtures(unittest.TestCase):
    def test_conflicts_exit_2(self):
        bad = [
            {"stock": individuals({}), "customers": [{"id": "C1", "table_id": TABLE["id"], "dish_id": DISH}]},  # giữ quá tồn
            {"stock": individuals({"ca_loc": 1}), "customers": [{"id": "C1", "table_id": TABLE["id"], "dish_id": DISH,
                                                    "order_status": "assigned"}]},  # assigned không có món
            {"customers": [{"id": "C1", "table_id": TABLE["id"], "dish_id": "pho_bo"}]},  # món ngoài phạm vi
            {"customers": [{"id": "C1", "table_id": TABLE["id"], "dish_id": DISH, "state": "eating",
                            "order_status": "served", "eat_ticks_left": 0, "base_price": 60}]},
        ]
        for block in bad:
            with Workdir() as w:
                self.assertEqual(code_of(w, block), 2, block)


class FullShift(unittest.TestCase):
    def test_full_shift_deterministic(self):
        inputs = [{"tick": 0, "move": [-1, 1]}, {"tick": 125, "move": [0, 0], "interact": True},
                  {"tick": 126, "interact": False}]
        out = []
        for _ in range(2):
            with Workdir() as w:
                rows, _ = run(w, {"stock": individuals({"ca_loc": 2, "bong_sung": 4})}, 10800, inputs=inputs, every=60)
                self.assertEqual(rows[-1]["reason"], "time")
                with open(w.path("o.jsonl"), "rb") as f:
                    out.append(f.read())
        self.assertEqual(out[0], out[1])


if __name__ == "__main__":
    unittest.main()
