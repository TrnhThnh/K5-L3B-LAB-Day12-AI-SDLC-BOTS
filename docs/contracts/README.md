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

## 4. Thay đổi ở Test Contract v1.1 (Phase 2)

- `game.contract.json`: `contract_version: "1.1"`, số chuẩn Ticket-02 mục 1. Nguyên liệu thêm `ca_keo`, `keo_neo` (file kho nhận 6 loại). `fish_initial` giờ là **số đàn** (8), vị trí chọn theo seed từ `fish_spawn_x` × `fish_spawn_depths`.
- Snapshot gather thêm `fish[].age_ticks` và `monsters[].{id, kind, pos, waypoints, target_idx, state, state_ticks_left, recoil_dir}`.
- Sự kiện gather mới:

| Sự kiện | `data` |
|---|---|
| `fish_spawned` | `{id, kind, pos}` |
| `monster_hit` | `{monster_id, hp, lost, pos}` (`pos` là vị trí người chơi, `lost` theo LIFO) |
| `faint` | thêm `cause: "monster"`; `lost` là phần giỏ còn lại |

- Thứ tự một bước gather (mục 4.5): đồng hồ, hồi chiêu, bất tử, nút → bơi, oxy, ngạt → Cá Sấu theo id rồi tối đa một hit → tương tác → bắt cá (vị trí cá trước khi bơi) → hết giờ → nếu còn giờ: cá bơi, sinh cá.
- `GatherSim(tuning, scenario, streams, ids, day=1, oxygen_max_s=None, hp_max=None)`: vòng ngày truyền số Ngày (bố trí Cá Sấu) và cấp nâng cấp đang áp dụng.

## 5. Vòng ngày `--mode day` (Chiến) và giao diện với quán, Shop (Thịnh)

- `chonoi/sim/day.py`: `DaySim` giữ `money`, `earned`, `reputation`, `upgrades` (đã mua), `active_upgrades` (đang áp dụng), số Ngày và `days_completed`.
- Dựng quán: `QuanSim(tuning, scenario_quan, streams, ids, inventory=<kho bàn giao>, money=, earned=, reputation=, dishes=<id món của kế hoạch Ngày>)`. Quán chạy riêng thì `dishes=None` (cả 6 món).
- Dựng gather: `GatherSim(..., day=<Ngày>, oxygen_max_s=<cấp oxy đang áp>, hp_max=<cấp áo phao đang áp>)`.
- Shop: `ShopPhase(shop_cfg, stock)` với `step(inp, day)`. Bản hiện tại là bản tối thiểu (mua `oxygen`, `hp`; `bought`, `buy_failed` với `funds`/`max_level`/`unknown`; `shop_done`; tự đóng sau `shop.max_ticks`). Thịnh tiếp quản file này nếu cần thêm.
- Input v1.1: nút `pause`, `shop_done`; `buy` là chuỗi, chỉ có tác dụng ở đúng frame khai báo. Pause xử lý trong `Session.step` (runner) cho cả ba mode.
- Sự kiện vòng ngày: `day_start {}`, `day_plan {dishes, ingredients}`, `phase_start {}`, `paused {}`, `resumed {}`, `bought {upgrade, level, price, money}`, `buy_failed {action, reason}`, `shop_end {reason: done/time}`. Vỏ event của `day` có thêm `day`.
- Snapshot `day` có thêm `day`, `day_plan`, `upgrades`, `active_upgrades`; pha `shop` có `stock` dư từ ca và `time_left_ticks` tới lúc đóng. Dòng `end` có `days_completed`, hoàn thành đủ Ngày thì `reason: "days_complete"`.

## Lịch sử thay đổi hợp đồng

| Ngày | Ai | Đổi gì | Lý do |
|---|---|---|---|
| 2026-11-21 | Chiến | Bản đầu: kho, giao diện UI, sự kiện gather | Kickoff Phase 1 |
| 2026-11-21 | Chiến | Đổi `data` sự kiện gather, thêm sự kiện quán theo PRD-0 mục E | Có PRD-0 thật; bản đầu tự đặt tên trường |
| 2026-11-21 | Chiến | Vòng ngày `day`, pause, Shop tối thiểu, input `buy`/`shop_done`/`pause` | Ticket-02 mục 2, 4 |
| 2026-11-21 | Chiến | Contract v1.1: số chuẩn, 6 nguyên liệu, 6 món, 2 bếp, 4 bàn, cá bơi/sinh, Cá Sấu, `day_plan`, `shop` | Ticket-02 (Phase 2) |
