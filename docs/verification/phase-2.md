# Phase 2 — bàn giao phần quán và QA

Phạm vi của Thịnh theo TICKET-02. Các mã bên dưới là mã truy vết nội bộ. Chạy từ gốc repo bằng `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`. [Log regression](../proof/phase-2/quan-tests.txt).

| Mục đề | Kết quả kiểm |
|---|---|
| §1.3 Bếp, bàn, bếp nhận đơn cũ nhất | Đạt. `test_layout_and_all_six_recipes` kiểm tọa độ và nấu từng món tại B2. `test_oldest_order_then_lowest_table` kiểm cả hai khóa ưu tiên. |
| §1.3 Boa, tiền ca, kết ca | Đạt. `test_tip_boundary` kiểm ngưỡng; `test_close_pays_eaters_and_releases_waiting_orders` kiểm khách ăn và chờ; `test_close_discards_assigned_dish` kiểm dọn bếp và tay. |
| §2 Lọc menu, giữ nguyên liệu, số suất | Đạt ở QuanSim. Caller truyền `day_plan=plan` khi dựng quán, với `plan` là mục của Ngày hiện tại. Bỏ tham số khi chạy quán độc lập. `test_daily_plan_filters_orders_but_does_not_cap_servings` kiểm cả đơn sai kế hoạch. |
| §4.1 Kho qua CLI | Đạt. Gather xuất file, quan đọc lại, tick 0 có đúng hai cá kèo và một kèo nèo. [Bằng chứng](../proof/phase-2/integration.json). |
| §4.2–4.5 Toàn Ngày, Shop, pause, nhiều Ngày và thời gian chạy | Chưa đạt ở bản bàn giao phần B. CLI còn từ chối mode day. Cần chạy lại trên commit tích hợp của nhóm. |
| §1.1–1.2, §2 Buổi sáng và UI | Thuộc phần của Chiến. Chưa xác nhận trên nhánh này. |

Không đổi tiêu chí của test Phase 1 để lấy kết quả đạt. Các test P1 về bắt cá từng phần, hồi chiêu khi bắt hụt và từ chối mode day phải được cập nhật khi nhóm ghép phần gather/day theo TICKET-02. Số test hiện tại chưa chứng minh toàn bộ v1.1. Cấu hình quán và kế hoạch D1–D5 được chuẩn bị trên nhánh bàn giao để Chiến review trước khi ghép manifest chung.

## Kết quả trên commit tích hợp `b1b4c9c` (tag `phase-2`)

Bảng trên là phần Thịnh kiểm trên nhánh `thinh/phase-2-quan-qa` trước khi tích hợp. Các mục "chưa đạt ở bản bàn giao phần B" được kiểm lại trên `main` tại `b1b4c9c`, commit gắn tag `phase-2`. Lệnh chung: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`, kết quả `Ran 100 tests ... OK` (CI GitHub Actions trên Linux cũng xanh).

| Mục đề | Bằng chứng | Kết quả |
|---|---|---|
| §1.1 Số chuẩn, cá bơi/sinh | `tests/test_gather_p2.py` (FishSwim, FishSpawn) | Đạt |
| §1.2 Cá Sấu, Máu, ngất | `tests/test_gather_p2.py` (Crocodile) | Đạt |
| §1.3 Quán 2 bếp, 4 bàn, 6 món | `tests/test_quan_rules.py`, `test_second_customer_takes_next_table` | Đạt |
| §2 Vòng ngày, kế hoạch D1–D5, lọc menu | `tests/test_day.py` (DayLoop), [day-1.jsonl](../proof/phase-2/day-1.jsonl) | Đạt. Một Ngày đủ 22.200 tick chạy 1,6 s. |
| §2 Shop, nâng cấp áp từ Ngày kế | `tests/test_day.py` (Shop), [day-shop.jsonl](../proof/phase-2/day-shop.jsonl) | Đạt. Mua oxy cấp 1, Ngày 2 có 2.700 tick oxy. |
| §4.2 Pause | `tests/test_day.py` (Pause) | Đạt |
| §2 Menu, intro, HUD, 30 FPS | `tests/test_live_ui.py`, [ảnh chụp 1280×720](../proof/phase-2/ui/) | Đạt. Đo 60 FPS trên trình duyệt. |
| §4.1 Kho qua CLI | [integration.json](../proof/phase-2/integration.json) | Đạt (Thịnh kiểm trên nhánh quán) |

Khi gộp nhánh của Thịnh vào `main` (sau khi lên v1.2), `tests/test_quan_phase2.py` được chuyển sang kho cá thể và chạy hộp đen qua headless. Bản gốc import helper từ bản `test_quan_rules.py` riêng trên nhánh của Thịnh, vốn dùng kho đếm v1.1. Hai ca `test_layout_and_all_six_recipes` (đủ 6 món nấu được ở B2) và `test_oldest_order_then_lowest_table` giữ nguyên ý kiểm và đều đạt. Ca lọc menu theo kế hoạch đã có ở `tests/test_day.py::DayLoop.test_plan_filters_menu`.
