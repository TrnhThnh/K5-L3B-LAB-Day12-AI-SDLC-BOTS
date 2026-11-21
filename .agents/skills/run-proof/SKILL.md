---
name: run-proof
description: Chạy test và headless để lưu bằng chứng kiểm chứng cho từng phase của nhóm BOTS.
---

Từ thư mục chứa game.contract.json, đặt N là số phase đang kiểm và chạy trong Bash:

```bash
mkdir -p "docs/proof/phase-$N"
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v > "docs/proof/phase-$N/tests.log" 2>&1
```

Kiểm mã thoát và dòng cuối log. Nếu test lỗi, ghi tên test và lỗi vào verification. Trên Windows dùng môi trường Python ghi trong AGENTS.md.

Chọn scenario hoặc inputs đúng AC. Ví dụ kiểm luồng kho Phase 1:

```bash
p="docs/proof/phase-$N"
python3 -m chonoi.headless --mode gather --seed 1 --ticks 2000 --inputs docs/proof/phase-1/gather-demo.inputs.json --out "$p/gather-demo.jsonl" --inventory-out "$p/gather-demo.kho.json"
python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --inventory "$p/gather-demo.kho.json" --out "$p/quan-doc-kho.jsonl"
```

Đối chiếu sự kiện gather_end và stock ở tick 0 của quán. Ghi seed, tick quan sát và đường dẫn bằng chứng trong docs/verification/phase-N.md. Kiểm git status --ignored vì repo có thể bỏ qua JSONL và log; khi nộp, chỉ thêm bằng chứng được trích dẫn.
