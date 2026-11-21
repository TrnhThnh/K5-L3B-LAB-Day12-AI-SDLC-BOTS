# TrnhThnh — Trịnh Hưng Thịnh

Tôi phụ trách luật quán và QA. Khi chuyển kho cá thể, tôi kiểm tra một nguyên liệu từ giỏ đến lúc nấu, cùng việc giữ chỗ và giá với cá thể có độ tươi khác nhau. [Commit chuyển kho](https://github.com/TrnhThnh/K5-L3B-LAB-Day12-AI-SDLC-BOTS/commit/7d7f196)

Tôi giúp Chiến kiểm bản tích hợp: chạy từng tag với fixture tương ứng, rồi chạy năm Ngày trên main và kiểm Shop cuối. [Kết quả review](../verification/phase-3.md)

Ở Phase 4, tôi bổ sung soak 10 Ngày, kiểm D1–D5 lặp lại và chạy regression: seed 7 đạt 10/10, 0 crash. Input rỗng nên earned bằng 0, không đánh giá chiến lược chơi. [Test](../../tests/test_soak.py) · [Bằng chứng](../proof/phase-4/soak.json)

AI từng kết luận mode day chưa có vì chỉ xem nhánh quán; tôi so lịch sử và chạy CLI trên main để xác minh. Khi bump contract 1.3, AI bỏ sót reader kho chỉ nhận schema 1.2; smoke gather → kho → quán bắt lỗi, rồi tôi xác minh 112 test sau tích hợp. [Đối chiếu](../verification/phase-2.md) · [Log](../proof/phase-4/unittest.txt)

Bài học: ghi commit/trạng thái đã chạy; thay contract phải kiểm luồng xuyên tiến trình, không chỉ lệnh mới.
