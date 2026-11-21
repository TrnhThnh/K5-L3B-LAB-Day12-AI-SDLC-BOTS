"""Test vòng ngày `--mode day`, Shop và pause (Ticket-02 mục 2, Test Contract v1.1 mục 4), hộp đen qua headless_cmd.
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_day -v
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def T():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


def ticks(s):
    return int(round(s * 60))


def run_day(w, scenario=None, inputs=None, days=None, n=60000, every=600, seed=4):
    args = ["--mode", "day", "--seed", str(seed), "--ticks", str(n), "--snapshot-every", str(every),
            "--out", w.path("o.jsonl")]
    if days is not None:
        args += ["--days", str(days)]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), scenario)]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


# Ví dụ Ticket-02 mục 4.3: có tiền và kho mang về, tương tác ở bến đóng ca sáng ngay.
DOCK = {"day": {"money": 200, "earned": 200},
        "gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False}}
DOCK_IN = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}]
SHOP_AT = 1 + ticks(T()["quan"]["duration_s"])  # tick mở Shop khi cập bến ở tick 1


def names(rows, tick=None):
    return [r["name"] for r in events(rows) if tick is None or r["tick"] == tick]


class DayLoop(unittest.TestCase):
    def test_one_full_day(self):
        g, q, shop = T()["gather"], T()["quan"], T()["shop"]
        with Workdir() as w:
            rows = run_day(w)
            self.assertEqual(names(rows, 0), ["day_start", "day_plan", "phase_start"])
            self.assertEqual(rows[3]["type"], "snapshot", "event tick 0 ghi trước snapshot tick 0")
            plan = events(rows, "day_plan")[0]
            self.assertEqual((plan["day"], plan["phase"]), (1, "gather"))
            d1 = T()["day_plan"][0]
            self.assertEqual(plan["data"], {"dishes": d1["dishes"], "ingredients": d1["ingredients"]})
            total = ticks(g["duration_s"]) + ticks(q["duration_s"]) + shop["max_ticks"]
            end = rows[-1]
            self.assertEqual((end["ticks"], end["reason"], end["days_completed"], end["state"]),
                             (total, "days_complete", 1, "finished"))
            self.assertLessEqual(total, 22200)

    def test_phase_changes_same_tick_and_old_phase_on_end_events(self):
        with Workdir() as w:
            rows = run_day(w, DOCK, DOCK_IN, n=SHOP_AT + 1, every=10000)
            ge = events(rows, "gather_end")[0]
            ps = [e for e in events(rows, "phase_start") if e["tick"] == ge["tick"]]
            self.assertEqual((ge["tick"], ge["phase"], ps[0]["phase"]), (1, "gather", "quan"))
            snap = {s["tick"]: s for s in snapshots(rows)}[1]
            self.assertEqual((snap["phase"], snap["phase_tick"]), ("quan", 0), "snapshot đổi pha ghi pha mới")
            self.assertEqual(snap["stock"], {"bong_sung": 2, "ca_loc": 1}, "kho bàn giao trong bộ nhớ")
            qe = events(rows, "quan_end")[0]
            self.assertEqual((qe["tick"], qe["phase"]), (SHOP_AT, "quan"))
            shop_snap = {s["tick"]: s for s in snapshots(rows)}[SHOP_AT]
            self.assertEqual((shop_snap["phase"], shop_snap["time_left_ticks"]), ("shop", T()["shop"]["max_ticks"]))
            for key in ("day", "day_plan", "upgrades", "active_upgrades"):
                self.assertIn(key, shop_snap)

    def test_plan_filters_menu(self):
        """D1 chỉ có cá lóc nướng trui và gỏi bông súng: kho lẩu cá linh không đủ cho món nào trong kế hoạch."""
        sc = {"gather": {"hold": ["ca_linh", "ca_linh", "ca_linh", "bong_dien_dien"], "random_fish": False}}
        first = T()["quan"]["first_customer_tick"]
        with Workdir() as w:
            rows = run_day(w, sc, DOCK_IN, n=1 + first, every=10000)
            self.assertEqual(names(rows, 1 + first), ["no_dish"])

    def test_faint_still_opens_quan_with_empty_stock(self):
        sc = {"gather": {"random_fish": False, "monsters": [], "hold": ["ca_loc"],
                         "player": {"pos": [50, 15], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59}}}
        with Workdir() as w:
            rows = run_day(w, sc, n=1, every=1)
            self.assertEqual(names(rows, 1), ["choke", "faint", "gather_end", "phase_start"])
            self.assertEqual(snapshots(rows)[-1]["stock"], {})


class Shop(unittest.TestCase):
    def test_buy_rules(self):
        ups = T()["shop"]["upgrades"]
        o1 = ups["oxygen"][0]["price"]
        inputs = DOCK_IN + [{"tick": SHOP_AT, "buy": "oxygen"}, {"tick": SHOP_AT + 1, "buy": "oxygen"},
                            {"tick": SHOP_AT + 2, "buy": "lao"}, {"tick": SHOP_AT + 3, "shop_done": True}]
        with Workdir() as w:
            rows = run_day(w, DOCK, inputs, days=2, n=SHOP_AT + 5, every=1)
            self.assertEqual(events(rows, "bought")[0]["data"],
                             {"upgrade": "oxygen", "level": 1, "price": o1, "money": 200 - o1})
            self.assertEqual([e["data"] for e in events(rows, "buy_failed")],
                             [{"action": "oxygen", "reason": "funds"}, {"action": "lao", "reason": "unknown"}])
            snap = {s["tick"]: s for s in snapshots(rows)}
            self.assertEqual((snap[SHOP_AT + 1]["upgrades"], snap[SHOP_AT + 1]["active_upgrades"]), ({"oxygen": 1}, {}),
                             "cấp vừa mua hiển thị ngay, chưa áp dụng")
            self.assertEqual(snap[SHOP_AT + 1]["earned"], 200, "mua không trừ earned")
            end = SHOP_AT + 4
            self.assertEqual(names(rows, end), ["shop_end", "day_start", "day_plan", "phase_start"])
            self.assertEqual([e["day"] for e in events(rows) if e["tick"] == end], [1, 2, 2, 2])
            s2 = snap[end]
            self.assertEqual((s2["day"], s2["phase"], s2["active_upgrades"]), (2, "gather", {"oxygen": 1}))
            self.assertEqual(s2["player"]["oxygen_max_ticks"], ticks(ups["oxygen"][0]["oxygen_max_s"]))

    def test_max_level_and_hp_upgrade(self):
        ups = T()["shop"]["upgrades"]
        sc = dict(DOCK, day={"money": 2000, "earned": 2000, "upgrades": {"hp": len(ups["hp"]) - 1}})
        inputs = DOCK_IN + [{"tick": SHOP_AT, "buy": "hp"}, {"tick": SHOP_AT + 1, "buy": "hp"},
                            {"tick": SHOP_AT + 2, "shop_done": True}]
        with Workdir() as w:
            rows = run_day(w, sc, inputs, days=2, n=SHOP_AT + 4, every=1)
            self.assertEqual(events(rows, "bought")[0]["data"]["level"], len(ups["hp"]))
            self.assertEqual(events(rows, "buy_failed")[0]["data"], {"action": "hp", "reason": "max_level"})
            last = snapshots(rows)[-1]
            self.assertEqual((last["player"]["hp"], last["player"]["hp_max"]), (ups["hp"][-1]["hp_max"],) * 2)

    def test_exact_price_buys_and_buy_before_shop_done(self):
        price = T()["shop"]["upgrades"]["oxygen"][0]["price"]
        sc = dict(DOCK, day={"money": price, "earned": price})
        inputs = DOCK_IN + [{"tick": SHOP_AT, "buy": "oxygen", "shop_done": True}]
        with Workdir() as w:
            rows = run_day(w, sc, inputs, n=SHOP_AT + 2, every=1)
            self.assertEqual(names(rows, SHOP_AT + 1), ["bought", "shop_end"])
            self.assertEqual(rows[-1]["money"], 0)

    def test_shop_times_out_and_keeps_leftover_stock(self):
        mx = T()["shop"]["max_ticks"]
        with Workdir() as w:
            rows = run_day(w, DOCK, DOCK_IN, n=SHOP_AT + mx, every=10000)
            se = events(rows, "shop_end")[0]
            self.assertEqual((se["tick"], se["data"]), (SHOP_AT + mx, {"reason": "time"}))


class Pause(unittest.TestCase):
    def test_pause_freezes_gameplay(self):
        inputs = [{"tick": 0, "move": [1, 0]}, {"tick": 10, "pause": True}, {"tick": 11, "pause": False},
                  {"tick": 30, "pause": True}]
        with Workdir() as w:
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "40", "--snapshot-every", "1",
                                     "--inputs", write_json(w.path("in.json"), frames(*inputs)), "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual([(e["tick"], e["name"]) for e in events(rows)], [(11, "paused"), (31, "resumed")])
            s = {r["tick"]: r for r in snapshots(rows)}
            self.assertEqual(s[20]["state"], "paused")
            self.assertEqual((s[20]["sim_tick"], s[20]["time_left_ticks"]), (s[11]["sim_tick"], s[11]["time_left_ticks"]))
            self.assertEqual(s[20]["player"]["pos"], s[11]["player"]["pos"])
            self.assertEqual(s[31]["sim_tick"], s[11]["sim_tick"] + 1, "resumed chạy gameplay ngay trong bước đó")
            self.assertEqual(rows[-1]["sim_tick"], 40 - 20)

    def test_actions_ignored_while_paused(self):
        inputs = [{"tick": 0, "pause": True}, {"tick": 1, "pause": False, "interact": True}]
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {"gather": {"hold": ["ca_loc"]}})
            run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--scenario", sc,
                         "--inputs", write_json(w.path("in.json"), frames(*inputs)), "--out", out)
            self.assertEqual([e["name"] for e in events(read_jsonl(out))], ["paused"], "cạnh interact khi pause bị bỏ")


class Validation(unittest.TestCase):
    def test_bad_day_args_exit_2(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            base = ["--seed", "1", "--ticks", "0", "--out", out]
            self.assertEqual(run_headless("--mode", "gather", "--days", "2", *base)[0], 2)
            for d in ("0", "6"):
                self.assertEqual(run_headless("--mode", "day", "--days", d, *base)[0], 2, d)
            for sc in ({"quan": {"stock": {"ca_loc": 1}}}, {"quan": {"reputation": 4}},
                       {"day": {"money": 300, "earned": 200}}, {"day": {"money": 100}},
                       {"day": {"upgrades": {"oxygen": 9}}},
                       {"day": {"day_plan": [{"day": 1, "dishes": {"pho": 1}}]}}):
                p = write_json(w.path("sc.json"), sc)
                self.assertEqual(run_headless("--mode", "day", "--scenario", p, *base)[0], 2, sc)

    def test_day_plan_override(self):
        sc = {"day": {"day_plan": [{"day": 1, "dishes": {"lau_mam": 1}}]}}
        with Workdir() as w:
            rows = run_day(w, sc, n=0)
            self.assertEqual(events(rows, "day_plan")[0]["data"]["ingredients"],
                             {"bong_dien_dien": 1, "ca_keo": 1, "ca_linh": 2, "keo_neo": 1})


class Determinism(unittest.TestCase):
    def test_two_days_same_bytes(self):
        out = []
        for _ in range(2):
            with Workdir() as w:
                run_day(w, days=2, n=45000, every=300, seed=11)
                with open(w.path("o.jsonl"), "rb") as f:
                    out.append(f.read())
        self.assertEqual(out[0], out[1])


if __name__ == "__main__":
    unittest.main()
