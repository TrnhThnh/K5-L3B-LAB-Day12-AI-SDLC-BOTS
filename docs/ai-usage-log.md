# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | duongchien147 | Claude Code (Opus 5.5), VS Code | Đọc repo, lập checklist, chia việc cho nhóm 2 người. Viết lát 1–2 của `chonoi/sim/gather.py`, `tests/test_gather_rules.py` (19 test), hợp đồng sự kiện, skill `check-contract`, các báo cáo Phase 1 | Chưa đo, xem `/cost` cuối phiên rồi điền | Kịch bản demo đầu tiên AI tính sai đường bơi nên không bắt được cá (kho ra `{"items":{}}`). Phát hiện khi đọc event trong JSONL, sau đó tính lại tọa độ. Ở lượt sửa `docs/contracts/README.md`, AI tự đặt tên sự kiện `customer_arrived` không có trong khung. Người đọc lại thấy và xóa. Lệnh grep đầu tiên trong skill ra quá nhiều dòng rác, phải viết lại. |
