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
| 12 | 2026-11-21, Phase 2 | "Lấy hướng ban đầu theo seed" và "đổi hướng theo seed" là góc kiểu gì? | Giả định: góc thực chọn đều trong [0, 360). Đề cho phép "chọn ngẫu nhiên nhất quán trong mỗi bản nộp". | Chiến |
| 13 | 2026-11-21, Phase 2 | 8 đàn đầu ca chọn điểm thế nào? | Giả định: chạy 8 lần đúng thuật toán sinh cá (trọng số loài, điểm cách mọi đàn đang sống > 1 m), nên 8 đàn luôn ở 8 điểm khác nhau. Không phát `fish_spawned` cho đàn đầu ca. | Chiến |
| 14 | 2026-11-21, Phase 2 | Ngưỡng "người chơi ở d ≥ 10" của Cá Sấu lấy từ đâu? | Lấy cận dưới `depths` của loài (cá sấu [10, 30]), vì Ticket-02 mô tả rắn dùng "ngưỡng độ sâu của loài" (d < 8). | Chiến |
| 15 | 2026-11-21, Phase 2 | Bước Cá Sấu vừa hết recoil có được phát hiện hoặc chạm không? | Không. Đề ghi "hết recoil về patrol, xét phát hiện/chạm từ bước kế". | Ticket-02 |
| 16 | 2026-11-21, Phase 2 | Có chụp snapshot ở tick đổi pha không, khi tick đó không phải bội số của `--snapshot-every`? | Có. Đề ghi "snapshot đổi pha ghi pha mới với phase_tick:0", nên runner luôn chụp ở tick đổi pha (vẫn tối đa một snapshot mỗi tick). | Chiến |
| 17 | 2026-11-21, Phase 2 | `buy` với lệnh chưa hỗ trợ (ví dụ mở rộng chưa bật) xử lý sao? | Trong Shop phát `buy_failed` với `reason: "unknown"` (đề: "Shop phát buy_failed nếu gặp lệnh không hỗ trợ"). Ngoài Shop thì bỏ qua. | Chiến |
| 18 | 2026-11-21, Phase 2 | Khối `gather`/`quan` trong scenario `day` áp cho Ngày nào? | Áp cho mọi Ngày (đề: "mẫu khởi tạo mỗi Ngày"), kể cả `gather.hold`. | Chiến |
| 19 | 2026-11-21, Phase 1 | Kho giữ chỗ và món của khách bỏ đi xử lý thế nào? | Giả định giữ chỗ trong kho tới khi bắt đầu nấu. Khách bỏ đi trước khi nấu thì giải phóng phần giữ chỗ. Sau khi nấu thì bỏ món của khách, không hoàn nguyên liệu. | Thịnh |
| 20 | 2026-11-21, Phase 1 | Thứ tự trong tick và thanh toán? | Bếp và khách đếm ngược trước tương tác, khách mới đến sau tương tác. Hết bàn thì bỏ lượt. Chốt boa lúc phục vụ, cộng tiền và uy tín khi ăn xong. | Thịnh |
| 21 | Phase 2 | Chọn đơn nào cho bếp và xử lý khách cuối ca? | TICKET-02 §1.3 chốt ưu tiên order_tick rồi id bàn. Khách còn ăn trả ngay; khách còn chờ rời không mất uy tín. | TICKET-02 |
Phase 3: ticket không nêu công thức giá. Theo quyết định của Thịnh, dùng floor(giá menu × độ tươi trung bình các cá thể / 100) khi bắt đầu nấu, sau hao tươi của tick đó.
| 22 | 2026-11-21, Phase 4 | "Benchmark có render" chạy thế nào trên máy chấm không có màn hình? | `bench_cmd` render toàn cảnh buổi sáng vào framebuffer RGB 1280×720 bằng phần mềm (thư viện chuẩn), mô phỏng 60 tick/s theo đồng hồ thật. Cửa sổ chơi trên trình duyệt đo FPS riêng (60 FPS). | Chiến |
| 23 | 2026-11-21, Phase 4 | `load_ms` tính từ lúc nào? | Từ lúc nạp module `chonoi.bench` tới khi khung đầu tiên render xong; chưa gồm thời gian khởi động trình thông dịch (ghi ở README, mục Giới hạn). | Chiến |
| 24 | 2026-11-21, Phase 4 | Soak dùng chiến lược input nào khi đề không chỉ định? | Dùng input rỗng tất định; các pha chạy đến timeout để kiểm đủ vòng gather → quan → shop và nhiều Ngày. Kết quả không đánh giá chất lượng chiến lược chơi. | Thịnh |
