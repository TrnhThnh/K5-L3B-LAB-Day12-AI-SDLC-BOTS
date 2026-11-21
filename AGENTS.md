# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan` (mở địa chỉ in ra; WASD, E, Space, R)
- Chỉ test luật gather: `PYTHONPATH=tests:. python3 -m unittest tests.test_gather_rules tests.test_gather_p2 -v`
- Vòng ngày (v1.1): `python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out day.jsonl`; test: `tests.test_day`
- **Windows** (không có `python3`): test hộp đen gọi `headless_cmd` = `python3 ...` nên báo `FileNotFoundError`. Không sửa `headless_cmd`, vì bộ chấm chạy trên Linux. Cách xử lý: tạo `python3.exe` (copy `python.exe` cùng `python3*.dll` sang một thư mục, rồi thêm thư mục đó vào PATH) hoặc chạy trong WSL. Trên PowerShell, `PYTHONPATH` phân cách bằng `;`: `$env:PYTHONPATH="tests;."`.

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py`, vòng ngày và Shop ở `chonoi/sim/day.py`. Nhóm đã sửa khung (`runner.py` cho pause/day, `inputs.py` cho `buy`/`pause`/`shop_done`, `scenario.py`, `contract.py`, `inventory.py` cho v1.1); lý do ghi trong commit.
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Nhóm BOTS (2 người, xem `TEAM.md`)
- Chiến (`duongchien147`) giữ `chonoi/sim/gather.py`, `chonoi/live.py`, `chonoi/web/`. Thịnh (`TrnhThnh`) giữ `chonoi/sim/quan.py`, `tests/`.
- Agent làm việc cho ai thì chỉ sửa file của người đó. Muốn sửa file chung (`game.contract.json`, `docs/contracts/`, `AGENTS.md`) thì báo Chiến.
- Dữ liệu sự kiện và thứ tự xử lý trong một bước của gather: `docs/contracts/README.md`. Giả định luật chưa rõ trong đề: `docs/clarify.md`.
- Báo cáo (`docs/verification`, `retro`, `members`, ...) viết xong thì cho chạy qua skill humanizer để văn tự nhiên, nhưng giữ nguyên số liệu và output lệnh.

## Skills / hooks của nhóm
- `.agents/skills/check-contract/` (Chiến): kiểm không hard-code số, không random/đồng hồ hệ thống, sắp bằng `sort_by_id`, tất định từng byte, rồi chạy toàn bộ test. Dùng trước khi push hoặc gắn tag, và sau mỗi lần agent sửa `chonoi/sim/`.
- (Thịnh viết skill thứ hai, ví dụ `run-proof`: chạy test và headless rồi lưu kết quả vào `docs/proof/phase-n/`.)
