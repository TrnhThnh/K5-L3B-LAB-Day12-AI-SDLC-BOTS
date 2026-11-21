# Phân công nhóm BOTS (2 người)

Nhóm có hai người nên mỗi người giữ hai module và hai vai. Chia theo file luật: Chiến làm buổi sáng (`gather`), Thịnh làm buổi tối (`quan`). Hai người sửa hai file khác nhau nên ít khi bị conflict.

| | Chiến (`duongchien147`) | Thịnh (`TrnhThnh`) |
|---|---|---|
| Module | `sim/gather` + `client/ui` | `sim/quan` + `qa` |
| Vai | PO + Integrator | QA lead + Scrum/Release |
| File được sửa | `chonoi/sim/gather.py`, `chonoi/live.py`, `chonoi/web/`, `tests/test_gather_rules.py` | `chonoi/sim/quan.py`, `chonoi/scenario.py` (phần quán), `tests/test_quan_rules.py` |
| File chung | `game.contract.json`, `docs/contracts/`, `AGENTS.md`: chỉ Chiến sửa. Thịnh muốn đổi thì nhắn Chiến. | |

Đánh dấu `[x]` khi xong và commit file này cùng code.

## Việc của Thịnh

### Bắt đầu (làm ngay)
- [ ] Vào repo, *Settings → Collaborators*, thêm `duongchien147` với quyền Write. Kiểm repo đang để public.
- [ ] `git pull`, rồi chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` và thấy `OK` (51 test). Máy Windows không có `python3` thì xem mục Lệnh trong `AGENTS.md`.
- [ ] Đọc `docs/contracts/README.md` (schema kho, sự kiện), `docs/clarify.md` và docstring đầu `chonoi/sim/quan.py`.

### Phase 1: luật quán (`chonoi/sim/quan.py`)
Số liệu lấy từ `tuning.quan` và `tuning.menu` trong `game.contract.json`, không ghi số thẳng vào code. Chỗ nào đề chưa rõ thì ghi vào `docs/clarify.md` rồi báo Chiến.

Lát 3, khách (Chiến làm thay ở Phase 1):
- [x] Khách đến theo lịch: khách đầu ở `first_customer_tick`, sau đó cứ `customer_interval_s` có một khách. Cấp id bằng `self.ids.new(...)`, xếp vào bàn trống.
- [x] Khách chọn món nấu được từ `stock` theo `menu[*].recipe` và giữ chỗ nguyên liệu (`reserved`). Không có món nào nấu được thì phát `no_dish`.
- [x] Kiên nhẫn giảm theo `patience_s`. Hết kiên nhẫn thì phát `customer_left`, uy tín cộng `left_reputation_delta`, kẹp trong [`reputation_min`, `reputation_max`], trả lại nguyên liệu đã giữ.
- [x] Dựng khách sẵn từ `scenario.customers[]` và suy ra `reserved`.
- [x] Bổ sung kiểm mâu thuẫn trong `chonoi/scenario.py`, ví dụ khách giữ chỗ nhiều hơn kho. Lỗi thì thoát mã 2.

Lát 4, bếp và phục vụ (Chiến làm thay ở Phase 1):
- [x] Mỗi tick tối đa một `interact`, chọn đối tượng theo thứ tự (khoảng cách, bếp trước bàn, id nhỏ), trong `interact_radius`.
- [x] Bếp: `cook_started`, nấu `cook_s` giây, xong thì `dish_ready`. Người chơi lấy món (`dish_picked`), cầm tối đa `carry_limit` món.
- [x] Bàn: `served`, khách ăn `eat_s` giây rồi `paid` với `price`. Có boa `tip_rate` và uy tín cộng `tip_reputation` khi kiên nhẫn còn từ `tip_min_patience_ratio` trở lên.
- [x] Cập nhật `money`, `earned`, `shift_earned`, `reputation`. Hết ca thì phát `quan_end` (đã có sẵn).
- [x] Điền `data` của các sự kiện quán vào bảng trong `docs/contracts/README.md`, nhắn Chiến xem lại.
- [x] Viết `tests/test_quan_rules.py` theo kiểu hộp đen như `tests/test_gather_rules.py`, mỗi luật ít nhất một test.

QA:
- [ ] Đọc lại `chonoi/sim/gather.py` và `tests/test_gather_rules.py` của Chiến, góp ý trong kênh nhóm hoặc qua comment commit.
- [ ] Trước khi gắn tag, chạy toàn bộ test và skill `.agents/skills/check-contract`, lưu output vào `docs/proof/phase-1/`.
- [ ] Điền các dòng `Q-xx` (luật quán) trong `docs/verification/phase-1.md`.
- [ ] Ghi một dòng của mình vào `docs/standup.md` và `docs/ai-usage-log.md`.

### Suốt lab
- [ ] Viết skill thứ hai `.agents/skills/run-proof/SKILL.md`: chạy test và headless, lưu kết quả vào `docs/proof/phase-n/`. Thêm tên skill vào mục Skills trong `AGENTS.md` (nhắn Chiến).
- [ ] Ít nhất 3 commit có nội dung bằng tài khoản `TrnhThnh`.
- [ ] Phase 2: viết retro nhanh trong `docs/retro.md` cùng Chiến.
- [ ] Phase 2–4: phần đề mới thuộc buổi tối hoặc thuộc QA thì Thịnh nhận. Cuối mỗi phase viết `docs/verification/phase-n.md`.
- [ ] Phase 4: tạo GitHub Release `v1.0.0` từ tag `phase-4`, viết `docs/members/TrnhThnh.md` theo `docs/members/TEMPLATE.md`.

## Việc của Chiến

### Phase 1
- [x] `TEAM.md`, `team_size`, hợp đồng `docs/contracts/README.md`, plan, clarify (nhóm 2 người).
- [x] Lát 1–2 gather trong `chonoi/sim/gather.py`, 19 test trong `tests/test_gather_rules.py`.
- [x] Proof demo gather, skill `check-contract`, verification phần gather.
- [ ] Hỏi giảng viên chuyện nhóm 2 người, ghi câu trả lời vào clarify #1.
- [x] Khi lab board mở PRD-0: đối chiếu clarify #2 đến #7 và sửa 3 giả định sai (#3, #4, #6). PRD-0 không đánh mã AC nên giữ mã `G-xx`.
- [ ] `client/ui`: cửa sổ `chonoi.live` hiện sự kiện (giỏ đầy, ngạt, ngất...).
- [ ] Đọc lại phần quán của Thịnh, ghép code, chạy test rồi gắn tag `phase-1`.

### Suốt lab
- [ ] Gắn tag `phase-2`, `phase-3`, `phase-4` đúng hạn. Giữ `docs/contracts/` và `AGENTS.md` cập nhật.
- [ ] Phase 2–4: phần đề mới thuộc buổi sáng, mode mới hoặc giao diện thì Chiến nhận.
- [ ] Viết mục "Sáng tạo của nhóm" trong README nếu làm thêm.
- [ ] Phase 4: viết `docs/members/duongchien147.md`, retro cuối cùng Thịnh, chuẩn bị demo.

## Phase 2 (Ticket-02, Test Contract v1.1, hạn tag `phase-2` lúc 1:55)

Ticket-02 gợi ý 4 lát: (1) số chuẩn và cá bơi/sinh, (2) Cá Sấu, Máu và ngất, (3) 2 bếp/4 bàn, 6 món và kế hoạch ngày, (4) day, Shop, pause, menu và HUD. Nhóm 2 người chia như sau: Chiến giữ buổi sáng và vòng ngày, Thịnh giữ buổi tối và Shop. Phần nào trong bảng dưới có thứ tự thì làm từ trên xuống, vì test ẩn chấm headless trước, giao diện sau.

Điều kiện trước: luật quán Phase 1 đã xong (Chiến làm thay). Thịnh bắt đầu Phase 2 bằng việc đọc `chonoi/sim/quan.py` và `tests/test_quan_rules.py`.

### Việc của Chiến
- [x] P2-A, đầu phase: chuyển `game.contract.json` sang `contract_version: "1.1"` với số chuẩn ở Ticket-02 mục 1 và mục 4.1: thêm khóa cá (`fish_speed`, `fish_turn_ticks`, `fish_max`, `fish_spawn_*`, `fish_x`, `fish_depths`, `fish_weights`), 8 đàn `fish_initial`, nút N5/N6 kèo nèo, `ca_keo`, `gather.monsters`, `quan` thêm B2 và T2–T4, `menu` 6 món, `day_plan` D1–D5, `shop`. Sửa phần kiểm tra trong `chonoi/contract.py`, `chonoi/inventory.py` (6 nguyên liệu) và `chonoi/scenario.py` cho v1.1. Đây là file khung, sửa xong báo Thịnh vì ảnh hưởng cả quán.
- [x] Lát 1: cá bơi 1.5 m/s, đổi hướng theo seed mỗi 120 bước, phản xạ ở mép, sinh cá mỗi 360 tick (trần 12 đàn, trọng số loài), sự kiện `fish_spawned`, trường `age_ticks`.
- [x] Lát 2: Cá Sấu M1 (M2 từ Ngày 3) với patrol, chase, recoil. Cú chạm làm mất 1 Máu, rơi `floor(n/2)` món theo LIFO, bất tử 90 tick; sự kiện `monster_hit`, `faint` với `cause: "monster"`.
- [x] Lát 4a: `--mode day` và `--days`, vòng pha `day_start → day_plan → phase_start(gather) → quan → shop`, bàn giao kho trong bộ nhớ, giữ tiền, uy tín và cấp qua các Ngày, `active_upgrades` áp từ Ngày kế. `pause`/`resumed` ở cả ba mode.
- [x] Lát 4b, nếu còn giờ: HUD, menu và màn hình DayIntro, EveningIntro, DayResult trên `chonoi.live`.
- [ ] Smoke `day --days 1`, chạy nhiều Ngày để kiểm nâng cấp, gắn tag `phase-2`.

### Việc của Thịnh
- [x] ~~Xong luật quán Phase 1 (lát 3–4)~~: Chiến đã làm thay (`chonoi/sim/quan.py`, `tests/test_quan_rules.py`). Thịnh đọc lại và góp ý.
- [ ] Lát 3: quán với 2 bếp, 4 bàn, 6 món (đã khai trong contract ở P2-A, code đọc theo dữ liệu nên không cần ghi số). Khách đến lúc tick 120 rồi cứ mỗi 900 tick, ngồi bàn trống id nhỏ nhất. Trong `day`, lọc menu theo món của kế hoạch Ngày trước khi xét nguyên liệu.
- [ ] Lát 4 phần Shop (Chiến đã viết bản tối thiểu `ShopPhase` trong `chonoi/sim/day.py` để vòng ngày chạy; Thịnh rà lại theo đề và bổ sung): `buy` (oxygen, hp), `bought`, `buy_failed` (funds, max_level, unknown), `shop_done`, tự đóng sau `shop.max_ticks`, `shop_end`. Tiền trừ vào `money`, giữ `earned`. Viết hàm Shop riêng để Chiến gọi từ vòng ngày.
- [ ] Phút 20: smoke tích hợp `gather --inventory-out` rồi `quan --inventory`, lưu `docs/proof/phase-2/integration.*`.
- [ ] Chạy lại toàn bộ test Phase 1 với số chuẩn (regression). Test nào phải đổi thì ghi lý do trong commit.
- [ ] `docs/verification/phase-2.md`, retro nhanh trong `docs/retro.md` (phút 45–50), ghi standup và ai-usage-log.

### Ghép giữa hai người
- Hai người chốt ngay đầu phase giao diện Chiến gọi sang quán và Shop trong vòng ngày: dựng `QuanSim` với kho trong bộ nhớ, tiền và uy tín đầu ca; dựng Shop với `money` và cấp hiện tại. Ghi vào `docs/contracts/README.md`.
- Mở rộng (Lao, vợt, rắn...) không bắt buộc với nhóm dưới 5 người, nên bỏ qua.

## Phase 4 (Ticket-04, Test Contract v1.3, tag `phase-4` và Release `v1.0.0`)

Bốn vai của Ticket-04 chia cho hai người. Chiến: Đóng gói + Release/Integrator. Thịnh: Bench/QA + Điều phối retro. Phần code chia theo file để không đè nhau.

### Việc của Chiến
- [x] `game.contract.json` → `contract_version: "1.3"`, khai `bench_cmd`, `soak_cmd`; `run_cmd` mở vòng ngày. Sửa `read_inventory` để v1.3 vẫn đọc kho cá thể.
- [x] `bench_cmd` (`chonoi/bench.py`): cảnh buổi sáng seed 42, Út Sen đứng ở bến, cá bơi, Cá Sấu, độ tươi; render 1280×720; làm nóng 3 s, đo `--duration` s; ghi `bench.json` 5 trường. Lưu artifact vào `docs/proof/phase-4/`.
- [x] Cảnh báo dễ nhận biết: thủy quái gần, oxy sắp hết, khách sắp giận (chữ và biểu tượng); chế độ tương phản cao; chơi thử cả ba cảnh báo ở chế độ đó, chụp ảnh.
- [x] README: cách chạy từ clone sạch ≤ 3 lệnh, yêu cầu môi trường, điều khiển, cách tính điểm, lệnh test, headless, bench, soak; mục "Sáng tạo của nhóm" nếu có. Thử clone sạch.
- [ ] CREDITS.md, LICENSE; release notes; gắn tag `phase-4` và tạo GitHub Release `v1.0.0` kèm bản đóng gói, cùng trỏ một commit.
- [x] `docs/members/duongchien147.md`.

### Việc của Thịnh
- [ ] `soak_cmd` (`chonoi/soak.py`): chạy 10 Ngày trong một tiến trình bằng bot tất định, kế hoạch D1–D5 lặp ở Ngày 6–10, ghi `soak.json` (`days`, `days_completed`, `crashes`, `results[]`, `duration_s`). Chạy hai lần cùng seed để so phần gameplay.
- [ ] Chạy regression P1–P3 trên commit bàn giao, lưu log; viết `docs/verification/phase-4.md` (AC-P4-xx → bằng chứng → kết quả).
- [ ] Rà CHANGELOG theo từng phase.
- [ ] Điều phối retro: mở đầu bằng hành động đã chốt ở retro P2, ghi điều tốt, điều cần sửa, hành động tiếp theo, một lỗi AI và cách xác minh (`docs/retro.md`).
- [ ] `docs/members/TrnhThnh.md`.

### Ghép
- Thịnh làm trên nhánh thì báo Chiến khi xong để gộp trước khi gắn tag. Tag `phase-4` và Release `v1.0.0` gắn sau khi cả hai phần đã vào `main` và CI xanh.

## Giờ chốt

| Mốc | Việc chung |
|---|---|
| Trước 0:50 | Thịnh xong lát 3–4, cả hai đọc code của nhau |
| 0:50–1:00 | Chạy toàn bộ test, Thịnh lưu proof, Chiến gắn tag `phase-1` |
| 1:00 / 1:55 / 2:30 | Mở đề phase mới: 5 phút cùng đọc, chia theo quy tắc ở trên |
| Trước 3:00 | Tag `phase-4`, Release `v1.0.0`, retro, file members |
