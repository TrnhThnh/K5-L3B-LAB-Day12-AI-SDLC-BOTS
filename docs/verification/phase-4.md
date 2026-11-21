# Phase 4 — verification

## Truy vết AC

| AC | Bằng chứng | Kết quả |
|---|---|---|
| AC-P4-01 Benchmark có render | [`bench.json`](../proof/phase-4/bench.json), [`bench-last-frame.png`](../proof/phase-4/bench-last-frame.png) | Đạt: 30 s, 13,834 frames; avg 461.15 FPS, 1% low 197.27 FPS, load 62 ms. Các ngưỡng 60/30 FPS và 10 s đều đạt. |
| AC-P4-02 Cảnh báo và tương phản cao | [Cảnh báo thường](../proof/phase-4/ui/normal-gather-monster-oxy.png), [thủy quái + oxy tương phản cao](../proof/phase-4/ui/hc-gather-monster-oxy.png), [khách giận tương phản cao](../proof/phase-4/ui/hc-quan-angry.png) | Có bằng chứng ảnh cho cảnh thường và tương phản cao; code hiển thị chữ/biểu tượng. |
| AC-P4-03 Soak CLI, 10 Ngày và replay | [`game.contract.json`](../../game.contract.json), [`soak.json`](../proof/phase-4/soak.json), [`test_soak.py`](../../tests/test_soak.py) | Đạt: seed 7 hoàn tất 10/10 Ngày, 0 crash; trace xác nhận kế hoạch D1–D5 lặp lại và kết quả từng Shop. Replay cùng seed khớp các trường gameplay, không so `duration_s`. |
| AC-P4-04 Regression P1–P3 và Phase 4 | [`unittest.txt`](../proof/phase-4/unittest.txt) | Đạt: 112 test, `OK`. |
| AC-P4-05 Đóng gói và phát hành | [`README.md`](../../README.md), tags Git | README ghi cách chạy từ clone sạch tối đa 3 lệnh. Chưa xác minh bằng clone sạch; tag `phase-4` và GitHub Release `v1.0.0` chưa được tạo tại lần kiểm này. |

Lệnh kiểm chứng trên Windows: đặt `$env:PYTHONPATH="tests;."`, sau đó chạy `python3 -m chonoi.soak --seed 7 --days 10 --out docs\proof\phase-4\soak.json` và `python3 -m unittest discover -s tests -v`. Môi trường này cần `python3` shim tạm theo [AGENTS.md](../../AGENTS.md); các lệnh trên đã chạy bằng Python 3.11.

Soak dùng input rỗng tất định: nhân vật đứng yên và các pha kết thúc theo timeout. Vì vậy phép thử xác nhận vòng chuyển pha, lặp kế hoạch và tiến trình nhiều Ngày; kết quả `earned: 0` không phải kiểm chứng hiệu quả của chiến lược chơi. Báo cáo đo `duration_s` thực tế; trường này được bỏ qua khi so replay.

## Trạng thái bàn giao

Benchmark, cảnh báo, tương phản cao và soak đã có code/bằng chứng trên `main`. Chưa có tag `phase-4` hay GitHub Release `v1.0.0`; tạo chúng từ cùng commit sau khi kiểm clone sạch và chốt bản đóng gói.
