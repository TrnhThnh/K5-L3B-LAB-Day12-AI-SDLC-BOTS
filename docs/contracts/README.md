# Hợp đồng tích hợp của nhóm BOTS

Người giữ: Chiến (Integrator). Muốn đổi thì nhắn trong kênh nhóm, rồi ghi lý do ở cuối file này.

## 1. Schema file kho (PRD-0 mục G)

- Ghi **một lần** khi có `gather_end`. Runner lo việc này qua `--inventory-out`. Hết `--ticks` mà chưa có `gather_end` thì không ghi.
- Dạng: `{"items": {<nguyên liệu>: <số nguyên > 0>}}`, khóa sắp theo bảng chữ cái, bỏ mục bằng 0.
- Nguyên liệu Phase 1: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
- Ngất (`fainted`) thì kho rỗng: `{"items": {}}`.
- File mẫu: [`inventory.sample.json`](inventory.sample.json).

`quan` đọc kho qua `--inventory` (hoặc `scenario.quan.stock`, không được dùng cả hai) và đưa vào `snapshot.stock`.

## 2. Giao diện `sim/*` ↔ `client/ui`

- UI **chỉ đọc snapshot** (`Session.snapshot()`) và gửi input qua `LiveInputs.set(move=[x, y], interact=bool, catch=bool)`. UI không gọi thẳng hàm luật.
- Trường snapshot `gather` mà UI dùng: `player.{pos, vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, at_surface, catch_cd_ticks}`, `hold` (thứ tự nhặt, cuối mảng là mới nhất), `hold_count`, `hold_capacity`, `nodes[].{id, kind, pos, ready, regrow_ticks}`, `fish[].{id, kind, pos, heading_deg}`.
- Trường snapshot `quan`: `player.pos`, `stock`, `hand`, `stoves[]`, `tables[]`, `customers[]` (Thịnh bổ sung khi làm lát 3–4).

## 3. Sự kiện

### Gather (Chiến phát; UI và test nghe)

| Sự kiện | `data` | Khi nào |
|---|---|---|
| `node_regrown` | `{node_id}` | `regrow_ticks` của nút về 0 |
| `dive` | `{pos}` | đầu bước ở mặt nước (d ≤ `surface_depth`), cuối bước ở dưới nước |
| `surface` | `{pos}` | ngược lại với `dive` |
| `oxygen_empty` | `{pos}` | oxy từ số dương về 0 |
| `choke` | `{hp}` (Máu còn lại) | đủ `choke_interval_ticks` tick liền ở dưới nước với oxy = 0 |
| `faint` | `{pos}` | Máu về 0, ngay sau `choke` |
| `gather` | `{node_id, kind, count}` | hái được nút ở mặt nước |
| `fish_caught` | `{fish_id, kind, count}` | bắt được đàn cá ở dưới nước |
| `hold_full` | `{hold_count, hold_capacity}` | giỏ không chứa hết phần vừa hái hoặc bắt |
| `gather_end` | `{reason, inventory: {items}}` | `docked` / `time` / `fainted` |

Thứ tự trong một bước: `node_regrown` → `dive`/`surface` → `oxygen_empty` → `choke` → `faint` → `gather_end(fainted)` (dừng ở đây nếu ngất) → `gather_end(docked)` hoặc `gather`/`hold_full` → `fish_caught`/`hold_full` → `gather_end(time)`.

### Quán (Thịnh phát; theo PRD-0 mục E)

Tên lấy từ khung `chonoi/sim/quan.py`: `customer_left`, `no_dish`, `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid`, `quan_end`. Thịnh điền `data` khi làm lát 3–4.

## Lịch sử thay đổi hợp đồng

| Ngày | Ai | Đổi gì | Lý do |
|---|---|---|---|
| 2026-11-21 | Chiến | Bản đầu: kho, giao diện UI, sự kiện gather | Kickoff Phase 1 |
