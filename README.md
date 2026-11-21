# Quán Ăn Chợ Nổi — nhóm BOTS

Game 2D quản lý quán ăn miền Tây. Buổi sáng, Út Sen lặn bắt cá và hái rau trên sông Chín Khúc, tránh Cá Sấu Năm Chèo và giữ oxy. Buổi tối, em nấu và dọn món cho khách trên nhà bè của Má Tư. Cuối ngày, tiền kiếm được dùng mua bình oxy và áo phao cho lần lặn sau. Một lượt chơi gồm 5 Ngày.

Nhóm 2 người: Dương Minh Chiến (`duongchien147`) và Trịnh Hưng Thịnh (`TrnhThnh`), phân công ở [TEAM.md](TEAM.md) và [docs/plan/phan-cong.md](docs/plan/phan-cong.md). Đề lab gốc ở [docs/LAB.md](docs/LAB.md).

## Chạy từ clone sạch (3 lệnh, macOS hoặc Linux)

```bash
git clone https://github.com/TrnhThnh/K5-L3B-LAB-Day12-AI-SDLC-BOTS.git
cd K5-L3B-LAB-Day12-AI-SDLC-BOTS
python3 -m chonoi.live --mode day --days 5
```

Mở địa chỉ in ra (mặc định `http://127.0.0.1:8000/`) bằng trình duyệt và chọn **Chơi**. Bản phát hành `v1.0.0` có file nén đính kèm: giải nén rồi chạy lệnh thứ ba trong thư mục vừa giải nén.

Yêu cầu môi trường: Python 3 (nhóm đã chạy trên 3.11 và 3.12), chỉ dùng thư viện chuẩn nên không cần cài gói nào; một trình duyệt hiện đại. `build_cmd` là `true` vì không có bước build. Trên Windows có thể dùng `python` thay `python3`.

## Điều khiển

| Phím | Tác dụng |
|---|---|
| WASD hoặc mũi tên | Bơi (buổi sáng), đi lại (buổi tối) |
| E | Hái nút ở mặt nước, cập bến; nấu, lấy món, dọn món |
| Space | Bắt cá khi đang lặn |
| P hoặc Esc | Tạm dừng; trong menu tạm dừng: M về menu |
| 1 / 2, Enter | Trong Shop: mua bình oxy / áo phao, đóng Shop |
| H | Bật/tắt chế độ tương phản cao (nhớ giữa các lần mở) |
| R | Chơi lại |

Sau mỗi ca tối, mua nâng cấp trong Shop và chọn Đóng Shop để chốt Ngày.

Ba cảnh báo luôn có chữ và biểu tượng ⚠: thủy quái ở gần (thêm viền màn hình), oxy sắp hết (dưới 25%) hoặc đã hết, khách sắp giận (kiên nhẫn dưới 25%, thêm 😠 trên bàn). Ở chế độ tương phản cao, nền đen, chữ trắng, cảnh báo khung đen viền vàng dày. Ảnh chụp ở [docs/proof/phase-4/ui/](docs/proof/phase-4/ui/).

## Cách tính điểm

Điểm = `earned + 100 × floor(uy tín)`. `earned` là tổng tiền thu (tiền món cộng boa), không giảm khi mua nâng cấp. Uy tín bắt đầu 3.0, trong khoảng [0, 5]: khách bỏ về vì hết kiên nhẫn trừ 0.5, mỗi lần nhận boa cộng 0.2. Giá món chốt theo độ tươi trung bình của nguyên liệu lúc bắt đầu nấu; boa bằng 20% giá đã chốt nếu khách còn ít nhất nửa kiên nhẫn lúc được dọn món.

## Lệnh test, headless, benchmark, soak

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v                          # toàn bộ test (1 lệnh)
python3 -m chonoi.headless --mode day --days 1 --seed 7 --ticks 22200 --out day.jsonl   # một Ngày không giao diện
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json                       # benchmark có render
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json                               # soak 10 Ngày
```

Kiểm bàn giao kho giữa hai tiến trình với fixture v1.2:

```bash
python3 -m chonoi.headless --mode gather --seed 7 --ticks 1 --scenario docs/proof/phase-3/dock.scenario.json --inputs docs/proof/phase-1/dock-inputs.json --inventory-out inventory.json --out gather.jsonl
python3 -m chonoi.headless --mode quan --seed 7 --ticks 0 --inventory inventory.json --out quan.jsonl
```

Cách thiết lập Python cho bộ test trên Windows có trong [AGENTS.md](AGENTS.md). Các tag `phase-1`, `phase-2` và `phase-3` lần lượt dùng contract v1.0, v1.1 và v1.2; `main` và `v1.0.0` dùng v1.3.

**Benchmark** (`chonoi/bench.py`): cảnh buổi sáng lõi seed 42, Út Sen đứng ở bến, cá bơi, Cá Sấu, độ tươi. Mô phỏng chạy 60 tick/s theo đồng hồ thật; mỗi khung render toàn cảnh vào framebuffer RGB 1280×720 bằng phần mềm (thư viện chuẩn, chạy được trên máy không có màn hình). Làm nóng 3 s, đo `--duration` s. `--frame-out khung.png` ghi khung cuối để xem. Kết quả trên máy của Chiến (Windows, Python 3.11): avg 461 FPS, 1% low 197 FPS, load 62 ms, xem [docs/proof/phase-4/bench.json](docs/proof/phase-4/bench.json). Cửa sổ chơi trên trình duyệt đo được 60 FPS ở 1280×720.

## Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `chonoi/sim/gather.py` | Buổi sáng: bơi, oxy, ngạt, hái, bắt cá, cá bơi/sinh, Cá Sấu, độ tươi trong giỏ |
| `chonoi/sim/quan.py` | Buổi tối: khách, giữ chỗ theo id, bếp, dọn món, tiền, uy tín, độ tươi trong kho |
| `chonoi/sim/day.py` | Vòng Ngày gather → quan → Shop, nâng cấp |
| `chonoi/runner.py`, `chonoi/headless.py` | Vòng tick, pause, JSONL, CLI headless |
| `chonoi/live.py`, `chonoi/web/index.html` | Cửa sổ chơi trên trình duyệt: menu, HUD, cảnh báo, Shop |
| `chonoi/bench.py`, `chonoi/soak.py` | Benchmark có render, soak nhiều Ngày |
| `game.contract.json` | Test Contract v1.3: lệnh và mọi số liệu luật |
| `tests/` | Test hộp đen qua `headless_cmd` và test đơn vị |
| `docs/` | Kế hoạch, hợp đồng, ADR, clarify, kiểm chứng và bằng chứng từng phase, retro, nhật ký AI |

## Sáng tạo của nhóm

Chưa có phần sáng tạo ngoài yêu cầu. Nhóm hai người ưu tiên làm đúng lõi và Test Contract qua cả bốn phase.

## Giới hạn đã biết

- Đồ họa là hình khối 2D tạm, chưa có âm thanh.
- Benchmark đo đường render phần mềm của `chonoi/bench.py`; cửa sổ chơi vẽ bằng canvas trên trình duyệt, đo riêng bằng trình duyệt.
- `load_ms` tính từ lúc nạp module `chonoi.bench`, chưa gồm thời gian khởi động trình thông dịch Python.
- Không làm phần mở rộng (Lao, vợt, rắn, cháy món, Chợ Chú Sáu, Sổ tay, dòng lũ, khách đặt trước, bảng xếp hạng, phụ đề SFX) vì nhóm dưới 5 người.
