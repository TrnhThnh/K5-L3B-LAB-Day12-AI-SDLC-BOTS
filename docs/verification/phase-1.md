# Ma trận truy vết Phase 1

PRD-0 không đánh mã AC cho từng luật, nên nhóm dùng mã nội bộ `G-xx` cho gather và `Q-xx` cho quán, mỗi mã trỏ tới một ý trong PRD-0 mục F hoặc G. Phần gather đã đối chiếu với PRD-0 thật; các giả định sai lúc đầu đã sửa (xem `docs/clarify.md` #3, #4, #6). Phần quán do Chiến làm thay Thịnh ở Phase 1 (xem `docs/plan/phan-cong.md`).

Lệnh chạy chung: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`. Kết quả lần chạy ngày 2026-11-21: `Ran 65 tests ... OK`, log ở [unittest.txt](../proof/phase-1/unittest.txt).

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| G-01 Dưới nước mất 1 oxy mỗi tick, mặt nước hồi `oxygen_refill_per_tick`, kẹp trong [0, max] | `test_gather_rules.Oxygen.test_underwater_loses_one_per_tick`, `test_surface_refills_and_clamps` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| G-02 `oxygen_empty` phát đúng một lần khi oxy từ dương về 0 | `Oxygen.test_oxygen_empty_once` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| G-03 Ngạt: đủ `choke_interval_ticks` thì `choke`, Máu giảm 1; lên mặt nước thì bộ đếm về 0 | `Oxygen.test_choke_every_interval`, `test_zero_oxy_counter_from_scenario`, `test_surfacing_resets_choke_counter` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (khớp PRD-0 F: ngạt lần đầu ở t+59) |
| G-04 Máu về 0: `faint`, `gather_end` reason `fainted`, mất giỏ, file kho rỗng | `Oxygen.test_faint_loses_hold_and_writes_empty_inventory` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| G-05 `dive` / `surface` khi đổi vùng nước | `Zones.test_dive_then_surface_events` | [gather-demo.jsonl](../proof/phase-1/gather-demo.jsonl) (tick 206 và 352) | Đạt |
| G-06 Hái nút `ready` gần nhất ở mặt nước, bằng khoảng cách thì lấy id nhỏ, nút mọc lại sau `regrow_s` | `Harvest.test_harvest_ready_node_then_regrow`, `test_nearest_then_smaller_id`, `test_no_harvest_underwater_or_out_of_range` | [gather-demo.jsonl](../proof/phase-1/gather-demo.jsonl) (tick 416) | Đạt |
| G-07 Cập bến được xét trước khi hái | `Harvest.test_dock_wins_over_harvest`, smoke `test_inv_01_gather_writes_inventory_quan_reads_it` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| G-08 Bắt cá chỉ khi ở dưới nước và hết hồi chiêu, được `fish_yield` con | `Catch.test_catch_school`, `test_no_catch_at_surface`, `test_cooldown_blocks_second_catch` | [gather-demo.jsonl](../proof/phase-1/gather-demo.jsonl) (tick 281) | Đạt |
| G-09 Giỏ LIFO, sức chứa `hold_capacity`; thiếu chỗ thì `hold_full`, giữ nút/đàn, không đặt hồi chiêu | `Harvest.test_hold_full_blocks_harvest`, `Catch.test_not_enough_room_keeps_school_and_cooldown`, `test_full_hold_keeps_fish`, `test_miss_sets_no_cooldown` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| G-10 Kho gather chuyển sang quán (smoke hai tiến trình PRD-0 mục G) | Chạy đúng hai lệnh smoke của PRD-0 với `dock.json`, `dock-inputs.json`; thêm demo gather rồi `--mode quan --inventory gather-demo.kho.json` | [smoke-catch.json](../proof/phase-1/smoke-catch.json) = `{"items":{"bong_sung":2,"ca_loc":1}}`, [smoke-quan.jsonl](../proof/phase-1/smoke-quan.jsonl) có cùng `stock`; [gather-demo.kho.json](../proof/phase-1/gather-demo.kho.json), [quan-doc-kho.jsonl](../proof/phase-1/quan-doc-kho.jsonl) (`stock` = `{"bong_dien_dien":1,"ca_linh":3}`) | Đạt |
| G-11 Cùng seed ra cùng byte | `Determinism.test_full_run_same_bytes` (2400 tick), chạy lại demo rồi `cmp` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| Q-01 Khách đến ở `first_customer_tick` rồi mỗi `customer_interval_s`, ngồi bàn trống id nhỏ nhất, giữ chỗ đúng công thức; hết bàn thì bỏ lượt | `test_quan_rules.Customers.test_first_customer_reserves_recipe`, `test_no_free_table_skips_turn` | [quan-demo.jsonl](../proof/phase-1/quan-demo.jsonl) (tick 120) | Đạt |
| Q-02 Có bàn mà không món nào đủ nguyên liệu khả dụng thì `no_dish` | `Customers.test_no_dish_when_nothing_cookable` | [quan-demo.jsonl](../proof/phase-1/quan-demo.jsonl) (tick 1920 trở đi) | Đạt |
| Q-03 Hết kiên nhẫn khi ca còn giờ: `customer_left` reason `patience`, uy tín cộng `left_reputation_delta`, nhả phần giữ | `Customers.test_patience_runs_out` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| Q-04 Bếp idle lấy đơn reserved cũ nhất, tiêu nguyên liệu, chốt giá, nấu `cook_s`; xong thì `dish_ready`; bếp ready giao món cho tay trống | `Kitchen.test_cook_ready_pick`, `test_idle_stove_without_order_does_nothing` | [quan-demo.jsonl](../proof/phase-1/quan-demo.jsonl) (tick 122, 722, 731) | Đạt |
| Q-05 Phục vụ đúng đơn, boa `floor(giá × tip_rate)` khi kiên nhẫn còn ≥ `tip_min_patience_ratio`; ăn xong `paid`, cộng tiền, boa dương cộng `tip_reputation` | `Serving.test_serve_eat_pay_with_tip`, `test_no_tip_below_ratio` | [quan-demo.jsonl](../proof/phase-1/quan-demo.jsonl) (served tick 881, tip 24; paid tick 1481, 144) | Đạt |
| Q-06 Hết ca: khách đang ăn trả ngay (`closing`), khách chờ rời không trừ uy tín, rồi `quan_end` | `Closing.test_closing_pays_eaters_and_releases_waiters`, `test_waiting_customer_leaves_without_penalty_at_close` | [quan-demo.jsonl](../proof/phase-1/quan-demo.jsonl) (tick 10800) | Đạt |
| Q-07 Fixture mâu thuẫn (giữ quá tồn, assigned không có món, món ngoài phạm vi, khách eating thiếu timer, món trên tay không khớp đơn) thoát mã 2 | `Fixtures.test_conflicts_exit_2`, `Serving.test_hand_without_matching_order_exit_2` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (chưa phủ hết danh sách ở PRD-0 mục D) |
| Q-08 Cả ca 10.800 tick, cùng seed ra cùng byte | `FullShift.test_full_shift_deterministic` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |

Lượt demo gather ([inputs](../proof/phase-1/gather-demo.inputs.json), seed 1): lặn xuống ở tick 206, bắt đàn F1 được 3 cá linh ở tick 281, ngoi lên ở tick 352, hái N1 ở tick 416, về bến ở tick 571. Kho ghi ra `{"items":{"bong_dien_dien":1,"ca_linh":3}}`.

Lượt demo quán nối tiếp ([inputs](../proof/phase-1/quan-demo.inputs.json), seed 1, `--inventory gather-demo.kho.json`): khách C1 đến ở tick 120 gọi lẩu cá linh bông điên điển, nấu từ tick 122, chín ở tick 722, bưng ở tick 731, phục vụ ở tick 881 với boa 24, trả 144 ở tick 1481. Hết ca: `money` 144, uy tín 3.2, điểm 444.

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: lát 1 và lát 2 của gather đạt và đã khớp PRD-0. Smoke hai tiến trình đạt. Lát 3–4 của quán đạt theo test của nhóm, nhưng xong muộn, sau hạn 1:00. Kiểm mâu thuẫn fixture quán mới phủ một phần mục D. HUD mới có cửa sổ thử của khung, chưa đủ HUD tối thiểu ở PRD-0 mục 2. README chưa có mục cách chạy theo DoD.
- Điều cần chỉnh cho phase sau: đọc kỹ đề trước khi tự đặt giả định (3 trong 6 giả định lúc đầu sai). Hoàn thiện HUD và README cách chạy theo DoD. Hỏi giảng viên chuyện nhóm 2 người.
