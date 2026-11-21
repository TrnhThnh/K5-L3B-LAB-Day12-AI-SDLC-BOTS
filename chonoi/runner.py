"""Vòng tick (Contract B, mô hình tick).

Thứ tự ghi: [event tick 0 của day] -> snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot
(nếu tới lượt, đổi pha hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

Pause (Test Contract v1.1 mục 4.2), xử lý ở đây cho cả ba mode: xét cạnh pause trước. Bước vào pause chỉ tăng tick
ngoài và phát `paused`; khi còn pause, bỏ qua cạnh hành động và buy, sim_tick/phase_tick/timer đứng yên. Cạnh lên
tiếp theo phát `resumed` rồi chạy gameplay ngay trong bước đó.

`Session` là API bước tick dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`).
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    if mode == "day":
        return DaySim(tuning, scenario, streams, ids, days=days)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False
        self.force_snapshot = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def _wrap(self, name, data, phase, day=None):
        if self.mode == "day":  # vỏ event của day có thêm `day` (Ngày lúc event xảy ra)
            return {"type": "event", "tick": self.tick, "phase": phase, "day": day if day is not None else self.sim.day,
                    "name": name, "data": data}
        return {"type": "event", "tick": self.tick, "phase": phase, "name": name, "data": data}

    def initial_rows(self) -> list:
        """Event ở tick 0 trước snapshot đầu (day_start, day_plan, phase_start của Ngày 1)."""
        return [self._wrap(*e) for e in getattr(self.sim, "initial_events", [])]

    def _state(self):
        if self.sim.done:
            return "finished"
        return "paused" if self.paused else "playing"

    def snapshot(self) -> dict:
        sim = self.sim
        mult = self.tuning["score"]["reputation_multiplier"]
        s = {"type": "snapshot", "tick": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode, "phase": sim.phase,
             "phase_tick": sim.phase_tick, "state": self._state(), "time_left_ticks": sim.time_left_ticks,
             "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
             "score": sim.earned + mult * math.floor(sim.reputation)}
        s.update(sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        self.tick += 1
        self.force_snapshot = False
        phase = self.sim.phase
        rows = []
        if inp.pressed("pause"):
            self.paused = not self.paused
            if self.paused:
                return [self._wrap("paused", {}, phase)]
            rows.append(self._wrap("resumed", {}, phase))
        elif self.paused:
            return []
        self.sim_tick += 1
        out = self.sim.step(inp)
        for e in out:
            rows.append(self._wrap(*e) if len(e) > 2 else self._wrap(e[0], e[1], phase))
        self.force_snapshot = bool(getattr(self.sim, "phase_changed", False))
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        mult = self.tuning["score"]["reputation_multiplier"]
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
               "state": "finished" if sim.done else self._state(),
               "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
               "score": sim.earned + mult * math.floor(sim.reputation)}
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_rows():
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done or sess.force_snapshot:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
