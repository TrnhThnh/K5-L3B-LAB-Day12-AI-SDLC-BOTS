# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21, kickoff | Đề yêu cầu nhóm 4–6 người, nhóm BOTS chỉ có 2. Nhóm 2 người có được chấp nhận không? | Chưa có trả lời, PO sẽ hỏi giảng viên. Trong lúc chờ, nhóm đặt `team_size: 2` và chia mỗi người 2 module. `tools/check_team.py` báo lỗi "số thành viên phải từ 4 đến 6", CI chỉ cảnh báo chứ không chặn. Nhóm không sửa script của giảng viên. | Chiến (PO), chờ giảng viên |
| 2 | 2026-11-21, Phase 1 | Tick oxy vừa về 0 có tính là tick ngạt đầu tiên không? | Giả định là có. Sau khi trừ oxy, nếu oxy = 0 và đang dưới nước thì `zero_oxy_ticks` tăng 1. Đủ `choke_interval_ticks` thì `choke`, Máu giảm 1 và bộ đếm về 0. Lên mặt nước hoặc còn oxy thì bộ đếm về 0. | Chiến |
| 3 | 2026-11-21, Phase 1 | Giỏ còn chỗ nhưng không đủ cho cả mẻ (ví dụ còn 2 chỗ, bắt cá linh được 3) thì xử lý sao? | Giả định: nhận đủ số chỗ còn trống, phần dư bỏ đi. Phát `gather`/`fish_caught` với `count` là số thật sự vào giỏ, sau đó phát `hold_full`. Đàn cá bị bắt thì biến mất, nút đã hái thì bắt đầu mọc lại. Nếu giỏ đã đầy hẳn thì chỉ phát `hold_full`, nút và cá giữ nguyên. | Chiến |
| 4 | 2026-11-21, Phase 1 | Bấm `catch` trượt (không có cá trong `catch_radius`) có tính hồi chiêu không? | Giả định là có, khi đang dưới nước và hết hồi chiêu. Bấm `catch` ở mặt nước thì không có tác dụng và không tính hồi chiêu. | Chiến |
| 5 | 2026-11-21, Phase 1 | Bắt xong thì đàn cá còn lại không? | Giả định: đàn cá bị xóa khỏi danh sách. Khung có ghi cá bơi và sinh thêm là việc của phase sau. | Chiến |
| 6 | 2026-11-21, Phase 1 | `data` của các sự kiện gather (choke, faint, gather, fish_caught, hold_full...) gồm trường nào? | Chưa thấy trong đề nên nhóm tự đặt, ghi ở `docs/contracts/README.md`. Khi có PRD-0 thì đối chiếu lại. | Chiến (Integrator) |
| 7 | 2026-11-21, Phase 1 | `invuln_ticks` dùng vào việc gì ở Phase 1? | Giả định: Phase 1 chỉ đếm ngược, `choke` không xét `invuln_ticks`. Để dành cho các đòn đánh ở phase sau. | Chiến |
| 8 | 2026-11-21, Phase 1 | Kho giữ chỗ và món của khách bỏ đi xử lý thế nào? | Giả định giữ chỗ trong kho tới khi bắt đầu nấu. Khách bỏ đi trước khi nấu thì giải phóng phần giữ chỗ. Sau khi nấu thì bỏ món của khách, không hoàn nguyên liệu. | Thịnh, chờ PO đối chiếu PRD-0 |
| 9 | 2026-11-21, Phase 1 | Thứ tự trong tick và thanh toán? | Bếp và khách đếm ngược trước tương tác, khách mới đến sau tương tác. Hết bàn thì bỏ lượt. Chốt boa lúc phục vụ, cộng tiền và uy tín khi ăn xong. | Thịnh, chờ PO đối chiếu PRD-0 |
