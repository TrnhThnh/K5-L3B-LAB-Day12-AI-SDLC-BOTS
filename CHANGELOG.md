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
