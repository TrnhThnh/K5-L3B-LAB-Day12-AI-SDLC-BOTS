"""File kho (Contract G, giữ nguyên ở v1.1): {"items": {id: số nguyên >= 0}}.

Đọc: từ chối sai schema / id lạ / số âm (BadInput -> mã 2).
Ghi: bỏ mục bằng 0, qua file tạm cùng thư mục rồi thay thế, byte-ổn-định.
"""

import json

from .ids import sort_by_id
import os
import tempfile

from .errors import BadInput

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
# v1.1 (Ticket-02): thêm cá kèo và kèo nèo
KINDS = KINDS_P1 + ("ca_keo", "keo_neo")


def validate_items(items, kinds=KINDS):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def validate_individuals(items):
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể")
    seen = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {"id", "kind", "fresh"}:
            raise BadInput("cá thể cần đúng id, kind, fresh")
        ident, fresh = item["id"], item["fresh"]
        if not isinstance(ident, str) or not ident or ident in seen or item["kind"] not in KINDS:
            raise BadInput("id hoặc kind không hợp lệ")
        if type(fresh) not in (int, float) or not 0 <= fresh <= 100:
            raise BadInput("fresh ngoài miền")
        seen.add(ident)
    return [dict(i) for i in items]


def age_items(items, decay_units, threshold, location, events):
    # 240 units per point makes both standard tick decrements integral.
    for i in sort_by_id(items):
        before = i["fresh"]
        units = before * 240
        nearest = round(units)
        if before == nearest / 240:
            units = nearest
        i["fresh"] = max(0, units - decay_units) / 240
        if i["fresh"] < threshold <= before:
            events.append(("spoiled", {"item_id": i["id"], "kind": i["kind"], "location": location}))


def read_inventory(path: str, kinds=KINDS, version="1.1"):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if version == "1.2":
        return validate_individuals(data["items"])
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items: dict):
    items = sort_by_id(items) if isinstance(items, list) else {k: items[k] for k in sorted(items) if items[k] > 0}
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
