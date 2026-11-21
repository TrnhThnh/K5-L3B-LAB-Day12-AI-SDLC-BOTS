"""Test luật gather mới ở Phase 2 (Ticket-02 mục 1.1, 1.2, Test Contract v1.1), hộp đen qua headless_cmd.
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_gather_p2 -v
"""

import json
import math
import unittest

from helpers import individuals

from helpers import Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json


def G():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


def run(w, block, ticks, inputs=None, every=1):
    args = ["--mode", "gather", "--seed", "5", "--ticks", str(ticks), "--snapshot-every", str(every),
            "--scenario", write_json(w.path("sc.json"), {"gather": block}), "--out", w.path("o.jsonl")]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    assert code == 0, err
    rows = read_jsonl(w.path("o.jsonl"))
    return rows, {s["tick"]: s for s in snapshots(rows)}


def fish_of(snap, fid):
    return next(f for f in snap["fish"] if f["id"] == fid)


NO_MON = {"monsters": []}


class FishSwim(unittest.TestCase):
    def test_initial_schools_distinct_and_in_band(self):
        g = G()
        with Workdir() as w:
            _, s = run(w, {}, 0)
            fish = s[0]["fish"]
            self.assertEqual(len(fish), g["fish_initial"])
            self.assertEqual(len({tuple(f["pos"]) for f in fish}), g["fish_initial"], "8 điểm khác nhau")
            for f in fish:
                self.assertIn(f["pos"][0], g["fish_spawn_x"])
                self.assertIn(f["pos"][1], g["fish_spawn_depths"][f["kind"]])

    def test_swims_at_fish_speed(self):
        with Workdir() as w:
            sc = dict(NO_MON, fish=[{"id": "F1", "kind": "ca_linh", "pos": [50, 6], "heading_deg": 0}])
            _, s = run(w, sc, 60)
            f = fish_of(s[60], "F1")
            self.assertTrue(close(f["pos"][0], 50 + G()["fish_speed"], 0.01), f)
            self.assertEqual(f["age_ticks"], 60)

    def test_reflects_at_x_edge(self):
        hi = G()["fish_x"][1]
        with Workdir() as w:
            sc = dict(NO_MON, fish=[{"id": "F1", "kind": "ca_linh", "pos": [hi - 0.5, 6], "heading_deg": 0}])
            _, s = run(w, sc, 60)
            f = fish_of(s[60], "F1")
            self.assertTrue(close(f["pos"][0], 2 * hi - (hi - 0.5 + G()["fish_speed"]), 0.01), f)
            self.assertTrue(close(f["heading_deg"], 180, 0.01), f)

    def test_reflects_at_species_depth_edge(self):
        hi = G()["fish_depths"]["ca_linh"][1]
        with Workdir() as w:
            sc = dict(NO_MON, fish=[{"id": "F1", "kind": "ca_linh", "pos": [50, hi - 0.5], "heading_deg": 90}])
            _, s = run(w, sc, 60)
            f = fish_of(s[60], "F1")
            self.assertTrue(close(f["pos"][1], 2 * hi - (hi - 0.5 + G()["fish_speed"]), 0.01), f)
            self.assertTrue(close(f["heading_deg"], 270, 0.01), f)

    def test_turn_on_120th_swim_step(self):
        turn = G()["fish_turn_ticks"]
        with Workdir() as w:
            sc = dict(NO_MON, fish=[{"id": "F1", "kind": "ca_loc", "pos": [50, 14], "heading_deg": 0,
                                     "age_ticks": turn - 2}])
            _, s = run(w, sc, 2)
            self.assertTrue(close(fish_of(s[1], "F1")["heading_deg"], 0, 0.001))
            self.assertEqual(fish_of(s[2], "F1")["age_ticks"], turn)

    def test_random_fish_false_keeps_fixture_still(self):
        with Workdir() as w:
            sc = dict(NO_MON, random_fish=False, fish=[{"id": "F1", "kind": "ca_keo", "pos": [50, 25]}])
            rows, s = run(w, sc, G()["fish_spawn_ticks"], every=G()["fish_spawn_ticks"])
            self.assertEqual(s[G()["fish_spawn_ticks"]]["fish"][0]["pos"], [50, 25])
            self.assertEqual(events(rows, "fish_spawned"), [])


class FishSpawn(unittest.TestCase):
    def test_spawn_on_schedule(self):
        g = G()
        k = g["fish_spawn_ticks"]
        with Workdir() as w:
            rows, s = run(w, NO_MON, k, every=k)
            ev = events(rows, "fish_spawned")
            self.assertEqual([e["tick"] for e in ev], [k])
            d = ev[0]["data"]
            self.assertEqual(d["id"], "F%d" % (g["fish_initial"] + 1))
            self.assertIn(d["pos"][0], g["fish_spawn_x"])
            self.assertIn(d["pos"][1], g["fish_spawn_depths"][d["kind"]])
            self.assertEqual(len(s[k]["fish"]), g["fish_initial"] + 1)

    def test_no_spawn_at_cap(self):
        g = G()
        fish = [{"id": f"F{i}", "kind": "ca_keo", "pos": [5 + 7 * i, 25]} for i in range(1, g["fish_max"] + 1)]
        with Workdir() as w:
            rows, _ = run(w, dict(NO_MON, fish=fish), g["fish_spawn_ticks"], every=g["fish_spawn_ticks"])
            self.assertEqual(events(rows, "fish_spawned"), [])


def croc(**kw):
    m = {"id": "M1", "kind": "ca_sau", "pos": [50, 15], "waypoints": [[50, 15], [54, 15]]}
    m.update(kw)
    return m


class Crocodile(unittest.TestCase):
    def sp(self):
        return G()["monsters"]["species"]["ca_sau"]

    def test_default_layout_day1_patrol(self):
        sp = self.sp()
        with Workdir() as w:
            _, s = run(w, {"random_fish": False}, 60)
            mons = s[60]["monsters"]
            self.assertEqual([m["id"] for m in mons], ["M1"], "gather độc lập dùng bố trí Ngày 1")
            self.assertTrue(close(mons[0]["pos"][0], 60 + sp["patrol_speed"], 0.01), mons[0])
            self.assertEqual(mons[0]["state"], "patrol")

    def test_patrol_switches_target_on_arrival(self):
        sp = self.sp()
        n = int(round(4 / sp["patrol_speed"] * 60))
        with Workdir() as w:
            _, s = run(w, {"random_fish": False, "monsters": [croc(pos=[50, 25], waypoints=[[50, 25], [54, 25]])]}, n)
            self.assertEqual(s[n]["monsters"][0]["pos"], [54, 25])
            self.assertEqual(s[n]["monsters"][0]["target_idx"], 0)

    def test_chase_when_deep_and_near(self):
        with Workdir() as w:
            _, s = run(w, {"random_fish": False, "player": {"pos": [50, 12]}, "monsters": [croc(pos=[50, 20])]}, 1)
            m = s[1]["monsters"][0]
            self.assertEqual(m["state"], "chase")
            self.assertTrue(close(m["pos"][1], 20 - self.sp()["chase_speed"] / 60, 0.001), m)

    def test_no_chase_when_shallow(self):
        with Workdir() as w:
            _, s = run(w, {"random_fish": False, "player": {"pos": [50, 9]}, "monsters": [croc(pos=[50, 12])]}, 1)
            self.assertEqual(s[1]["monsters"][0]["state"], "patrol")

    def test_hit_loses_hp_half_hold_and_sets_invuln(self):
        mo = G()["monsters"]
        hold = ["ca_loc", "bong_sung", "ca_linh", "ca_linh", "keo_neo"]
        with Workdir() as w:
            rows, s = run(w, {"random_fish": False, "player": {"pos": [50, 15]}, "hold": individuals(hold),
                              "monsters": [croc()]}, 1)
            hit = events(rows, "monster_hit")[0]
            n = math.floor(len(hold) * mo["loss_ratio"])
            self.assertEqual(hit["data"], {"monster_id": "M1", "hp": G()["hp_max"] - 1,
                                           "lost": list(reversed(individuals(hold, 100 - 1 / 120)))[:n], "pos": [50, 15]})
            p = s[1]["player"]
            self.assertEqual((p["hp"], p["invuln_ticks"]), (G()["hp_max"] - 1, mo["invuln_ticks"]))
            self.assertEqual(s[1]["hold"], individuals(hold, 100 - 1 / 120)[:len(hold) - n])
            m = s[1]["monsters"][0]
            self.assertEqual((m["state"], m["state_ticks_left"], m["recoil_dir"]),
                             ("recoil", self.sp()["recoil_ticks"], [1, 0]), "trùng tâm dùng +x")

    def test_recoil_then_patrol(self):
        sp = self.sp()
        r = sp["recoil_ticks"]
        with Workdir() as w:
            rows, s = run(w, {"random_fish": False, "player": {"pos": [50, 15]}, "monsters": [croc()]}, r + 1)
            m = s[r + 1]["monsters"][0]
            self.assertTrue(close(m["pos"][0], 50 + sp["recoil_dist"], 0.001), m)
            self.assertEqual(m["state"], "patrol")
            self.assertEqual(len(events(rows, "monster_hit")), 1, "bất tử 90 tick nên không có hit thứ hai")

    def test_invulnerable_blocks_hit(self):
        with Workdir() as w:
            rows, s = run(w, {"random_fish": False, "player": {"pos": [50, 15], "invuln_ticks": 10},
                              "monsters": [croc()]}, 1)
            self.assertEqual(events(rows, "monster_hit"), [])
            self.assertNotEqual(s[1]["monsters"][0]["state"], "recoil")

    def test_faint_by_monster(self):
        hold = ["ca_loc", "bong_sung", "ca_linh"]
        with Workdir() as w:
            inv = w.path("inv.json")
            args = ["--mode", "gather", "--seed", "1", "--ticks", "5", "--out", w.path("o.jsonl"),
                    "--inventory-out", inv, "--scenario",
                    write_json(w.path("sc.json"), {"gather": {"random_fish": False, "hold": individuals(hold),
                                                              "player": {"pos": [50, 15], "hp": 1},
                                                              "monsters": [croc()]}})]
            self.assertEqual(run_headless(*args)[0], 0)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual([e["name"] for e in events(rows)], ["monster_hit", "faint", "gather_end"])
            self.assertEqual(events(rows, "monster_hit")[0]["data"]["lost"], individuals(hold, 100 - 1 / 120)[-1:])
            self.assertEqual(events(rows, "faint")[0]["data"], {"cause": "monster", "lost": individuals(["ca_loc", "bong_sung"], 100 - 1 / 120)[::-1], "hp": 0})
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

    def test_bad_monster_fixture_exit_2(self):
        for m in (croc(kind="ran"), croc(pos=[50, 5]), croc(waypoints=[[50, 15]]), croc(state="recoil"),
                  croc(target_idx=2)):
            with Workdir() as w:
                sc = write_json(w.path("sc.json"), {"gather": {"monsters": [m]}})
                code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--scenario", sc,
                                       "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, m)


if __name__ == "__main__":
    unittest.main()
