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
- [x] `git pull`, rồi chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` và thấy `OK` (51 test). Máy Windows không có `python3` thì xem mục Lệnh trong `AGENTS.md`.
- [x] Đọc `docs/contracts/README.md` (schema kho, sự kiện), `docs/clarify.md` và docstring đầu `chonoi/sim/quan.py`.

### Phase 1: luật quán (`chonoi/sim/quan.py`)
Số liệu lấy từ `tuning.quan` và `tuning.menu` trong `game.contract.json`, không ghi số thẳng vào code. Chỗ nào đề chưa rõ thì ghi vào `docs/clarify.md` rồi báo Chiến.

Lát 3, khách:
- [x] Khách đến theo lịch: khách đầu ở `first_customer_tick`, sau đó cứ `customer_interval_s` có một khách. Cấp id bằng `self.ids.new(...)`, xếp vào bàn trống.
- [x] Khách chọn món nấu được từ `stock` theo `menu[*].recipe` và giữ chỗ nguyên liệu (`reserved`). Không có món nào nấu được thì phát `no_dish`.
- [x] Kiên nhẫn giảm theo `patience_s`. Hết kiên nhẫn thì phát `customer_left`, uy tín cộng `left_reputation_delta`, kẹp trong [`reputation_min`, `reputation_max`], trả lại nguyên liệu đã giữ.
- [x] Dựng khách sẵn từ `scenario.customers[]` và suy ra `reserved` (TODO ở dòng 40).
- [x] Bổ sung kiểm mâu thuẫn trong `chonoi/scenario.py`, ví dụ khách giữ chỗ nhiều hơn kho. Lỗi thì thoát mã 2.

Lát 4, bếp và phục vụ:
- [x] Mỗi tick tối đa một `interact`, chọn đối tượng theo thứ tự (khoảng cách, bếp trước bàn, id nhỏ), trong `interact_radius`.
- [x] Bếp: `cook_started`, nấu `cook_s` giây, xong thì `dish_ready`. Người chơi lấy món (`dish_picked`), cầm tối đa `carry_limit` món.
- [x] Bàn: `served`, khách ăn `eat_s` giây rồi `paid` với `price`. Có boa `tip_rate` và uy tín cộng `tip_reputation` khi kiên nhẫn còn từ `tip_min_patience_ratio` trở lên.
- [x] Cập nhật `money`, `earned`, `shift_earned`, `reputation`. Hết ca thì phát `quan_end` (đã có sẵn).
- [ ] Điền `data` của các sự kiện quán vào bảng trong `docs/contracts/README.md`, nhắn Chiến xem lại.
- [x] Viết `tests/test_quan_rules.py` theo kiểu hộp đen như `tests/test_gather_rules.py`, mỗi luật ít nhất một test.

QA:
- [ ] Đọc lại `chonoi/sim/gather.py` và `tests/test_gather_rules.py` của Chiến, góp ý trong kênh nhóm hoặc qua comment commit.
- [x] Trước khi gắn tag, chạy toàn bộ test và skill `.agents/skills/check-contract`, lưu output vào `docs/proof/phase-1/`.
- [x] Điền các dòng `Q-xx` (luật quán) trong `docs/verification/phase-1.md`.
- [x] Ghi một dòng của mình vào `docs/standup.md` và `docs/ai-usage-log.md`.

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
- [ ] Khi lab board mở PRD-0: đối chiếu clarify #2 đến #7, đổi mã `G-xx` sang mã AC thật.
- [ ] `client/ui`: cửa sổ `chonoi.live` hiện sự kiện (giỏ đầy, ngạt, ngất...).
- [ ] Đọc lại phần quán của Thịnh, ghép code, chạy test rồi gắn tag `phase-1`.

### Suốt lab
- [ ] Gắn tag `phase-2`, `phase-3`, `phase-4` đúng hạn. Giữ `docs/contracts/` và `AGENTS.md` cập nhật.
- [ ] Phase 2–4: phần đề mới thuộc buổi sáng, mode mới hoặc giao diện thì Chiến nhận.
- [ ] Viết mục "Sáng tạo của nhóm" trong README nếu làm thêm.
- [ ] Phase 4: viết `docs/members/duongchien147.md`, retro cuối cùng Thịnh, chuẩn bị demo.

## Giờ chốt

| Mốc | Việc chung |
|---|---|
| Trước 0:50 | Thịnh xong lát 3–4, cả hai đọc code của nhau |
| 0:50–1:00 | Chạy toàn bộ test, Thịnh lưu proof, Chiến gắn tag `phase-1` |
| 1:00 / 1:55 / 2:30 | Mở đề phase mới: 5 phút cùng đọc, chia theo quy tắc ở trên |
| Trước 3:00 | Tag `phase-4`, Release `v1.0.0`, retro, file members |
