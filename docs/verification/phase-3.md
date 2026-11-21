# Phase 3 — kiểm chứng kho và độ tươi

Quyết định tích hợp: phát triển trên nhánh từ main đã có vòng Ngày. Chuyển đồng thời writer, reader, quán và Shop trước khi bàn giao manifest v1.2. Ghép HUD từ main rồi chạy lại regression. Các mã dưới đây là mã truy vết nội bộ.

| AC | Bằng chứng | Kết quả |
|---|---|---|
| AC-P3-01 Kho cá thể qua file | [gather](../proof/phase-3/gather.jsonl), [kho](../proof/phase-3/inventory.json), [quán tick 0](../proof/phase-3/quan.jsonl) | I7 giữ nguyên kind và fresh sau bước cập bến. |
| AC-P3-02 Bàn giao trong ngày và xuyên ngày | [Hai Ngày](../proof/phase-3/two-days.jsonl) | Ngày 1 nhận I7, Ngày 2 nhận I8. Shop không hao tươi. Cả hai ngày đều hoàn tất. |
| AC-P3-03 Ngưỡng 30 và thứ tự spoiled | test_threshold_is_strict_one_event_per_item | Ở đúng 30 vẫn dùng được; khi thấp hơn mới phát spoiled. I2 đứng trước I10. |
| AC-P3-04 Giữ nguyên liệu và giữ lại | test_spoiled_reservations_reallocated_before_cooking, test_automatic_reservations_and_conflicts | Giữ tươi nhất, hòa theo id. Hàng ươn nhả trước tương tác; đơn không đủ chuyển unfulfillable. |
| AC-P3-05 Khóa giá khi nấu | test_price_locks_at_cook_start_and_uses_each_ingredient | Gỏi có hai bông ở 70 và 80 điểm lúc nấu; giá 30, không đổi lúc chín. |
| AC-P3-06 Kho không hợp lệ | test_invalid_inventory_files_exit_two | Kho đếm, id sai/trùng, kind lạ và fresh sai miền đều trả mã 2. |
| AC-P3-07 HUD | chonoi/web/index.html, tests/test_live_ui.py, [ảnh HUD sáng](../proof/phase-3/ui/hud-gather-fresh.png), [ảnh HUD quán](../proof/phase-3/ui/hud-quan-fresh.png), [scenario](../proof/phase-3/ui/hud-fresh.scenario.json) | Đạt. Chiến kiểm bằng trình duyệt: giỏ và kho quán hiện "tươi thấp nhất" và số món ươn. Khi kiểm, Chiến thấy dòng "Cần lấy" vẫn đếm hàng ươn (cá lóc 1/3 dù con cá đã ươn), đã sửa để chỉ đếm hàng còn dùng được (0/3). |

Regression P1–P2 giữ các ca chuyển pha, pause, thời gian, thanh toán, LIFO và ghi file nguyên tử. Fixture và assertion dạng kho đếm được chuyển sang cá thể; kỳ vọng giá món mới nấu phản ánh một bước hao tươi trước tương tác. [Log toàn bộ suite](../proof/phase-3/unittest.txt).

Chạy lại bằng `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`. Các mở rộng đặt bàn và dòng lũ nằm ngoài phạm vi lõi của nhóm hai người.

Bảng tác động, quyết định đổi schema và thứ tự tích hợp: [ADR-0001](../adr/0001-kho-ca-the-v1.2.md).

## Kiểm lại cả ba tag và main

Ngày 21/11/2026, QA xuất từng tag vào thư mục riêng bằng git archive rồi chạy unittest discover với đúng code và fixture của tag.

| Tag | Commit | Contract | Test đạt |
|---|---|---|---:|
| phase-1 | e778858 | 1.0 | 65/65 |
| phase-2 | b1b4c9c | 1.1 | 100/100 |
| phase-3 | 64233ea | 1.2 | 107/107 |

Trên main sau tag Phase 3, lệnh chơi ở manifest mở vòng 5 Ngày. README có lệnh chạy bản chơi, headless và smoke kho. Đã chạy lại smoke qua hai tiến trình theo README và so toàn bộ mảng cá thể giữa gather_end, file kho và snapshot quán tick 0.

Với seed 7, không input, snapshot mỗi 1.000 tick, một Ngày hoàn tất ở tick 22.200 trong 0,41 giây trên máy kiểm. Năm Ngày hoàn tất ở tick 111.000 trong 1,71 giây, đủ năm sự kiện day_plan và kết thúc với days_completed=5. Sau khi bổ sung kiểm fixture quán và day, [107 test trên main đều đạt](../proof/phase-3/main-regression.txt).

Kiểm hành chính bằng tools/check_team.py vẫn báo nhóm có hai người, dưới mức 4–6. Việc chấp nhận ngoại lệ đang chờ giảng viên theo clarify #1. Kết quả trên không xác nhận thời điểm GitHub nhận từng tag.
