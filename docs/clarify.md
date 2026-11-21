# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

Các giả định #2 đến #7 ghi lúc chưa có PRD-0. Khi PRD-0 có trên lab board, Chiến đã đối chiếu lại; cột trả lời ghi kết quả đối chiếu.

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21, kickoff | Đề yêu cầu nhóm 4–6 người, nhóm BOTS chỉ có 2. Nhóm 2 người có được chấp nhận không? | Chưa có trả lời, PO sẽ hỏi giảng viên. Trong lúc chờ, nhóm đặt `team_size: 2` và chia mỗi người 2 module. `tools/check_team.py` báo lỗi "số thành viên phải từ 4 đến 6", CI chỉ cảnh báo chứ không chặn. Nhóm không sửa script của giảng viên. | Chiến (PO), chờ giảng viên |
| 2 | 2026-11-21, Phase 1 | Tick oxy vừa về 0 có tính là tick ngạt đầu tiên không? | Giả định là có. PRD-0 mục F xác nhận: "kể cả bước vừa chạm 0", ngạt lần đầu ở t+59. Code giữ nguyên. | PRD-0 |
| 3 | 2026-11-21, Phase 1 | Giỏ còn chỗ nhưng không đủ cho cả mẻ thì xử lý sao? | Giả định ban đầu là nhận phần vừa, phần dư bỏ đi. **Sai so với PRD-0 mục F**: thiếu chỗ thì phát `hold_full`, giữ nguyên đàn hoặc nút, không thêm gì. Đã sửa code và test. | PRD-0 |
| 4 | 2026-11-21, Phase 1 | Bấm `catch` trượt có tính hồi chiêu không? | Giả định ban đầu là có. **Sai so với PRD-0**: "không có đàn trong tầm thì không có sự kiện bắt hay hồi chiêu", hồi chiêu chỉ đặt khi bắt thành công (Ticket-02 cũng ghi "tính từ lần bắt thành công"). Đã sửa. | PRD-0 |
| 5 | 2026-11-21, Phase 1 | Bắt xong thì đàn cá còn lại không? | Giả định đàn bị xóa. PRD-0 xác nhận ("xóa đàn"). | PRD-0 |
| 6 | 2026-11-21, Phase 1 | `data` của các sự kiện gather gồm trường nào? | Bản đầu tự đặt. Đã đổi theo PRD-0 mục E: `gather.amount`, `fish_caught.yield`, `hold_full {action, node_id/fish_id, required, free}`, `oxygen_empty {oxygen_ticks: 0}`, `faint {cause, lost, hp: 0}`. Xem `docs/contracts/README.md`. | PRD-0 |
| 7 | 2026-11-21, Phase 1 | `invuln_ticks` dùng vào việc gì ở Phase 1? | Phase 1 chỉ đếm ngược. Ticket-02 xác nhận ngạt xuyên bất tử; bất tử dùng cho cú chạm của Cá Sấu ở Phase 2. | Ticket-02 |
| 8 | 2026-11-21, Phase 1 | Lượt khách có bàn trống nhưng không món nào đủ nguyên liệu thì khách có ngồi không? | Giả định: không tạo khách, chỉ phát `no_dish`, bàn vẫn trống. PRD-0 chỉ ghi "không có món đủ thì phát no_dish". | Chiến |
| 9 | 2026-11-21, Phase 1 | Trường `dish` của bếp trong snapshot là gì? | Giả định: dùng payload món `{order_id, dish_id, base_price}`, giống `hand`. | Chiến |
| 10 | 2026-11-21, Phase 1 | Id khách mới dùng tiền tố nào? | Giả định: `C` (C1, C2...), nối sau hậu tố lớn nhất của khách fixture. `order_id` bằng id khách theo PRD-0. | Chiến |
| 11 | 2026-11-21, Phase 1 | Khách chờ hết kiên nhẫn đúng bước hết ca thì tính `patience` hay `closing`? | Tính `closing`, không trừ uy tín, vì PRD-0 chỉ trừ uy tín "nếu ca còn giờ". | Chiến |
