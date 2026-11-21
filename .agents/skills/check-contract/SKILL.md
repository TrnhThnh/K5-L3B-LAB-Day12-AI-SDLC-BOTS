---
name: check-contract
description: Kiểm luật sim của nhóm BOTS có giữ đúng quy tắc vàng không (không hard-code số, không random/đồng hồ hệ thống, sắp id, tất định từng byte). Dùng trước khi push hoặc gắn tag, và sau mỗi lần agent sửa chonoi/sim/.
---

# check-contract (Chiến viết, Phase 1)

Chạy theo thứ tự. Bước nào lỗi thì dừng và báo lỗi, không tự sửa test cho xanh.

1. **Không dùng random toàn cục hay đồng hồ hệ thống** trong `chonoi/sim/`:
   ```bash
   grep -nE "import random|random\.|time\.|datetime" chonoi/sim/*.py
   ```
   Không được có kết quả nào, trừ `ramp.py`. Số ngẫu nhiên phải đi qua `self.rng.get("<tên luồng>")`.

2. **Không hard-code số của contract** (tốc độ, bán kính, sức chứa, thời gian):
   ```bash
   for f in chonoi/sim/gather.py chonoi/sim/quan.py; do
     grep -nE "[^_a-zA-Z0-9.\"'\[]([2-9][0-9]*|1[0-9]+|[0-9]+\.[0-9]*[1-9])\b" "$f" | grep -vE "^[0-9]+:( {0,6}[^ ]| *#)" | sed "s|^|$f:|"
   done
   ```
   Lệnh này bỏ qua số 0, số 1, docstring và comment. Đọc từng dòng còn lại: `% 360` hay `60.0` (TICK) là hằng toán học, giữ được. Số nào có trong `game.contract.json` thì phải đọc qua `self.t[...]`.

3. **Sắp thực thể bằng `sort_by_id`** mỗi khi duyệt nút, cá, khách hoặc bếp để chọn đối tượng. Dùng `sorted(...)` theo id dạng chuỗi là sai vì F10 sẽ đứng trước F2.

4. **Tất định**: cùng seed thì ra cùng byte.
   ```bash
   python3 -m chonoi.headless --mode gather --seed 7 --ticks 2000 --inputs docs/proof/phase-1/gather-demo.inputs.json --out /tmp/a.jsonl
   python3 -m chonoi.headless --mode gather --seed 7 --ticks 2000 --inputs docs/proof/phase-1/gather-demo.inputs.json --out /tmp/b.jsonl
   cmp /tmp/a.jsonl /tmp/b.jsonl && echo OK
   ```

5. **Toàn bộ test**: `PYTHONPATH=tests:. python3 -m unittest discover -s tests`, phải ra `OK`.

Báo lại ngắn gọn: bước nào đạt, bước nào lỗi (kèm file:dòng). Ghi một dòng vào `docs/ai-usage-log.md` nếu agent đã sửa code.
