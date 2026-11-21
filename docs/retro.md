# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: fixture một tick bắt được trường hợp đóng ca trùng lúc hết kiên nhẫn.
- Điều vướng: CLI hiện tại chưa dựng được day nên mới kiểm được giao diện truyền kế hoạch vào quán.
- Hành động Phase 3: Thịnh chạy lại smoke một và nhiều Ngày trên commit tích hợp trước khi Chiến gắn tag.

## Phase 4 (cuối)

- **Hành động từ Phase 2.** Thịnh đã chạy smoke bàn giao kho và kiểm hai Ngày liên tiếp ở Phase 3. Trace ghi I7 ở Ngày 1, I8 ở Ngày 2. QA sau tag kiểm thêm đủ năm lần đóng Shop. [Trace hai Ngày](proof/phase-3/two-days.jsonl) · [Kết quả kiểm ba tag](verification/phase-3.md)
- **Điều làm tốt.** Fixture một tick giúp hai người phân biệt lỗi tính tiền khi đóng ca với lỗi hao tươi lúc bàn giao. Chiến còn phát hiện qua HUD rằng mục “Cần lấy” tính cả hàng ươn dù bộ test mô phỏng đã xanh.
- **Điều vướng.** Nhánh quán và main phát triển song song. AI từng kết luận sai về tiến độ của Thịnh khi chỉ nhìn main. Khi tích hợp, Chiến so tên test ở cả hai nhánh và giữ lại hai ca còn thiếu về sáu món tại B2 và thứ tự nhận đơn. [Commit tích hợp](https://github.com/TrnhThnh/K5-L3B-LAB-Day12-AI-SDLC-BOTS/commit/17c1108)
- **Số liệu.** Tại d3c89ff, git shortlog -sn HEAD ghi 10 commit của duongchien147 và 9 của TrnhThnh, tính cả merge. Hai người chưa ghi số token hoặc chi phí cá nhân.
- **Nếu làm lại.** Trước khi chia lát, hai người sẽ thống nhất một fixture kho, một lệnh chạy và commit gốc. Khi review, mỗi người chạy fixture ở đầu vào và đầu ra của module bên kia trước khi ghi kết luận vào verification.
- **Soak Phase 4.** Lệnh mới chạy đủ 10 Ngày và replay cùng seed đạt 0 crash; input rỗng cho earned bằng 0, nên đây là kiểm tra vòng đời, không phải đánh giá chơi tối ưu. [Báo cáo và phạm vi](verification/phase-4.md)
- **Benchmark và cảnh báo.** Bằng chứng ghi 461.15 FPS trung bình, 197.27 FPS 1% low, load 62 ms; có ảnh cảnh báo ở chế độ thường và tương phản cao. [Ma trận Phase 4](verification/phase-4.md)
- **Lỗi AI và xác minh.** Khi tăng contract lên 1.3, AI ban đầu chưa cập nhật reader kho còn nhận schema cá thể ở 1.2; regression bắt lỗi ở bước đọc lại kho bằng headless. Bản tích hợp giữ schema kho v1.2 và so phiên bản theo số; suite sau tích hợp chạy lại đủ 112 test. Bài học: chạy cả test xuyên tiến trình sau thay đổi version, không chỉ test parser hoặc soak riêng.
- **Việc tiếp theo.** Clone sạch để kiểm 3 lệnh, chuẩn bị gói phát hành, rồi tạo tag `phase-4` và GitHub Release `v1.0.0` từ cùng commit sau khi regression và soak đạt.
