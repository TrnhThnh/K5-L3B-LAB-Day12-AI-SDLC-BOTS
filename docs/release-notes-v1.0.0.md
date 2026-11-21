# Quán Ăn Chợ Nổi v1.0.0

Bản phát hành đầu tiên của nhóm BOTS (Dương Minh Chiến, Trịnh Hưng Thịnh), chạy theo Test Contract v1.3.

## Điểm mới

- Buổi sáng (Lặn & Hái): bơi trong mặt cắt sông, oxy và ngạt, Máu, hái bông điên điển, bông súng, kèo nèo; bắt cá lóc, cá linh, cá kèo. Cá bơi và sinh thêm theo lịch, Cá Sấu Năm Chèo tuần tra, đuổi và cắn làm rơi hàng.
- Buổi tối (Mở Quán): 2 bếp, 4 bàn, 6 món. Khách đến theo lịch, giữ chỗ nguyên liệu, nấu, dọn món, boa và uy tín.
- Vòng 5 Ngày: kế hoạch món của Má Tư mỗi Ngày, Shop cuối Ngày bán bình oxy và áo phao, nâng cấp có hiệu lực từ Ngày sau.
- Độ tươi: mỗi nguyên liệu có id và độ tươi riêng, hao trong giỏ và trong kho, dưới 30 là ươn; giá món tính theo độ tươi lúc bắt đầu nấu.
- Cửa sổ chơi trên trình duyệt: menu, màn giới thiệu Ngày, mở quán, kết quả Ngày, tổng kết, tạm dừng, HUD đầy đủ; ba cảnh báo có chữ và biểu tượng (thủy quái gần, oxy sắp hết, khách sắp giận); chế độ tương phản cao (phím H).
- Lệnh không giao diện cho máy chấm: `headless` (gather, quan, day), `bench` (benchmark có render 1280×720), `soak` (10 Ngày liên tục).

## Cách chạy

Cần Python 3 (đã chạy trên 3.11 và 3.12) và một trình duyệt; không cần cài gói nào.

```bash
git clone https://github.com/TrnhThnh/K5-L3B-LAB-Day12-AI-SDLC-BOTS.git
cd K5-L3B-LAB-Day12-AI-SDLC-BOTS
python3 -m chonoi.live --mode day --days 5
```

Hoặc tải file `quan-an-cho-noi-v1.0.0.zip` đính kèm, giải nén, vào thư mục vừa giải nén rồi chạy lệnh thứ ba. Mở địa chỉ in ra và chọn Chơi. Điều khiển, lệnh test, headless, bench và soak ghi trong README.

## Số đo

- Test: 112 test đạt (`PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`), CI GitHub Actions trên Linux xanh.
- Benchmark seed 42, 30 s: avg 461 FPS, 1% low 197 FPS, load 62 ms (máy Windows của Chiến).
- Soak seed 7, 10 Ngày: 10/10 Ngày hoàn tất, 0 crash, chạy lại cùng seed cho kết quả gameplay giống nhau.

## Giới hạn đã biết

- Đồ họa là hình khối 2D tạm, chưa có âm thanh.
- Benchmark đo đường render phần mềm của `chonoi/bench.py`, không phải canvas trên trình duyệt; `load_ms` chưa gồm thời gian khởi động trình thông dịch.
- Soak dùng input rỗng: nhân vật đứng yên nên tiền thu bằng 0; phép thử kiểm vòng đời nhiều Ngày, không đánh giá cách chơi.
- Không làm các phần mở rộng (Lao, vợt, rắn, cháy món, Chợ Chú Sáu, Sổ tay, dòng lũ, khách đặt trước, bảng xếp hạng, phụ đề SFX).
- Đã thử chạy từ clone sạch trên Windows; trên macOS/Linux mới kiểm qua CI (test và headless), chưa mở cửa sổ chơi.
