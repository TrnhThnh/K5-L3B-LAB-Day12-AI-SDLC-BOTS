# Kịch bản demo (≤ 5 phút)

Theo checklist demo của Ticket-04: chơi một Ngày, chạy test, chỉ bằng chứng chia việc, mở ma trận truy vết. Demo trực tiếp hay quay video .mp4 đều dùng kịch bản này. Hai người chia lời: Chiến nói phần 1 và 3, Thịnh nói phần 2 và 4.

## Chuẩn bị trước khi quay (không tính giờ)

1. Mở terminal ở thư mục repo, `git pull`.
2. Chạy sẵn bộ test một lần để biết chạy được (mất khoảng 1 phút): `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`. Trên Windows xem mục Lệnh trong `AGENTS.md`.
3. Mở sẵn các tab trình duyệt:
   - Repo: https://github.com/TrnhThnh/K5-L3B-LAB-Day12-AI-SDLC-BOTS
   - Commits: https://github.com/TrnhThnh/K5-L3B-LAB-Day12-AI-SDLC-BOTS/commits/main
   - Commit gộp nhánh của Thịnh: https://github.com/TrnhThnh/K5-L3B-LAB-Day12-AI-SDLC-BOTS/commit/17c1108
   - Release: https://github.com/TrnhThnh/K5-L3B-LAB-Day12-AI-SDLC-BOTS/releases/tag/v1.0.0
4. Chạy game: `python3 -m chonoi.live --mode day --days 5`, mở `http://127.0.0.1:8000/`, để ở menu chính.
5. Quay màn hình: Windows dùng Xbox Game Bar (Win + Alt + R) hoặc OBS; macOS dùng Cmd + Shift + 5. Xuất .mp4.

## 1. Chơi một Ngày (0:00–2:00, Chiến)

| Làm | Nói |
|---|---|
| Bấm Chơi. Màn "Ngày 1" hiện món Má Tư định nấu. | "Đầu Ngày, Má Tư báo hôm nay nấu cá lóc nướng trui và gỏi bông súng, HUD ghi nguyên liệu cần lấy." |
| Bơi sang phải dọc mặt nước, bấm E ở hai nút bông súng (N3 ở x 44, N4 ở x 60). | "Hái ở mặt nước bằng E. Thanh dưới cùng đếm đã lấy trên cần lấy, kèm độ tươi." |
| Lặn xuống chỗ cá lóc (cá màu xanh rêu), bấm Space khi chữ "Space: bắt cá lóc" hiện. | "Dưới nước thì mất oxy, Space để bắt cá. Gần Cá Sấu sẽ có cảnh báo Thủy quái." |
| Bấm H một lần rồi bấm H lại. | "Chế độ tương phản cao cho người khó nhìn màu." |
| Ngoi lên, bơi về bến bên trái, bấm E. | "Cập bến thì kho mang về quán." |
| Màn "Chiều tối" hiện kho và số suất nấu được, bấm phím để mở quán. | |
| Chờ khách đến (khoảng 2 giây), đi tới bếp B1 bấm E nấu, chờ chín, E lấy món, đi tới bàn của khách bấm E. | "Khách giữ đúng nguyên liệu khi gọi. Nấu, bưng, dọn trước khi hết kiên nhẫn thì được boa." |
| Để ca tối chạy hết (hoặc tua video), màn "Kết quả Ngày 1" hiện, bấm phím vào Shop. Bấm 1 hoặc 2 nếu đủ tiền, Enter để đóng Shop. | "Cuối Ngày xem kết quả, mua nâng cấp, đóng Shop là xong một Ngày." |

Mẹo: ca tối dài 3 phút. Khi quay video, cắt đoạn chờ hoặc tua nhanh, ghi chữ "tua nhanh" lên video.

## 2. Chạy test (2:00–2:45, Thịnh)

Chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`, cuộn tới dòng cuối `Ran 112 tests ... OK`. Mở tab Actions trên GitHub cho thấy CI xanh.

Nói: "Bộ test hộp đen chạy qua `headless_cmd`, gồm regression cả bốn phase. CI chạy lại trên Linux mỗi lần push."

## 3. Bằng chứng chia việc (2:45–3:45, Chiến)

| Mở | Nói |
|---|---|
| `TEAM.md` | "Nhóm hai người, chia theo hai buổi: Chiến giữ buổi sáng, vòng ngày, giao diện; Thịnh giữ buổi tối, QA, độ tươi." |
| `docs/plan/phan-cong.md` | "Checklist từng phase, đánh dấu ai làm gì." |
| Tab Commits | "Commit của cả hai tài khoản trên `main`." |
| Commit `17c1108` | "Thịnh làm Phase 2 trên nhánh riêng; khi gộp, nhóm giữ tài liệu và test của Thịnh, chuyển test sang schema mới." |

## 4. Ma trận truy vết (3:45–4:45, Thịnh)

| Mở | Nói |
|---|---|
| `docs/verification/phase-4.md` | "Mỗi AC nối với bằng chứng và kết quả." |
| Bấm link `bench.json` | "Benchmark seed 42, 30 giây: 461 FPS trung bình, 1% low 197." |
| Bấm link ảnh `hc-gather-monster-oxy.png` | "Cảnh báo ở chế độ tương phản cao." |
| `docs/verification/phase-3.md`, bấm một link proof | "Phase 3: kho cá thể và độ tươi, có bằng chứng chạy thật." |
| Tab Release `v1.0.0` | "Bản phát hành kèm file nén chạy được, cùng commit với tag `phase-4`." |

Kết (4:45–5:00): "Đó là Quán Ăn Chợ Nổi của nhóm BOTS. Cảm ơn thầy cô."
