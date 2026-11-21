"""Buổi tối — Mở Quán (`quan`), theo PRD-0 mục F "Quán" và Test Contract v1.0.

Nhóm BOTS (duongchien147, nhận thay phần của TrnhThnh ở Phase 1). Dữ liệu sự kiện: docs/contracts/README.md.

Một bước:
  1. tăng phase_tick, giảm timer ca, nấu, ăn, kiên nhẫn; ready_ticks chỉ tăng cho món đã ready ở đầu bước
  2. bếp theo id: nấu xong -> ready (dish_ready)
  3. đi lại, rồi tối đa MỘT interact chọn theo (khoảng cách, bếp trước bàn, id)
  4. theo id bàn: ăn xong trả tiền (paid) rồi rời; còn giờ thì khách chờ hết kiên nhẫn rời (customer_left);
     hết ca: khách đang ăn trả ngay, khách chờ rời `closing` không trừ uy tín, rồi quan_end
  5. còn giờ: lịch khách (first_customer_tick, rồi mỗi customer_interval_s), customer_arrived / no_dish
"""

import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0
STOVE_STATES = ("idle", "cooking", "ready")
CUST_STATES = ("waiting", "eating")
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")
CUST_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left", "eat_ticks_left",
             "order_status", "reserved", "base_price", "tip"}


def _ticks(seconds):
    return int(round(seconds * TICK))


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho vật lý (gồm cả phần đang giữ chỗ): --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", _ticks(t["duration_s"]))
        self.reputation = float(scenario.get("reputation", t["reputation_initial"]))
        self.random_customers = scenario.get("random_customers", True)
        self.patience_max = _ticks(t["patience_s"])
        self.phase_tick = 0
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = [self._fixture_customer(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
        self._fill_missing_reserved(scenario.get("customers", []))
        self._validate_fixture()
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    # --- dựng và kiểm fixture -------------------------------------------------
    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _fixture_customer(self, c):
        extra = set(c) - CUST_KEYS
        if extra:
            raise BadInput(f"customers.{c['id']}: trường lạ {sorted(extra)}")
        if c.get("dish_id") not in self.menu:
            raise BadInput(f"customers.{c['id']}: dish_id phải là món trong menu")
        out = {"id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
               "order_tick": c.get("order_tick", 0), "state": c.get("state", "waiting"),
               "patience_ticks_left": c.get("patience_ticks_left", self.patience_max),
               "eat_ticks_left": c.get("eat_ticks_left", 0),
               "order_status": c.get("order_status", "reserved"),
               "reserved": dict(c.get("reserved", {})),
               "base_price": c.get("base_price"), "tip": c.get("tip", 0)}
        if out["state"] not in CUST_STATES or out["order_status"] not in ORDER_STATUSES:
            raise BadInput(f"customers.{c['id']}: state/order_status không hợp lệ")
        for k in ("order_tick", "patience_ticks_left", "eat_ticks_left", "tip"):
            v = out[k]
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise BadInput(f"customers.{c['id']}.{k} phải là số nguyên không âm")
        if out["patience_ticks_left"] > self.patience_max:
            raise BadInput(f"customers.{c['id']}: kiên nhẫn vượt tối đa")
        return out

    def _fill_missing_reserved(self, raw):
        """Đơn reserved thiếu `reserved` thì cấp theo công thức, theo order_tick rồi id bàn."""
        given = {c["id"] for c in raw if "reserved" in c}
        todo = [c for c in self.customers if c["order_status"] == "reserved" and c["id"] not in given]
        for c in sorted(todo, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            c["reserved"] = dict(self.menu[c["dish_id"]]["recipe"])

    def _validate_fixture(self):
        held = {}
        for c in self.customers:
            recipe = self.menu[c["dish_id"]]["recipe"]
            st = c["order_status"]
            if st == "reserved" and c["reserved"] != recipe:
                raise BadInput(f"customers.{c['id']}: giữ chỗ khác công thức")
            if st != "reserved" and c["reserved"]:
                raise BadInput(f"customers.{c['id']}: chỉ đơn reserved mới giữ chỗ")
            for k, n in c["reserved"].items():
                held[k] = held.get(k, 0) + n
            if c["state"] == "eating":
                if st != "served" or c["eat_ticks_left"] <= 0 or not isinstance(c["base_price"], int):
                    raise BadInput(f"customers.{c['id']}: khách eating phải served, có timer ăn và base_price")
            elif st == "served":
                raise BadInput(f"customers.{c['id']}: đơn served thì khách phải đang ăn")
        for k, n in held.items():
            if n > self.stock.get(k, 0):
                raise BadInput(f"giữ chỗ {k} vượt tồn kho")
        orders = {c["id"]: c for c in self.customers}
        on_dish = []
        for s in self.stoves:
            if s["state"] not in STOVE_STATES:
                raise BadInput(f"stoves.{s['id']}: state không hợp lệ")
            if s["state"] == "idle":
                if s["dish"] is not None:
                    raise BadInput(f"stoves.{s['id']}: bếp idle không có món")
                continue
            if s["state"] == "cooking" and s["cook_ticks_left"] <= 0:
                raise BadInput(f"stoves.{s['id']}: bếp cooking cần cook_ticks_left > 0")
            on_dish.append(s["dish"])
        if self.hand is not None:
            on_dish.append(self.hand)
        seen = set()
        for d in on_dish:
            oid = d.get("order_id") if isinstance(d, dict) else None
            c = orders.get(oid)
            if c is None or c["dish_id"] != d.get("dish_id") or c["order_status"] != "assigned":
                raise BadInput("món trên bếp/tay không khớp đơn assigned")
            if oid in seen:
                raise BadInput(f"bếp và tay giữ cùng đơn {oid}")
            seen.add(oid)
        for c in self.customers:
            if c["order_status"] == "assigned" and c["id"] not in seen:
                raise BadInput(f"customers.{c['id']}: đơn assigned phải có đúng một món ở bếp hoặc tay")

    # --- snapshot ---------------------------------------------------------------
    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": [dict(c, reserved={k: c["reserved"][k] for k in sorted(c["reserved"])})
                          for c in sort_by_id(self.customers)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và timer
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for s in self.stoves:
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            else:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
        # 2. bếp nấu xong
        for s in self.stoves:
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"], s["ready_ticks"] = "ready", 0
                events.append(("dish_ready", self._stove_ev(s)))
        # 3. đi lại rồi tối đa một interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        # 4. thu tiền, khách rời, đóng ca
        closing = self.time_left_ticks <= 0
        for c in sorted(list(self.customers), key=lambda c: id_key(c["table_id"])):
            if c["state"] == "eating" and (c["eat_ticks_left"] == 0 or closing):
                self._pay(c, "closing" if c["eat_ticks_left"] > 0 else "finished_eating", events)
            elif c["state"] == "waiting" and closing:
                self._leave(c, "closing", events)
            elif c["state"] == "waiting" and c["patience_ticks_left"] == 0:
                self._leave(c, "patience", events)
        if closing:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        # 5. lịch khách
        self._schedule_customer(events)
        return events

    # --- tương tác ----------------------------------------------------------------
    def _interact(self, events):
        r = self.t["interact_radius"]
        cands = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= r:
                cands.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= r:
                cands.append((d, 1, id_key(tb["id"]), "table", tb))
        if not cands:
            return
        _, _, _, kind, obj = min(cands, key=lambda x: x[:3])
        if kind == "stove":
            self._use_stove(obj, events)
        else:
            self._use_table(obj, events)

    def _use_stove(self, s, events):
        if s["state"] == "idle":
            waiting = [c for c in self.customers if c["order_status"] == "reserved"]
            if not waiting:
                return
            c = min(waiting, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
            dish = self.menu[c["dish_id"]]
            items = []
            for k in sorted(c["reserved"]):
                n = c["reserved"][k]
                self.stock[k] = self.stock.get(k, 0) - n
                items.extend([k] * n)
            c["reserved"], c["order_status"], c["base_price"] = {}, "assigned", dish["price"]
            s["state"], s["cook_ticks_left"], s["ready_ticks"] = "cooking", _ticks(dish["cook_s"]), 0
            s["dish"] = {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": dish["price"]}
            events.append(("cook_started", dict(self._stove_ev(s), items=items, base_price=dish["price"])))
        elif s["state"] == "ready" and self.hand is None:
            ev = self._stove_ev(s)
            self.hand = s["dish"]
            s["state"], s["dish"], s["ready_ticks"] = "idle", None, 0
            events.append(("dish_picked", ev))

    def _use_table(self, tb, events):
        if self.hand is None:
            return
        c = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
        if c is None or c["state"] != "waiting" or c["id"] != self.hand["order_id"]:
            return
        price = self.hand["base_price"]
        ratio = c["patience_ticks_left"] / self.patience_max
        tip = math.floor(price * self.t["tip_rate"] + 1e-9) if ratio >= self.t["tip_min_patience_ratio"] else 0
        c["state"], c["order_status"] = "eating", "served"
        c["eat_ticks_left"], c["base_price"], c["tip"] = _ticks(self.t["eat_s"]), price, tip
        self.hand = None
        events.append(("served", {"order_id": c["id"], "table_id": tb["id"], "dish_id": c["dish_id"],
                                  "patience_ticks_left": c["patience_ticks_left"], "base_price": price, "tip": tip}))

    # --- khách --------------------------------------------------------------------
    def _pay(self, c, reason, events):
        amount = c["base_price"] + c["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if c["tip"] > 0:
            self._add_reputation(self.t["tip_reputation"])
        self.customers.remove(c)
        events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": c["base_price"],
                                "tip": c["tip"], "amount": amount, "reason": reason}))

    def _leave(self, c, reason, events):
        if reason == "patience":
            self._add_reputation(self.t["left_reputation_delta"])
        # nhả phần giữ thô (chưa trừ kho vật lý); bỏ món của đơn trên bếp hoặc tay, nguyên liệu đã dùng mất
        for s in self.stoves:
            if s["dish"] is not None and s["dish"]["order_id"] == c["id"]:
                s["state"], s["dish"], s["cook_ticks_left"], s["ready_ticks"] = "idle", None, 0, 0
        if self.hand is not None and self.hand["order_id"] == c["id"]:
            self.hand = None
        self.customers.remove(c)
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"], "reason": reason,
                                         "reputation": self.reputation}))

    def _schedule_customer(self, events):
        if not self.random_customers:
            return
        first = int(self.t["first_customer_tick"])
        every = _ticks(self.t["customer_interval_s"])
        if self.phase_tick < first or (self.phase_tick - first) % every != 0:
            return
        busy = {c["table_id"] for c in self.customers}
        free = [tb for tb in self.tables if tb["id"] not in busy]  # tables đã sắp theo id
        if not free:
            return
        dishes = [d for d in sorted(self.menu) if self._can_make(d)]
        if not dishes:
            events.append(("no_dish", {}))
            return
        dish_id = dishes[self.rng.get("customer_dish").randrange(len(dishes))]
        table = free[0]
        cid = self.ids.new("C")
        self.customers.append({"id": cid, "table_id": table["id"], "dish_id": dish_id,
                               "order_tick": self.phase_tick, "state": "waiting",
                               "patience_ticks_left": self.patience_max, "eat_ticks_left": 0,
                               "order_status": "reserved", "reserved": dict(self.menu[dish_id]["recipe"]),
                               "base_price": None, "tip": 0})
        events.append(("customer_arrived", {"order_id": cid, "table_id": table["id"], "dish_id": dish_id}))

    def _available(self) -> dict:
        """Kho khả dụng = tồn vật lý trừ phần đang giữ chỗ."""
        out = dict(self.stock)
        for c in self.customers:
            for k, n in c["reserved"].items():
                out[k] = out.get(k, 0) - n
        return out

    def _can_make(self, dish_id) -> bool:
        avail = self._available()
        return all(avail.get(k, 0) >= n for k, n in self.menu[dish_id]["recipe"].items())

    # --- tiện ích -----------------------------------------------------------------
    def _add_reputation(self, delta):
        r = round(self.reputation + delta, 6)  # tránh sai số float làm lệch floor(reputation) của điểm
        self.reputation = min(float(self.t["reputation_max"]), max(float(self.t["reputation_min"]), r))

    @staticmethod
    def _stove_ev(s):
        return {"stove_id": s["id"], "order_id": s["dish"]["order_id"], "dish_id": s["dish"]["dish_id"]}

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
