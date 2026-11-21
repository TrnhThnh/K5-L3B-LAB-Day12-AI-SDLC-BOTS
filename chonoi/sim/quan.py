"""Buổi tối — lịch khách, bếp, phục vụ và thanh toán."""

from math import dist, floor

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, *, day_plan=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        if day_plan is not None:
            dishes = day_plan["dishes"]
            if not dishes or any(dish not in self.menu for dish in dishes):
                raise BadInput("kế hoạch ngày chứa món không hợp lệ")
            self.menu = {dish: self.menu[dish] for dish in dishes}
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.tick = 0
        self.arrivals = scenario.get("random_customers", True)
        self.patience = round(t["patience_s"] * TICK)
        self.customers = sort_by_id([dict(c) for c in scenario.get("customers", [])])
        for c in self.customers:
            if c.get("dish_id") not in self.menu:
                raise BadInput("đơn không thuộc thực đơn hiện tại")
            ids.reserve(c["id"])
            c.setdefault("order_tick", 0)
            c.setdefault("state", "waiting")
            c.setdefault("patience_ticks_left", self.patience)
            recipe = self.menu[c["dish_id"]]["recipe"] if c["state"] == "waiting" else {}
            if c.get("reserved", recipe) != recipe:
                raise BadInput("reserved không khớp trạng thái đơn")
            c["reserved"] = dict(recipe)
        if any(self._available(k) < 0 for k in {k for c in self.customers for k in c["reserved"]}):
            raise BadInput("tổng nguyên liệu giữ chỗ vượt kho")
        # Mỗi món trên bếp/trên tay thuộc đúng một đơn assigned.
        self.owners = {}
        assigned = [c for c in self.customers if c["state"] == "assigned"]
        slots = [(s["id"], s["dish"]) for s in self.stoves if s["dish"]]
        if self.hand:
            slots.append(("hand", self.hand))
        for slot, dish in slots:
            owner = next((c for c in assigned if c["dish_id"] == dish), None)
            if owner is None:
                raise BadInput("món thiếu đơn assigned")
            self.owners[slot] = owner["id"]
            assigned.remove(owner)
        if assigned:
            raise BadInput("đơn assigned thiếu món")
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "available_stock": {k: self._available(k) for k in sorted(self.stock) if self._available(k) > 0},
            "shift_earned": self.shift_earned,
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.tick += 1
        self._advance(events)
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        elapsed = self.tick - self.t["first_customer_tick"]
        if self.time_left_ticks and self.arrivals and elapsed >= 0 and elapsed % round(self.t["customer_interval_s"] * TICK) == 0:
            self._arrive(events)
        if self.time_left_ticks <= 0:
            for c in sort_by_id(self.customers):
                self._finish_customer(c, events)
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _available(self, kind):
        return self.stock.get(kind, 0) - sum(c["reserved"].get(kind, 0) for c in self.customers)

    def _arrive(self, events):
        occupied = {c["table_id"] for c in self.customers}
        table = next((t for t in self.tables if t["id"] not in occupied), None)
        if table is None:
            return
        ident = self.ids.new("C")
        choices = [dish for dish, item in sorted(self.menu.items())
                   if all(self._available(k) >= n for k, n in item["recipe"].items())]
        if not choices:
            events.append(("no_dish", {"customer_id": ident, "table_id": table["id"]}))
            return
        dish = self.rng.get("customer_dish").choice(choices)
        self.customers.append({"id": ident, "table_id": table["id"], "dish_id": dish,
                               "state": "waiting", "order_tick": self.tick, "patience_ticks_left": self.patience,
                               "reserved": dict(self.menu[dish]["recipe"])})

    def _reputation(self, delta):
        self.reputation = min(self.t["reputation_max"], max(self.t["reputation_min"], self.reputation + delta))

    def _advance(self, events):
        for s in self.stoves:
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] -= 1
                if s["cook_ticks_left"] == 0:
                    s["state"] = "ready"
                    events.append(("dish_ready", {"stove_id": s["id"], "dish_id": s["dish"]}))
        for c in sort_by_id(self.customers):
            timer = "eat_ticks_left" if c["state"] == "eating" else "patience_ticks_left"
            c[timer] = max(0, c[timer] - 1)
            if c[timer] == 0 and (self.time_left_ticks or c["state"] == "eating"):
                self._finish_customer(c, events)

    def _finish_customer(self, c, events):
        data = {"customer_id": c["id"], "dish_id": c["dish_id"]}
        if c["state"] == "eating":
            amount = c["price"] + c["tip"]
            self.money += amount
            self.earned += amount
            self.shift_earned += amount
            if c["tip"]:
                self._reputation(self.t["tip_reputation"])
            events.append(("paid", dict(data, price=c["price"], tip=c["tip"])))
        else:
            if self.time_left_ticks:
                self._reputation(self.t["left_reputation_delta"])
            for s in self.stoves:
                if self.owners.get(s["id"]) == c["id"]:
                    self.owners.pop(s["id"])
                    s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
            if self.owners.get("hand") == c["id"]:
                self.owners.pop("hand")
                self.hand = None
            events.append(("customer_left", data))
        self.customers.remove(c)

    def _interact(self, events):
        # Stable min keeps the stove first and then the natural ID order on ties.
        targets = self.stoves + self.tables
        target = min(targets, key=lambda e: dist(self.pos, e["pos"]), default=None)
        if target is None or dist(self.pos, target["pos"]) > self.t["interact_radius"]:
            return
        ident = target["id"]
        if target in self.stoves:
            if target["state"] == "ready" and self.hand is None and self.t["carry_limit"] >= 1:
                self.hand = target["dish"]
                self.owners["hand"] = self.owners.pop(ident)
                target.update(state="idle", dish=None, ready_ticks=0)
                events.append(("dish_picked", {"stove_id": ident, "dish_id": self.hand}))
            elif target["state"] == "idle":
                waiting = (c for c in self.customers if c["state"] == "waiting")
                c = min(waiting, key=lambda c: (c["order_tick"], id_key(c["table_id"])), default=None)
                if c is None:
                    return
                for k, n in c["reserved"].items():
                    self.stock[k] -= n
                c.update(state="assigned", reserved={})
                dish = c["dish_id"]
                self.owners[ident] = c["id"]
                target.update(state="cooking", dish=dish, cook_ticks_left=round(self.menu[dish]["cook_s"] * TICK))
                events.append(("cook_started", {"customer_id": c["id"], "stove_id": ident, "dish_id": dish}))
            return
        c = next((c for c in self.customers if c["table_id"] == ident), None)
        if c and self.owners.get("hand") == c["id"]:
            price = self.menu[self.hand]["price"]
            qualifies = c["patience_ticks_left"] >= self.patience * self.t["tip_min_patience_ratio"]
            tip = floor(price * self.t["tip_rate"]) if qualifies else 0
            c.update(state="eating", price=price, tip=tip, eat_ticks_left=round(self.t["eat_s"] * TICK))
            events.append(("served", {"customer_id": c["id"], "dish_id": self.hand, "table_id": ident}))
            self.hand = None
            self.owners.pop("hand")

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
