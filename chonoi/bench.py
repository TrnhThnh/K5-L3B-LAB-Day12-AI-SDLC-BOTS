"""Benchmark có render (Ticket-04 mục 1, `bench_cmd`).

    python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json [--frame-out last.png]

Cảnh đo: buổi sáng lõi v1.2/v1.3 (độ tươi, cá bơi, Cá Sấu, hiệu ứng mặc định), Út Sen đứng yên ở bến.
Mô phỏng chạy đúng 60 tick/s theo đồng hồ thật (bước cố định, tối đa 5 bước bù mỗi khung) và mỗi khung
render toàn bộ cảnh vào framebuffer RGB 1280×720 bằng phần mềm (chỉ thư viện chuẩn, chạy được trên máy
không có màn hình). Làm nóng 3 s rồi đo `--duration` s, ghi đúng 5 trường:
    avg_fps = frames / measured_s
    p1_low_fps = 1 / (thời gian trung bình của max(1, ceil(0.01 × frames)) khung chậm nhất, tính bằng giây)
    load_ms = mili giây từ lúc khởi chạy module tới khung đầu tiên của cảnh đo được render xong
Cửa sổ trình duyệt (`chonoi.live`) vẽ cùng snapshot này bằng canvas; bench đo đường render phần mềm.
"""

import time

T_LAUNCH = time.perf_counter()  # đặt trước mọi import nặng để load_ms tính cả thời gian nạp module

import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import struct  # noqa: E402
import sys  # noqa: E402
import zlib  # noqa: E402

from .contract import load_contract  # noqa: E402
from .errors import BadInput  # noqa: E402
from .inputs import InputPlayer  # noqa: E402
from .runner import Session  # noqa: E402

W, H = 1280, 720
WARMUP_S = 3.0
TICK_S = 1.0 / 60.0
MAX_CATCHUP = 5

KIND_RGB = {"ca_loc": (124, 154, 82), "ca_linh": (214, 230, 242), "ca_keo": (217, 160, 102),
            "bong_dien_dien": (242, 194, 48), "bong_sung": (232, 121, 156), "keo_neo": (143, 207, 107)}


class Frame:
    """Framebuffer RGB. Mọi hình vẽ quy về tô hình chữ nhật theo từng hàng (nhanh trong Python thuần)."""

    def __init__(self):
        self.buf = bytearray(W * H * 3)
        self._rows = {}

    def _row(self, rgb, n):
        key = (rgb, n)
        r = self._rows.get(key)
        if r is None:
            r = self._rows[key] = bytes(rgb) * n
        return r

    def rect(self, x0, y0, x1, y1, rgb):
        x0, x1 = max(0, int(x0)), min(W, int(x1))
        y0, y1 = max(0, int(y0)), min(H, int(y1))
        if x0 >= x1 or y0 >= y1:
            return
        row = self._row(rgb, x1 - x0)
        b = self.buf
        for y in range(y0, y1):
            i = (y * W + x0) * 3
            b[i:i + len(row)] = row

    def ellipse(self, cx, cy, rx, ry, rgb):
        """Ellipse đặc, tô theo từng hàng."""
        ry_i = max(1, int(ry))
        for dy in range(-ry_i, ry_i + 1):
            half = rx * math.sqrt(max(0.0, 1 - (dy / ry) ** 2))
            self.rect(cx - half, cy + dy, cx + half + 1, cy + dy + 1, rgb)

    def bar(self, x, y, w, h, frac, rgb):
        self.rect(x, y, x + w, y + h, (20, 24, 30))
        self.rect(x, y, x + w * max(0.0, min(1.0, frac)), y + h, rgb)

    def png(self, path):
        raw = b"".join(b"\x00" + bytes(self.buf[y * W * 3:(y + 1) * W * 3]) for y in range(H))

        def chunk(tag, data):
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

        with open(path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
                    + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


class GatherRenderer:
    """Vẽ cảnh lặn như cửa sổ chơi: trời, nước phù sa, nút hái, cá, Cá Sấu, người chơi, HUD oxy/Máu/giỏ."""

    TOP, BOTTOM, SKY = 96, 92, 5

    def __init__(self, tuning):
        g = tuning["gather"]
        self.g = g
        X, D = g["bounds"]["x"][1], g["bounds"]["d"][1]
        self.s = min((W - 20) / (X + 4), (H - self.TOP - self.BOTTOM) / (D + self.SKY + 1))
        self.ox = (W - self.s * (X + 4)) / 2 + 2 * self.s
        self.oy = self.TOP + self.SKY * self.s
        self.X, self.D = X, D
        self.background = self._background()

    def sx(self, x):
        return self.ox + x * self.s

    def sy(self, d):
        return self.oy + d * self.s

    def _background(self):
        f = Frame()
        f.rect(0, 0, W, H, (16, 22, 28))
        for y in range(self.TOP, int(self.oy)):  # ánh hồng buổi sớm
            t = (y - self.TOP) / max(1, self.oy - self.TOP)
            f.rect(0, y, W, y + 1, (int(247 + 6 * t), int(201 + 30 * t), int(168 + 32 * t)))
        y0, y1 = int(self.oy), int(self.sy(self.D))
        for y in range(y0, y1):  # nước phù sa
            t = (y - y0) / max(1, y1 - y0)
            f.rect(self.sx(0), y, self.sx(self.X), y + 1, (int(180 - 137 * t), int(138 - 102 * t), int(78 - 58 * t)))
        f.rect(0, 0, W, 88, (12, 18, 24))
        f.rect(0, H - self.BOTTOM, W, H, (12, 18, 24))
        return bytes(f.buf)

    def draw(self, frame, snap):
        frame.buf[:] = self.background
        s = self.s
        for n in snap["nodes"]:
            col = KIND_RGB.get(n["kind"], (190, 190, 190)) if n["ready"] else (90, 80, 60)
            frame.ellipse(self.sx(n["pos"][0]), self.sy(n["pos"][1]), 0.9 * s, 0.4 * s, col)
        for fsh in snap["fish"]:
            frame.ellipse(self.sx(fsh["pos"][0]), self.sy(fsh["pos"][1]), 0.9 * s, 0.45 * s,
                          KIND_RGB.get(fsh["kind"], (190, 190, 190)))
        for m in snap.get("monsters", []):
            frame.ellipse(self.sx(m["pos"][0]), self.sy(m["pos"][1]), 2.2 * s, 0.6 * s,
                          (106, 143, 58) if m["state"] == "chase" else (79, 107, 44))
        p = snap["player"]
        frame.ellipse(self.sx(p["pos"][0]), self.sy(p["pos"][1]), 0.6 * s, 0.6 * s, (255, 138, 61))
        # HUD: oxy, Máu, giỏ kèm độ tươi
        frac = p["oxygen_ticks"] / p["oxygen_max_ticks"]
        frame.bar(130, 12, 260, 28, frac, (79, 195, 247) if frac >= 0.25 else (255, 23, 68))
        for i in range(p["hp_max"]):
            frame.rect(410 + i * 30, 14, 434 + i * 30, 38, (255, 107, 129) if i < p["hp"] else (80, 40, 48))
        spoil = 30
        for i in range(snap["hold_capacity"]):
            x0 = 16 + i * 34
            frame.rect(x0, H - 80, x0 + 30, H - 50, (40, 46, 52))
            if i < len(snap["hold"]):
                it = snap["hold"][i]
                frame.rect(x0 + 3, H - 77, x0 + 27, H - 53, KIND_RGB.get(it["kind"], (190, 190, 190)))
                frame.bar(x0, H - 46, 30, 5, it["fresh"] / 100, (102, 187, 106) if it["fresh"] >= spoil else (183, 28, 28))


def run_bench(seed, duration, out_path, frame_out=None):
    if duration <= 0:
        raise BadInput("--duration phải > 0")
    tuning = load_contract()["tuning"]
    sess = Session("gather", tuning, {}, seed)  # buổi sáng lõi mặc định, không input: Út Sen đứng ở bến
    idle = InputPlayer([])
    renderer = GatherRenderer(tuning)
    frame = Frame()
    load_ms = None
    times = []
    start = last = prev_end = time.perf_counter()
    acc = 0.0
    measure_from = start + WARMUP_S
    stop_at = measure_from + duration
    while True:
        now = time.perf_counter()
        acc += now - last
        last = now
        steps = 0
        while acc >= TICK_S and steps < MAX_CATCHUP and not sess.done:
            sess.step(idle.advance(sess.tick))
            acc -= TICK_S
            steps += 1
        if steps == MAX_CATCHUP:
            acc = 0.0  # chậm quá thì bỏ bù, giống cửa sổ chơi
        renderer.draw(frame, sess.snapshot())
        end = time.perf_counter()
        if load_ms is None:
            load_ms = int(round((end - T_LAUNCH) * 1000))
        if prev_end >= measure_from:  # khung nằm trọn trong khoảng đo: thời gian = khoảng giữa hai khung liên tiếp
            times.append(end - prev_end)
        prev_end = end
        if end >= stop_at:
            break
    measured_s = sum(times)
    frames = len(times)
    k = max(1, math.ceil(0.01 * frames))
    slowest = sorted(times, reverse=True)[:k]
    # measured_s giữ nguyên độ chính xác để frames / measured_s tính lại đúng avg_fps (làm tròn measured_s
    # rồi so sẽ lệch tới ~0.6 FPS khi FPS cao và --duration ngắn)
    result = {"avg_fps": round(frames / measured_s, 2), "p1_low_fps": round(1.0 / (sum(slowest) / k), 2),
              "frames": frames, "measured_s": measured_s, "load_ms": load_ms}
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f)
        f.write("\n")
    if frame_out:
        frame.png(frame_out)
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.bench")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--duration", type=float, required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--frame-out", dest="frame_out", help="ghi khung cuối ra PNG (bằng chứng render)")
    a = p.parse_args(argv)
    try:
        res = run_bench(a.seed, a.duration, a.out, a.frame_out)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
