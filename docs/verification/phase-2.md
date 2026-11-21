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
