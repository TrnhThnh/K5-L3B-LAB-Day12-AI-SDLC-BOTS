# ADR-0001: Chuyển kho đếm sang kho cá thể có độ tươi (Test Contract v1.2)

- Trạng thái: chấp nhận
- Ngày, người quyết: 2026-11-21. Thịnh chọn cách chuyển và làm phần lớn thay đổi trên nhánh `thinh/phase-3-quan-qa`. Chiến review khi tích hợp.
- Ghi chú: ADR này viết sau khi đã tích hợp, dựa trên các commit `7d7f196`, `442f279`, `9a0972d` và ghi chú trong `docs/verification/phase-3.md`. Lúc làm, nhóm chưa ghi bảng tác động trước khi bắt đầu như Ticket-03 gợi ý.

## Bối cảnh

Ticket-03 (Change Request "Mùa Nước Nổi") thay kho đếm theo loại `{"items": {"ca_loc": 2}}` bằng mảng cá thể `{"items": [{"id", "kind", "fresh"}]}`. Mỗi nguyên liệu có id riêng, cấp tăng dần xuyên pha và Ngày. Độ tươi hao 0,5/s trong giỏ, 0,25/s trong kho quán. Dưới 30 là ươn. Giữ chỗ chuyển từ giữ theo lượng sang giữ theo id. Giá món chốt theo độ tươi trung bình lúc bắt đầu nấu. Ở v1.2, file kho đếm phải trả mã 2.

Thay đổi này đụng vào hợp đồng giữa hai buổi (file kho, bàn giao trong `day`), nên ảnh hưởng mọi module.

## Các lựa chọn đã cân nhắc

1. Hỗ trợ song song hai schema trong lúc chuyển, chọn theo `contract_version`, rồi bật v1.2 khi cả hai đầu sẵn sàng (Ticket-03 gợi ý).
2. Chuyển một lần: đổi cả bên ghi (gather), bên đọc (quán), Shop và fixture test trong cùng một nhánh, rồi mới đưa lên `main`.

## Quyết định

Chọn cách 2. Nhóm chỉ có hai người và Thịnh giữ cả bên đọc lẫn phần lớn bên ghi, nên chuyển một lần trên nhánh riêng ít rủi ro hơn việc giữ hai schema. `main` vẫn chạy v1.1 cho tới khi nhánh v1.2 qua toàn bộ test. Nhánh được gộp `main` mới nhất (có HUD của Chiến) trước khi đưa lên.

Thứ tự tích hợp:
1. `chonoi/inventory.py`: kiểm schema cá thể (`validate_individuals`), hao tươi (`age_items`), ghi file theo id, giữ đủ độ chính xác ở ngưỡng 30.
2. Gather ghi kho cá thể. Quán đọc kho, giữ chỗ theo id, chốt giá theo độ tươi. Shop giữ nguyên độ tươi.
3. Chuyển fixture của mọi test sang cá thể (helper `individuals` trong `tests/helpers.py`).
4. HUD hiện độ tươi.
5. Chạy lại toàn bộ test, đưa lên `main` (`9a0972d`).

Công thức giá: Ticket-03 có ghi `floor(giá niêm yết × trung bình fresh / 100)`. Thịnh áp công thức này sau bước hao tươi của tick bắt đầu nấu (xem `docs/clarify.md`).

## Hệ quả — bảng tác động

| Module | File đã đổi | Test giữ / đổi / thêm | Người phụ trách |
|---|---|---|---|
| Adapter kho | `chonoi/inventory.py`, `chonoi/headless.py`, `chonoi/jsonl.py`, `chonoi/scenario.py` | Thêm `tests/test_freshness.py::test_invalid_inventory_files_exit_two` | Thịnh |
| Lặn | `chonoi/sim/gather.py` | Đổi fixture `hold` trong `tests/test_gather_rules.py`, `tests/test_gather_p2.py`; thêm `test_threshold_is_strict_one_event_per_item` | Thịnh (gather vốn của Chiến) |
| Quán | `chonoi/sim/quan.py` | Đổi `tests/test_quan_rules.py`; thêm các ca giữ chỗ khi hàng ươn và chốt giá trong `tests/test_freshness.py` | Thịnh |
| day, Shop | `chonoi/sim/day.py` | Đổi `tests/test_day.py` (kho cá thể, id mới cho Ngày kế) | Thịnh |
| HUD | `chonoi/live.py`, `chonoi/web/index.html` | Đổi `tests/test_live_ui.py`; Chiến kiểm bố cục bằng trình duyệt | Thịnh viết, Chiến kiểm |
| Smoke và contract | `game.contract.json` (`contract_version: "1.2"`, khối `freshness`) | Đổi `tests/test_smoke_p1.py`, `tests/test_python_starter_units.py` sang kho cá thể | Thịnh |

Breaking change: mọi fixture và file kho dạng đếm không còn hợp lệ ở v1.2 (mã 2). Cách cập nhật fixture ghi trong `CHANGELOG.md`.
