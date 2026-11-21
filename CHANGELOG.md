# Changelog
## Unreleased

### Gather (duongchien147)
- Lát 1: oxy, ngạt, Máu, ngất, dive/surface, giỏ LIFO.
- Lát 2: hái nút, bắt cá, hold_full, nút mọc lại.
- Test hộp đen `tests/test_gather_rules.py` (19 test).
- Gather khớp PRD-0: dữ liệu sự kiện theo mục E, thiếu chỗ thì giữ đàn/nút, hồi chiêu chỉ khi bắt thành công.

### Quán (duongchien147, làm thay TrnhThnh)
- Lát 3: khách theo lịch, chọn món theo seed, giữ chỗ, kiên nhẫn, `no_dish`, `customer_left`.
- Lát 4: bếp, bưng, phục vụ, boa, trả tiền, uy tín, đóng ca, kiểm mâu thuẫn fixture.
- Test hộp đen `tests/test_quan_rules.py` (13 test).

### Phase 2 — Test Contract v1.1 (duongchien147)
- `game.contract.json` v1.1: số chuẩn Ticket-02, `ca_keo`/`keo_neo`, 6 món, B2, T2–T4, `monsters`, `day_plan` D1–D5, `shop`.
- Khung: kiểm contract v1.1, kho 6 nguyên liệu, scenario nhận `monsters[]`, `fish[].age_ticks`.
- Gather lát 1: 8 đàn đầu ca theo seed, cá bơi/đổi hướng/phản xạ, sinh cá mỗi 360 tick (`fish_spawned`).
- Gather lát 2: Cá Sấu patrol/chase/recoil, `monster_hit`, bất tử 90 tick, ngất do quái.
- Test: `tests/test_gather_p2.py` (17 test); sửa 3 test cũ theo luật mới (lý do trong commit).
- Lát 4a: `--mode day` và `--days`, vòng pha gather → quan → shop, bàn giao kho trong bộ nhớ, giữ tiền/uy tín/cấp qua Ngày, nâng cấp áp từ Ngày kế; pause/resumed cho cả ba mode; Shop tối thiểu.
- Test: `tests/test_day.py` (13 test); test smoke cũ bỏ kiểm `--mode day` bị từ chối (v1.1 đã hỗ trợ).
- Lát 4b: cửa sổ chơi có `--mode day`, menu chính (Chơi/Thoát), DayIntro tự chuyển sau 4 s, EveningIntro, DayResult, Summary, pause (Tiếp tục/Về menu), Shop (1/2 mua, Enter đóng), HUD sáng/tối theo Ticket-02, chữ không chân ≥ 18 px; 60 FPS ở 1280×720.

## Phase 3 — thay đổi schema kho

V1.2 dùng mảng cá thể trong file kho, gather.hold và quan.stock. Thay mỗi đơn vị trong kho đếm bằng một object có id riêng, kind và fresh; xem docs/contracts/inventory.sample.json. Đổi phần giữ chỗ sang mảng id. Fixture cũ không còn hợp lệ.

## Phase 4 — Test Contract v1.3, phát hành v1.0.0 (duongchien147)
- `game.contract.json` → `contract_version: "1.3"`, khai `bench_cmd` (`python3 -m chonoi.bench`) và `soak_cmd` (`python3 -m chonoi.soak`). Gameplay, tuning, kho và JSONL giữ như v1.2.
- `read_inventory` so phiên bản theo số: từ v1.2 trở đi đều đọc kho cá thể (trước đó chỉ nhận đúng chuỗi `"1.2"`, nên v1.3 sẽ quay về kho đếm).
- Vòng ngày: quá 5 Ngày thì kế hoạch D1–D5 lặp lại (cho soak 10 Ngày).
- `chonoi/bench.py`: benchmark có render phần mềm 1280×720, làm nóng 3 s, ghi `bench.json` 5 trường; `tests/test_bench.py`.
- Cửa sổ chơi: ba cảnh báo có chữ và biểu tượng (thủy quái gần, oxy sắp hết/hết, khách sắp giận), chế độ tương phản cao (phím H, nhớ giữa các lần mở).
- README của nhóm: chạy từ clone sạch 3 lệnh, điều khiển, cách tính điểm, lệnh test/headless/bench/soak, giới hạn đã biết. Đề lab gốc chuyển sang `docs/LAB.md`.
- `chonoi/soak.py`: chạy N Ngày bằng một session headless, xác minh kế hoạch lặp D1–D5 và kết quả từng Ngày; replay cùng seed để kiểm định tính lặp.
- Bằng chứng soak 10 Ngày seed 7 và regression Phase 4: `docs/proof/phase-4/soak.json`, `docs/proof/phase-4/unittest.txt`.
