"""Test luật gather của nhóm BOTS (lát 1 + lát 2), kiểu HỘP ĐEN qua headless_cmd như test_smoke_p1.

Mọi số đọc từ game.contract.json, không hard-code. Giả định chỗ đề chưa rõ: docs/clarify.md.
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_gather_rules -v
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def G():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


def omax():
    return int(round(G()["oxygen_max_s"] * 60))


def run(w, block, ticks, inputs=None, every=1, inv_out=None):
    """Chạy gather với scenario `block`; trả (rows, snapshot theo tick)."""
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--snapshot-every", str(every),
            "--scenario", write_json(w.path("sc.json"), {"gather": block}), "--out", w.path("o.jsonl")]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if inv_out:
        args += ["--inventory-out", inv_out]
    code, err = run_headless(*args)
    assert code == 0, err
    rows = read_jsonl(w.path("o.jsonl"))
    return rows, {s["tick"]: s for s in snapshots(rows)}


def names(rows):
    return [r["name"] for r in events(rows)]


class Oxygen(unittest.TestCase):
    def test_underwater_loses_one_per_tick(self):
        with Workdir() as w:
            _, s = run(w, {"player": {"pos": [20, 5]}, "random_fish": False}, 10)
            self.assertEqual(s[10]["player"]["oxygen_ticks"], omax() - 10)
            self.assertFalse(s[10]["player"]["at_surface"])

    def test_surface_refills_and_clamps(self):
        refill = G()["oxygen_refill_per_tick"]
        with Workdir() as w:
            _, s = run(w, {"player": {"pos": [20, 0], "oxygen_ticks": 100}, "random_fish": False}, 1)
            self.assertEqual(s[1]["player"]["oxygen_ticks"], 100 + refill)
        with Workdir() as w:
            _, s = run(w, {"player": {"pos": [20, 0], "oxygen_ticks": omax() - 1}, "random_fish": False}, 1)
            self.assertEqual(s[1]["player"]["oxygen_ticks"], omax())

    def test_oxygen_empty_once(self):
        with Workdir() as w:
            rows, s = run(w, {"player": {"pos": [20, 5], "oxygen_ticks": 1}, "random_fish": False}, 5)
            ev = events(rows, "oxygen_empty")
            self.assertEqual([e["tick"] for e in ev], [1])
            self.assertEqual(ev[0]["data"], {"oxygen_ticks": 0})
            self.assertEqual(s[5]["player"]["oxygen_ticks"], 0)

    def test_choke_every_interval(self):
        interval = G()["choke_interval_ticks"]
        with Workdir() as w:
            rows, s = run(w, {"player": {"pos": [20, 5], "oxygen_ticks": 0}, "random_fish": False}, interval * 2)
            ch = events(rows, "choke")
            self.assertEqual([e["tick"] for e in ch], [interval, interval * 2])
            self.assertEqual(ch[0]["data"]["hp"], G()["hp_max"] - 1)
            self.assertEqual(s[interval * 2]["player"]["hp"], G()["hp_max"] - 2)

    def test_zero_oxy_counter_from_scenario(self):
        interval = G()["choke_interval_ticks"]
        with Workdir() as w:
            rows, _ = run(w, {"player": {"pos": [20, 5], "oxygen_ticks": 0, "zero_oxy_ticks": interval - 1},
                              "random_fish": False}, 1)
            self.assertEqual([e["tick"] for e in events(rows, "choke")], [1])

    def test_surfacing_resets_choke_counter(self):
        with Workdir() as w:
            _, s = run(w, {"player": {"pos": [20, 1], "oxygen_ticks": 0, "zero_oxy_ticks": 30},
                           "random_fish": False}, 20, inputs=[{"tick": 0, "move": [0, -1]}])
            last = s[20]["player"]
            self.assertTrue(last["at_surface"])
            self.assertEqual(last["zero_oxy_ticks"], 0)
            self.assertGreater(last["oxygen_ticks"], 0)

    def test_faint_loses_hold_and_writes_empty_inventory(self):
        interval = G()["choke_interval_ticks"]
        with Workdir() as w:
            inv = w.path("inv.json")
            rows, _ = run(w, {"player": {"pos": [20, 5], "oxygen_ticks": 0, "zero_oxy_ticks": interval - 1, "hp": 1},
                              "hold": ["ca_loc", "bong_sung"], "random_fish": False}, 50, inv_out=inv)
            self.assertEqual(names(rows), ["choke", "faint", "gather_end"])
            self.assertEqual(events(rows, "faint")[0]["data"],
                             {"cause": "choke", "lost": ["bong_sung", "ca_loc"], "hp": 0}, "lost theo LIFO")
            end = events(rows, "gather_end")[0]
            self.assertEqual(end["tick"], 1)
            self.assertEqual(end["data"], {"reason": "fainted", "inventory": {"items": {}}})
            self.assertEqual(rows[-1]["reason"], "fainted")
            self.assertEqual(snapshots(rows)[-1]["hold"], [])
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})


class Zones(unittest.TestCase):
    def test_dive_then_surface_events(self):
        with Workdir() as w:
            rows, _ = run(w, {"player": {"pos": [20, 0]}, "random_fish": False}, 120,
                          inputs=[{"tick": 0, "move": [0, 1]}, {"tick": 30, "move": [0, -1]}])
            self.assertEqual(names(rows), ["dive", "surface"])
            dive, surf = events(rows, "dive")[0], events(rows, "surface")[0]
            self.assertGreater(dive["data"]["pos"][1], G()["surface_depth"])
            self.assertLessEqual(surf["data"]["pos"][1], G()["surface_depth"])
            self.assertLess(dive["tick"], surf["tick"])


class Harvest(unittest.TestCase):
    def node_scn(self, **extra):
        b = {"player": {"pos": [12, 0]}, "random_fish": False,
             "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}]}
        b.update(extra)
        return b

    def test_harvest_ready_node_then_regrow(self):
        regrow = int(round(G()["regrow_s"] * 60))
        with Workdir() as w:
            rows, s = run(w, self.node_scn(), regrow + 2,
                          inputs=[{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                                  {"tick": 2, "interact": True}])
            g = events(rows, "gather")
            self.assertEqual(len(g), 1, "nút đang mọc lại không hái được lần hai")
            self.assertEqual(g[0]["data"], {"node_id": "N1", "kind": "bong_dien_dien", "amount": G()["node_yield"]})
            self.assertEqual(s[1]["hold"], ["bong_dien_dien"] * G()["node_yield"])
            self.assertFalse(s[1]["nodes"][0]["ready"])
            self.assertEqual(s[1]["nodes"][0]["regrow_ticks"], regrow)
            rg = events(rows, "node_regrown")
            self.assertEqual([e["tick"] for e in rg], [1 + regrow])
            self.assertTrue(s[1 + regrow]["nodes"][0]["ready"])

    def test_no_harvest_underwater_or_out_of_range(self):
        with Workdir() as w:
            rows, _ = run(w, self.node_scn(player={"pos": [12, 2]}), 1, inputs=[{"tick": 0, "interact": True}])
            self.assertEqual(events(rows, "gather"), [])
        with Workdir() as w:
            far = 12 + G()["interact_radius"] + 0.5
            rows, _ = run(w, self.node_scn(player={"pos": [far, 0]}), 1, inputs=[{"tick": 0, "interact": True}])
            self.assertEqual(events(rows, "gather"), [])

    def test_hold_full_blocks_harvest(self):
        cap = G()["hold_capacity"]
        with Workdir() as w:
            rows, s = run(w, self.node_scn(hold=["ca_loc"] * cap), 1, inputs=[{"tick": 0, "interact": True}])
            self.assertEqual(names(rows), ["hold_full"])
            self.assertEqual(events(rows, "hold_full")[0]["data"],
                             {"action": "gather", "node_id": "N1", "required": G()["node_yield"], "free": 0})
            self.assertTrue(s[1]["nodes"][0]["ready"], "giỏ đầy: nút không bị hái")
            self.assertEqual(s[1]["hold_count"], cap)

    def test_nearest_then_smaller_id(self):
        with Workdir() as w:
            nodes = [{"id": "N10", "kind": "bong_sung", "pos": [11, 0]},
                     {"id": "N2", "kind": "bong_dien_dien", "pos": [13, 0]}]
            rows, _ = run(w, self.node_scn(nodes=nodes), 1, inputs=[{"tick": 0, "interact": True}])
            self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N2")

    def test_dock_wins_over_harvest(self):
        with Workdir() as w:
            nodes = [{"id": "N1", "kind": "bong_sung", "pos": [2, 0]}]
            rows, _ = run(w, self.node_scn(player={"pos": [2, 0]}, nodes=nodes), 1,
                          inputs=[{"tick": 0, "interact": True}])
            self.assertEqual(names(rows), ["gather_end"])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")


class Catch(unittest.TestCase):
    def fish_scn(self, **extra):
        b = {"player": {"pos": [15, 5]}, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}]}
        b.update(extra)
        return b

    def test_catch_school(self):
        y = G()["fish_yield"]["ca_linh"]
        cd = int(round(G()["catch_cooldown_s"] * 60))
        with Workdir() as w:
            rows, s = run(w, self.fish_scn(hold=["bong_sung"]), 1, inputs=[{"tick": 0, "catch": True}])
            self.assertEqual(events(rows, "fish_caught")[0]["data"], {"fish_id": "F1", "kind": "ca_linh", "yield": y})
            self.assertEqual(s[1]["hold"], ["bong_sung"] + ["ca_linh"] * y, "giỏ giữ thứ tự nhặt, mới nhất ở cuối")
            self.assertEqual(s[1]["fish"], [])
            self.assertEqual(s[1]["player"]["catch_cd_ticks"], cd)

    def test_no_catch_at_surface(self):
        with Workdir() as w:
            fish = [{"id": "F1", "kind": "ca_linh", "pos": [15, 1]}]
            rows, s = run(w, self.fish_scn(player={"pos": [15, 0]}, fish=fish), 1, inputs=[{"tick": 0, "catch": True}])
            self.assertEqual(events(rows, "fish_caught"), [])
            self.assertEqual(s[1]["player"]["catch_cd_ticks"], 0)

    def test_cooldown_blocks_second_catch(self):
        cd = int(round(G()["catch_cooldown_s"] * 60))
        fish = [{"id": "F1", "kind": "ca_loc", "pos": [15, 5]}, {"id": "F2", "kind": "ca_loc", "pos": [15.5, 5]}]
        with Workdir() as w:
            inputs = [{"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": 2, "catch": True},
                      {"tick": 3, "catch": False}, {"tick": cd + 1, "catch": True}]
            rows, _ = run(w, self.fish_scn(fish=fish), cd + 2, inputs=inputs)
            ev = events(rows, "fish_caught")
            self.assertEqual([(e["tick"], e["data"]["fish_id"]) for e in ev], [(1, "F1"), (cd + 2, "F2")])

    def test_not_enough_room_keeps_school_and_cooldown(self):
        """PRD-0 F: thiếu chỗ cho cả đàn thì hold_full, giữ đàn, không đặt hồi chiêu, không thử đàn khác."""
        cap = G()["hold_capacity"]
        y = G()["fish_yield"]["ca_linh"]
        fish = [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}, {"id": "F2", "kind": "ca_loc", "pos": [16, 5]}]
        with Workdir() as w:
            rows, s = run(w, self.fish_scn(hold=["ca_loc"] * (cap - y + 1), fish=fish), 1,
                          inputs=[{"tick": 0, "catch": True}])
            self.assertEqual(names(rows), ["hold_full"])
            self.assertEqual(events(rows, "hold_full")[0]["data"],
                             {"action": "catch", "fish_id": "F1", "required": y, "free": y - 1})
            self.assertEqual(len(s[1]["fish"]), 2)
            self.assertEqual(s[1]["hold_count"], cap - y + 1)
            self.assertEqual(s[1]["player"]["catch_cd_ticks"], 0)

    def test_miss_sets_no_cooldown(self):
        with Workdir() as w:
            rows, s = run(w, self.fish_scn(fish=[{"id": "F1", "kind": "ca_loc", "pos": [40, 5]}]), 1,
                          inputs=[{"tick": 0, "catch": True}])
            self.assertEqual(events(rows), [])
            self.assertEqual(s[1]["player"]["catch_cd_ticks"], 0)

    def test_full_hold_keeps_fish(self):
        cap = G()["hold_capacity"]
        with Workdir() as w:
            rows, s = run(w, self.fish_scn(hold=["ca_loc"] * cap), 1, inputs=[{"tick": 0, "catch": True}])
            self.assertEqual(names(rows), ["hold_full"])
            self.assertEqual(len(s[1]["fish"]), 1)


class Determinism(unittest.TestCase):
    def test_full_run_same_bytes(self):
        inputs = [{"tick": 0, "move": [1, 0]}, {"tick": 150, "move": [0, 0], "interact": True},
                  {"tick": 151, "move": [0.5, 1], "interact": False}, {"tick": 200, "catch": True},
                  {"tick": 201, "catch": False, "move": [0, 1]}]
        out = []
        for _ in range(2):
            with Workdir() as w:
                run(w, {}, 2400, inputs=inputs, every=10)
                with open(w.path("o.jsonl"), "rb") as f:
                    out.append(f.read())
        self.assertEqual(out[0], out[1])


if __name__ == "__main__":
    unittest.main()
