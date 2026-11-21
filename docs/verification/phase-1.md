# Ma trận truy vết Phase 1

Mã AC chính thức của PRD-0 chưa có trong repo (lab board chưa mở đề lúc viết), nên bảng dưới tạm dùng mã nội bộ `G-xx` cho phần gather. Khi có PRD-0, Chiến sẽ đổi sang mã AC thật. Phần quán (`Q-xx`) do Thịnh điền.

Lệnh chạy chung: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`. Kết quả lần chạy ngày 2026-11-21: `Ran 51 tests ... OK`, log ở [unittest.txt](../proof/phase-1/unittest.txt).

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| G-01 Dưới nước mất 1 oxy mỗi tick, mặt nước hồi `oxygen_refill_per_tick`, kẹp trong [0, max] | `test_gather_rules.Oxygen.test_underwater_loses_one_per_tick`, `test_surface_refills_and_clamps` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| G-02 `oxygen_empty` phát đúng một lần khi oxy từ dương về 0 | `Oxygen.test_oxygen_empty_once` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| G-03 Ngạt: đủ `choke_interval_ticks` thì `choke`, Máu giảm 1; lên mặt nước thì bộ đếm về 0 | `Oxygen.test_choke_every_interval`, `test_zero_oxy_counter_from_scenario`, `test_surfacing_resets_choke_counter` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo giả định clarify #2) |
| G-04 Máu về 0: `faint`, `gather_end` reason `fainted`, mất giỏ, file kho rỗng | `Oxygen.test_faint_loses_hold_and_writes_empty_inventory` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| G-05 `dive` / `surface` khi đổi vùng nước | `Zones.test_dive_then_surface_events` | [gather-demo.jsonl](../proof/phase-1/gather-demo.jsonl) (tick 206 và 352) | Đạt |
| G-06 Hái nút `ready` gần nhất ở mặt nước, bằng khoảng cách thì lấy id nhỏ, nút mọc lại sau `regrow_s` | `Harvest.test_harvest_ready_node_then_regrow`, `test_nearest_then_smaller_id`, `test_no_harvest_underwater_or_out_of_range` | [gather-demo.jsonl](../proof/phase-1/gather-demo.jsonl) (tick 416) | Đạt |
| G-07 Cập bến được xét trước khi hái | `Harvest.test_dock_wins_over_harvest`, smoke `test_inv_01_gather_writes_inventory_quan_reads_it` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| G-08 Bắt cá chỉ khi ở dưới nước và hết hồi chiêu, được `fish_yield` con | `Catch.test_catch_school`, `test_no_catch_at_surface`, `test_cooldown_blocks_second_catch` | [gather-demo.jsonl](../proof/phase-1/gather-demo.jsonl) (tick 281) | Đạt |
| G-09 Giỏ LIFO, sức chứa `hold_capacity`, đầy thì `hold_full` | `Harvest.test_hold_full_blocks_harvest`, `Catch.test_partial_fill_then_hold_full`, `test_full_hold_keeps_fish` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo giả định clarify #3) |
| G-10 Kho gather chuyển sang quán | Chạy demo gather rồi `--mode quan --inventory gather-demo.kho.json` | [gather-demo.kho.json](../proof/phase-1/gather-demo.kho.json), [quan-doc-kho.jsonl](../proof/phase-1/quan-doc-kho.jsonl) (`stock` = `{"bong_dien_dien":1,"ca_linh":3}`) | Đạt |
| G-11 Cùng seed ra cùng byte | `Determinism.test_full_run_same_bytes` (2400 tick), chạy lại demo rồi `cmp` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| Q-xx Luật quán (lát 3–4) | Thịnh điền | | Chưa làm |

Lượt demo gather ([inputs](../proof/phase-1/gather-demo.inputs.json), seed 1): lặn xuống ở tick 206, bắt đàn F1 được 3 cá linh ở tick 281, ngoi lên ở tick 352, hái N1 ở tick 416, về bến ở tick 571. Kho ghi ra `{"items":{"bong_dien_dien":1,"ca_linh":3}}`.

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: lát 1 và lát 2 của gather đạt theo test của nhóm và smoke test. Lát 3–4 của quán chưa xong. Một số luật đang dựa trên giả định (clarify #2 đến #7) vì chưa đối chiếu được với PRD-0.
- Điều cần chỉnh cho phase sau: đối chiếu giả định với PRD-0 rồi đổi mã AC. Thêm hiển thị sự kiện trên cửa sổ `chonoi.live` (phần `client/ui`). Hỏi giảng viên chuyện nhóm 2 người.
