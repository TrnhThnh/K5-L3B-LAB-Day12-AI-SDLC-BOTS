"""Vòng ngày (`--mode day`, Ticket-02 mục 2 và Test Contract v1.1 mục 4).

DayIntro -> gather -> EveningIntro -> quan -> DayResult -> Shop -> Ngày kế (tối đa --days Ngày).
Headless bỏ qua các màn hình intro/result; chỉ chạy ba pha gameplay gather, quan, shop.

Đổi pha (mục 4.5):
  - đầu Ngày: day_start -> day_plan -> phase_start(gather), cùng tick
  - sau gather_end: dựng quán với kho bàn giao (trong bộ nhớ) và phát phase_start(quan) cùng tick, kể cả khi ngất
  - sau quan_end: dựng Shop và phát phase_start(shop) cùng tick
  - đóng Shop: shop_end, tăng days_completed, kết thúc hoặc dựng Ngày kế ngay tick đó
  - pha mới chỉ chạy gameplay từ bước sau; event kết thúc mang pha cũ
Tiền, earned, uy tín và cấp đã mua giữ qua Ngày. Cấp đã mua chỉ chép sang active_upgrades khi dựng Ngày mới.

Nhóm BOTS: Chiến viết vòng ngày; Shop (`ShopPhase`) là bản tối thiểu để vòng ngày chạy, Thịnh tiếp quản.
"""

import copy

from .gather import GatherSim
from .quan import QuanSim

TICK = 60


def plan_ingredients(menu, dishes):
    ing = {}
    for dish, n in dishes.items():
        for k, v in menu[dish]["recipe"].items():
            ing[k] = ing.get(k, 0) + v * n
    return {k: ing[k] for k in sorted(ing)}


class ShopPhase:
    """Shop cuối Ngày: mua cấp kế tiếp (oxygen, hp), đóng bằng shop_done hoặc sau shop.max_ticks."""

    phase = "shop"

    def __init__(self, shop_cfg, stock):
        self.cfg = shop_cfg
        self.stock = list(stock)  # kho dư từ ca, bỏ sau Shop
        self.time_left_ticks = int(shop_cfg["max_ticks"])
        self.phase_tick = 0
        self.done = False
        self.reason = None

    def step(self, inp, day):
        """Một bước Shop; `day` là DaySim (giữ money và upgrades). Trả list (name, data)."""
        ev = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if inp.buy:  # xử lý một buy trước cạnh shop_done, kể cả bước cuối
            ev.append(self._buy(inp.buy, day))
        if inp.pressed("shop_done"):
            self.done, self.reason = True, "done"
        elif self.time_left_ticks <= 0:
            self.done, self.reason = True, "time"
        if self.done:
            ev.append(("shop_end", {"reason": self.reason}))
        return ev

    def _buy(self, kind, day):
        levels = self.cfg["upgrades"].get(kind)
        if levels is None:
            return ("buy_failed", {"action": kind, "reason": "unknown"})
        cur = day.upgrades.get(kind, 0)
        if cur >= len(levels):
            return ("buy_failed", {"action": kind, "reason": "max_level"})
        nxt = levels[cur]
        if day.money < nxt["price"]:  # đủ đúng giá vẫn mua được
            return ("buy_failed", {"action": kind, "reason": "funds"})
        day.money -= nxt["price"]  # trừ money, giữ earned và điểm
        day.upgrades[kind] = nxt["level"]
        return ("bought", {"upgrade": kind, "level": nxt["level"], "price": nxt["price"], "money": day.money})

    def snapshot(self):
        return {"stock": self.stock}


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.t = tuning
        self.streams = streams
        self.ids = ids
        self.days = days
        self.tpl_gather = scenario.get("gather", {})
        self.tpl_quan = scenario.get("quan", {})
        d = scenario.get("day", {})
        self.money = d.get("money", 0)
        self.earned = d.get("earned", 0)
        self.reputation = float(d.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = dict(d.get("upgrades", {}))
        self.active_upgrades = {}
        self.plans = {}
        for p in tuning["day_plan"]:
            self.plans[p["day"]] = {"dishes": dict(p["dishes"]), "ingredients": dict(p["ingredients"])}
        for p in d.get("day_plan", []):
            self.plans[p["day"]] = {"dishes": dict(p["dishes"]),
                                    "ingredients": plan_ingredients(tuning["menu"], p["dishes"])}
        self.day = 0
        self.days_completed = 0
        self.cur = None
        self.done = False
        self.reason = None
        self.phase_changed = False
        self.initial_events = []
        self._start_day(self.initial_events)

    # --- trạng thái chung cho runner ------------------------------------------------
    @property
    def phase(self):
        return self.cur.phase

    @property
    def phase_tick(self):
        return self.cur.phase_tick

    @property
    def time_left_ticks(self):
        return self.cur.time_left_ticks

    def _sync_from_quan(self):
        q = self.cur
        self.money, self.earned, self.reputation = q.money, q.earned, q.reputation

    def plan(self):
        return self.plans.get(self.day, {"dishes": {}, "ingredients": {}})

    # --- dựng pha -------------------------------------------------------------------
    def _level_value(self, kind, key):
        lv = self.active_upgrades.get(kind, 0)
        if lv <= 0:
            return None
        return self.t["shop"]["upgrades"][kind][lv - 1][key]

    def _start_day(self, ev):
        self.day += 1
        self.active_upgrades = dict(self.upgrades)
        self.cur = GatherSim(self.t, copy.deepcopy(self.tpl_gather), self.streams, self.ids, day=self.day,
                             oxygen_max_s=self._level_value("oxygen", "oxygen_max_s"),
                             hp_max=self._level_value("hp", "hp_max"))
        self.phase_changed = True
        ev.append(("day_start", {}, "gather", self.day))
        ev.append(("day_plan", copy.deepcopy(self.plan()), "gather", self.day))
        ev.append(("phase_start", {}, "gather", self.day))

    def _start_quan(self, items, ev):
        self.cur = QuanSim(self.t, copy.deepcopy(self.tpl_quan), self.streams, self.ids, inventory=items,
                           money=self.money, earned=self.earned, reputation=self.reputation,
                           dishes=list(self.plan()["dishes"]))
        self.phase_changed = True
        ev.append(("phase_start", {}, "quan", self.day))

    def _start_shop(self, stock, ev):
        self.cur = ShopPhase(self.t["shop"], stock)
        self.phase_changed = True
        ev.append(("phase_start", {}, "shop", self.day))

    # --- một bước -------------------------------------------------------------------
    def step(self, inp):
        """Trả list (name, data, phase, day). Event kết thúc mang pha và Ngày cũ."""
        self.phase_changed = False
        ev = []
        if self.cur.phase == "gather":
            ev += [(n, d, "gather", self.day) for n, d in self.cur.step(inp)]
            if self.cur.done:
                self._start_quan(self.cur.inventory_items(), ev)
        elif self.cur.phase == "quan":
            ev += [(n, d, "quan", self.day) for n, d in self.cur.step(inp)]
            self._sync_from_quan()
            if self.cur.done:
                self._start_shop(self.cur.stock, ev)
        else:
            ev += [(n, d, "shop", self.day) for n, d in self.cur.step(inp, self)]
            if self.cur.done:
                self.days_completed += 1
                if self.days_completed >= self.days:
                    self.done, self.reason = True, "days_complete"
                else:
                    self._start_day(ev)
        return ev

    def snapshot(self) -> dict:
        s = self.cur.snapshot()
        s.update({"day": self.day, "day_plan": copy.deepcopy(self.plan()),
                  "upgrades": dict(sorted(self.upgrades.items())),
                  "active_upgrades": dict(sorted(self.active_upgrades.items()))})
        return s
