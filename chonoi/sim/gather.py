"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm BOTS đã viết (duongchien147): lát 1 và lát 2 bên dưới. Giả định chỗ đề chưa rõ ghi ở docs/clarify.md,
dữ liệu sự kiện ghi ở docs/contracts/README.md.
Thứ tự một bước (PRD mục 13.8, "Gather"):
  Lát 1 (đã làm): bơi + oxy + biên + giỏ
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  Lát 2 (đã làm): hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Phase 2 (Ticket-02, Test Contract v1.1), thứ tự bước theo mục 4.5:
  đồng hồ, hồi chiêu, bất tử, nút -> bơi, oxy, ngạt -> Cá Sấu theo id rồi tối đa một hit
  -> tương tác (bến trước hái) -> bắt cá (vị trí cá trước khi bơi) -> hết giờ
  -> nếu còn giờ: cá bơi, sinh cá theo lịch.
"""

import math

from ..ids import sort_by_id
from ..inventory import age_items, validate_individuals
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")
MONSTER_STATES = ("patrol", "chase", "recoil")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1, oxygen_max_s=None, hp_max=None):
        t = tuning["gather"]
        self.day = day
        self.hp_max = int(hp_max if hp_max is not None else t["hp_max"])
        self.t = t
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round((oxygen_max_s if oxygen_max_s is not None else t["oxygen_max_s"]) * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.freshness = tuning["freshness"]
        self.decay_units = self.freshness["gather_decay_per_s"] * 240 / TICK
        self.hold = validate_individuals(scenario.get("hold", []))
        for item in self.hold:
            if day > 1:
                item["id"] = ids.new("I")
            else:
                ids.reserve(item["id"])  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = 0
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        # random_fish=false: tắt cá mặc định, bơi và sinh; cá fixture đứng yên.
        # random_fish=true + fish[]: thay đàn ban đầu, vẫn bơi/sinh.
        self.fish_live = scenario.get("random_fish", True)
        src_fish = scenario.get("fish", [])
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": float(f.get("heading_deg", 0)), "age_ticks": f.get("age_ticks", 0)}
                     for f in src_fish]
        src_mon = scenario["monsters"] if "monsters" in scenario else [
            m for m in t["monsters"]["spawns"] if m.get("from_day", 1) <= day]
        self.monsters = [self._monster(m) for m in src_mon]
        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                ids.reserve(e["id"])
        if "fish" not in scenario and self.fish_live:
            for _ in range(int(t["fish_initial"])):  # 8 đàn ở 8 điểm khác nhau theo seed
                self._spawn_fish(None)
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> list:
        return sort_by_id(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      "age_ticks": f["age_ticks"]} for f in sort_by_id(self.fish)],
            "monsters": [{k: m[k] for k in ("id", "kind", "pos", "waypoints", "target_idx", "state",
                                             "state_ticks_left", "recoil_dir")} for m in sort_by_id(self.monsters)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        age_items(self.hold, self.decay_units, self.freshness["spoiled_below"], "hold", events)
        # 2. bơi + chặn mép; so phân vùng đầu/cuối bước -> dive / surface
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif now_surface and not was_surface:
            events.append(("surface", {"pos": list(self.pos)}))
        # 2b. oxy theo d CUỐI bước, ngạt, ngất
        if self._oxygen_step(now_surface, events):
            return events
        # 2c. Cá Sấu theo id, rồi tối đa một hit
        if self._monsters_step(events):
            return events
        # 3. interact: bến trước, rồi hái (chỉ ở mặt nước)
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if now_surface:
                self._harvest(events)
        # 4. bắt cá (chỉ dưới nước, hết hồi chiêu)
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not now_surface:
            self._catch(events)
        # 5. hết giờ; còn giờ thì cá bơi rồi sinh cá theo lịch
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        if self.fish_live:
            for f in sort_by_id(self.fish):
                self._swim_fish(f)
            if self.phase_tick % int(self.t["fish_spawn_ticks"]) == 0:
                self._spawn_fish(events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _oxygen_step(self, at_surface, events) -> bool:
        """Cập nhật oxy / ngạt / Máu theo vị trí cuối bước. Trả True nếu ngất (buổi kết thúc)."""
        t = self.t
        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + int(t["oxygen_refill_per_tick"]))
            self.zero_oxy_ticks = 0
            return False
        before = self.oxygen_ticks
        self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
        if before > 0 and self.oxygen_ticks == 0:
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))
        if self.oxygen_ticks > 0:
            self.zero_oxy_ticks = 0
            return False
        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks < int(t["choke_interval_ticks"]):
            return False
        self.zero_oxy_ticks = 0
        self.hp = max(0, self.hp - 1)
        events.append(("choke", {"hp": self.hp}))
        if self.hp > 0:
            return False
        lost = list(reversed(self.hold))  # bỏ giỏ theo LIFO: nhặt sau bỏ trước
        self.hold = []
        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
        self._finish("fainted", events)
        return True

    # --- cá bơi và sinh cá (Ticket-02 mục 1.1) ------------------------------------
    def _swim_fish(self, f):
        t = self.t
        f["age_ticks"] += 1
        if f["age_ticks"] % int(t["fish_turn_ticks"]) == 0:  # đổi hướng theo seed trước khi di chuyển
            f["heading_deg"] = self.rng.get("fish_turn").uniform(0.0, 360.0)
        h = math.radians(f["heading_deg"])
        step = t["fish_speed"] / TICK
        vec = [math.cos(h), math.sin(h)]
        bands = (t["fish_x"], t["fish_depths"][f["kind"]])
        for i in range(2):
            lo, hi = bands[i]
            v = f["pos"][i] + vec[i] * step
            if v > hi:  # phản xạ phần quãng đường còn lại, đảo thành phần hướng vuông góc với mép
                v, vec[i] = 2 * hi - v, -vec[i]
            elif v < lo:
                v, vec[i] = 2 * lo - v, -vec[i]
            f["pos"][i] = min(hi, max(lo, v))
        f["heading_deg"] = math.degrees(math.atan2(vec[1], vec[0])) % 360

    def _spawn_fish(self, events):
        """Sinh tối đa một đàn: còn dưới trần, có điểm cách mọi đàn đang sống > clearance.
        Chọn loài theo trọng số (chuẩn hóa lại trên các loài còn điểm), rồi chọn đều một điểm."""
        t = self.t
        if len(self.fish) >= int(t["fish_max"]):
            return
        clear = t["fish_spawn_clearance"]
        options = {}
        for kind in sorted(t["fish_weights"]):
            pts = [[float(x), float(d)] for x in t["fish_spawn_x"] for d in t["fish_spawn_depths"][kind]
                   if all(math.dist([x, d], f["pos"]) > clear for f in self.fish)]
            if pts:
                options[kind] = pts
        if not options:
            return
        rng = self.rng.get("fish_spawn")
        total = sum(t["fish_weights"][k] for k in options)
        r, acc, kind = rng.random() * total, 0.0, None
        for k in options:
            acc += t["fish_weights"][k]
            kind = k
            if r < acc:
                break
        pos = options[kind][rng.randrange(len(options[kind]))]
        fish = {"id": self.ids.new("F"), "kind": kind, "pos": pos,
                "heading_deg": rng.uniform(0.0, 360.0), "age_ticks": 0}
        self.fish.append(fish)
        if events is not None:
            events.append(("fish_spawned", {"id": fish["id"], "kind": kind, "pos": list(pos)}))

    # --- Cá Sấu (Ticket-02 mục 1.2) -----------------------------------------------
    def _monster(self, m):
        return {"id": m["id"], "kind": m["kind"], "pos": [float(c) for c in m["pos"]],
                "waypoints": [[float(c) for c in w] for w in m["waypoints"]],
                "target_idx": m.get("target_idx", 1), "state": m.get("state", "patrol"),
                "state_ticks_left": m.get("state_ticks_left", 0), "recoil_dir": m.get("recoil_dir")}

    def _species(self, m):
        return self.t["monsters"]["species"][m["kind"]]

    def _clamp_monster(self, m):
        b, (dlo, dhi) = self.t["bounds"], self._species(m)["depths"]
        m["pos"][0] = min(b["x"][1], max(b["x"][0], m["pos"][0]))
        m["pos"][1] = min(dhi, max(dlo, m["pos"][1]))

    @staticmethod
    def _move_towards(m, target, speed) -> bool:
        """Đi về `target` tối đa speed/60 m. Trả True nếu tới nơi trong bước này."""
        dist = math.dist(m["pos"], target)
        step = speed / TICK
        if dist <= step + 1e-9:  # dung sai cộng dồn float: 240 bước × 1/60 m phải tới đúng 4 m
            m["pos"] = [float(target[0]), float(target[1])]
            return True
        m["pos"] = [m["pos"][i] + (target[i] - m["pos"][i]) / dist * step for i in range(2)]
        return False

    def _monsters_step(self, events) -> bool:
        """Cập nhật Cá Sấu theo id, rồi xét tối đa một hit. Trả True nếu người chơi ngất."""
        fresh = set()  # vừa hết recoil: về patrol, xét phát hiện/chạm từ bước kế
        for m in sort_by_id(self.monsters):
            sp = self._species(m)
            if m["state"] == "recoil":
                step = sp["recoil_dist"] / sp["recoil_ticks"]
                m["pos"] = [m["pos"][i] + m["recoil_dir"][i] * step for i in range(2)]
                self._clamp_monster(m)
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"], m["state_ticks_left"], m["recoil_dir"] = "patrol", 0, None
                    fresh.add(m["id"])
                continue
            deep = self.pos[1] >= sp["depths"][0]
            dist = math.dist(m["pos"], self.pos)
            if m["state"] == "patrol" and deep and dist <= sp["detect_radius"]:
                m["state"] = "chase"
            elif m["state"] == "chase" and (dist > sp["exit_radius"] or not deep):
                m["state"] = "patrol"
            if m["state"] == "chase":
                self._move_towards(m, self.pos, sp["chase_speed"])
            elif self._move_towards(m, m["waypoints"][m["target_idx"]], sp["patrol_speed"]):
                m["target_idx"] = 1 - m["target_idx"]  # đến nơi: đổi mục tiêu cho bước sau
            self._clamp_monster(m)
        if self.invuln_ticks > 0:
            return False
        hits = []
        for m in sort_by_id(self.monsters):
            sp = self._species(m)
            d = math.dist(m["pos"], self.pos)
            if (m["state"] != "recoil" and m["id"] not in fresh and d <= sp["hit_radius"]
                    and self.pos[1] >= sp["depths"][0]):
                hits.append((d, m))
        if not hits:
            return False
        m = min(hits, key=lambda x: x[0])[1]  # gần nhất; hòa thì id nhỏ (đã duyệt theo id)
        mo = self.t["monsters"]
        self.hp = max(0, self.hp - 1)
        n_lost = math.floor(len(self.hold) * mo["loss_ratio"])
        lost = [self.hold.pop() for _ in range(n_lost)]  # LIFO: nhặt sau mất trước
        self.invuln_ticks = int(mo["invuln_ticks"])
        away = [m["pos"][i] - self.pos[i] for i in range(2)]
        norm = math.hypot(*away)
        m["recoil_dir"] = [away[0] / norm, away[1] / norm] if norm > 0 else [1.0, 0.0]
        m["state"], m["state_ticks_left"] = "recoil", int(self._species(m)["recoil_ticks"])
        events.append(("monster_hit", {"monster_id": m["id"], "hp": self.hp, "lost": lost, "pos": list(self.pos)}))
        if self.hp > 0:
            return False
        rest = list(reversed(self.hold))
        self.hold = []
        events.append(("faint", {"cause": "monster", "lost": rest, "hp": 0}))
        self._finish("fainted", events)
        return True

    def _nearest(self, items, radius):
        """Phần tử gần nhất trong bán kính; bằng khoảng cách thì id nhỏ hơn (thứ tự sort_by_id)."""
        best, best_d = None, None
        for e in sort_by_id(items):
            dd = math.dist(self.pos, e["pos"])
            if dd <= radius and (best_d is None or dd < best_d):
                best, best_d = e, dd
        return best

    def _free(self) -> int:
        return int(self.t["hold_capacity"]) - len(self.hold)

    def _harvest(self, events):
        """PRD-0 F: đủ chỗ thì thêm node_yield, đặt regrow, phát gather; thiếu chỗ phát hold_full, nút giữ nguyên."""
        node = self._nearest([n for n in self.nodes if n["regrow_ticks"] == 0], self.t["interact_radius"])
        if node is None:
            return
        need = int(self.t["node_yield"])
        if self._free() < need:
            events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                         "required": need, "free": self._free()}))
            return
        self.hold.extend({"id": self.ids.new("I"), "kind": node["kind"], "fresh": self.freshness["initial"]}
                         for _ in range(need))  # cuối mảng là mới nhất (LIFO)
        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": need}))

    def _catch(self, events):
        """PRD-0 F: đàn gần nhất; đủ chỗ thì thêm toàn bộ yield, xóa đàn, đặt hồi chiêu.
        Thiếu chỗ: hold_full, giữ đàn và hồi chiêu, không thử đàn khác. Không có đàn: không gì cả."""
        fish = self._nearest(self.fish, self.t["catch_radius"])
        if fish is None:
            return
        need = int(self.t["fish_yield"][fish["kind"]])
        if self._free() < need:
            events.append(("hold_full", {"action": "catch", "fish_id": fish["id"],
                                         "required": need, "free": self._free()}))
            return
        self.hold.extend({"id": self.ids.new("I"), "kind": fish["kind"], "fresh": self.freshness["initial"]}
                         for _ in range(need))
        self.fish = [f for f in self.fish if f["id"] != fish["id"]]
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": need}))

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
