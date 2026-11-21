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
- Trường snapshot `quan`: `player.{pos, vel}`, `stock` (kho vật lý, gồm phần đang giữ), `hand` (payload món hoặc null), `stoves[].{id, pos, state, dish, cook_ticks_left, ready_ticks}` (`dish` là payload món), `tables[].{id, pos, customer_id}`, `customers[]` theo PRD-0 mục D.

## 3. Sự kiện

### Gather (Chiến phát; UI và test nghe)

| Sự kiện | `data` | Khi nào |
|---|---|---|
Theo PRD-0 mục E (Test Contract v1.0):

| Sự kiện | `data` | Khi nào |
|---|---|---|
| `node_regrown` | `{node_id}` | `regrow_ticks` của nút từ 1 về 0 |
| `dive` | `{pos}` | đầu bước ở mặt nước (d ≤ `surface_depth`), cuối bước ở dưới nước |
| `surface` | `{pos}` | ngược lại với `dive` |
| `oxygen_empty` | `{oxygen_ticks: 0}` | oxy từ số dương về 0 |
| `choke` | `{hp}` (Máu sau khi trừ) | đủ `choke_interval_ticks` bước dưới nước kết thúc với oxy = 0, tính cả bước vừa chạm 0 |
| `faint` | `{cause: "choke", lost, hp: 0}` | Máu về 0; `lost` là giỏ theo LIFO (nhặt sau bỏ trước) |
| `gather` | `{node_id, kind, amount}` | hái được nút ở mặt nước |
| `fish_caught` | `{fish_id, kind, yield}` | bắt đủ cả đàn ở dưới nước |
| `hold_full` | `{action: "gather"/"catch", node_id hoặc fish_id, required, free}` | giỏ không đủ chỗ; nút hoặc đàn giữ nguyên, không đặt hồi chiêu |
| `gather_end` | `{reason, inventory: {items}}` | `docked` / `time` / `fainted` |

Thứ tự trong một bước: `node_regrown` → `dive`/`surface` → `oxygen_empty` → `choke` → `faint` → `gather_end(fainted)` (dừng ở đây nếu ngất) → `gather_end(docked)` hoặc `gather`/`hold_full` → `fish_caught`/`hold_full` → `gather_end(time)`.

### Quán (Thịnh phát; theo PRD-0 mục E)

Theo PRD-0 mục E:

| Sự kiện | `data` |
|---|---|
| `customer_arrived` | `{order_id, table_id, dish_id}` |
| `no_dish` | `{}` (có bàn mà thiếu món) |
| `cook_started` | `{stove_id, order_id, dish_id, items, base_price}` (`items` là mảng kind, sắp theo kind) |
| `dish_ready` / `dish_picked` | `{stove_id, order_id, dish_id}` |
| `served` | `{order_id, table_id, dish_id, patience_ticks_left, base_price, tip}` |
| `paid` | `{order_id, table_id, base_price, tip, amount, reason: finished_eating/closing}` |
| `customer_left` | `{order_id, table_id, reason: patience/closing, reputation}` |
| `quan_end` | `{reason: "time", money, earned, shift_earned, reputation}` |

Payload món trên tay: `{order_id, dish_id, base_price}`, `order_id` bằng id khách.

## Lịch sử thay đổi hợp đồng

| Ngày | Ai | Đổi gì | Lý do |
|---|---|---|---|
| 2026-11-21 | Chiến | Bản đầu: kho, giao diện UI, sự kiện gather | Kickoff Phase 1 |
| 2026-11-21 | Chiến | Đổi `data` sự kiện gather, thêm sự kiện quán theo PRD-0 mục E | Có PRD-0 thật; bản đầu tự đặt tên trường |
