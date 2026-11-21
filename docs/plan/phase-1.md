# Kế hoạch Phase 1 (≤ 1 trang)

- Mục tiêu: chạy được hai buổi `gather` và `quan` theo PRD-0 ở chế độ headless. Kho đi từ `gather` sang `quan`, cùng seed thì ra cùng byte. Gắn tag `phase-1` trước mốc 1:00.
- Việc / người / phụ thuộc (checklist chi tiết: [phan-cong.md](phan-cong.md)):

| Việc | Người | Phụ thuộc |
|---|---|---|
| Kickoff: `TEAM.md`, `team_size`, hợp đồng `docs/contracts/`, clarify nhóm 2 người | Chiến | — |
| Lát 1 gather: oxy, ngạt, Máu, ngất, dive/surface, giỏ LIFO | Chiến | hợp đồng sự kiện |
| Lát 2 gather: hái nút, bắt cá, `hold_full`, regrow | Chiến | lát 1 |
| Lát 3 quan: khách đến, chọn món, giữ chỗ, kiên nhẫn, bỏ đi | Thịnh | schema kho |
| Lát 4 quan: bếp, bưng, phục vụ, trả tiền, boa, uy tín, `quan_end` | Thịnh | lát 3 |
| Test hộp đen cho từng lát | người làm lát đó; người kia đọc lại | lát tương ứng |
| Ghép, chạy toàn bộ test, `verification/phase-1.md`, gắn tag | Thịnh (proof) + Chiến (tag) | tất cả |

- Rủi ro:
  - Nhóm chỉ có 2 người, mỗi người ôm 2 module. Bù lại bằng cách làm phần lõi trước, phần UI và sáng tạo để sau.
  - PRD-0 chưa có trong repo nên một số luật phải tự giả định. Mỗi giả định ghi vào `docs/clarify.md` để hỏi lại PO.
  - Máy Windows không có lệnh `python3` nên test hộp đen lỗi. Cách chạy ghi trong `AGENTS.md`.
