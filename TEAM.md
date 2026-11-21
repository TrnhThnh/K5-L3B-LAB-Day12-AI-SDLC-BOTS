# TEAM

**Tên nhóm:** BOTS  **Số người:** 2  (khớp `team_size` trong `game.contract.json`; đề yêu cầu 4–6, xem `docs/clarify.md` #1)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Dương Minh Chiến | duongchien147 | `sim/gather` + `client/ui` | PO + Integrator | Trịnh Hưng Thịnh (`sim/quan`) |
| Trịnh Hưng Thịnh | TrnhThnh | `sim/quan` + `qa` | QA lead + Scrum/Release | Dương Minh Chiến (`sim/gather`) |

Việc chính của mỗi người:
- Chiến: luật buổi sáng `gather` (oxy, Máu, hái, bắt cá, giỏ) và cửa sổ chơi thử. Giữ hợp đồng `docs/contracts/`, giữ `docs/clarify.md`, hỏi giảng viên, gắn tag các phase.
- Thịnh: luật buổi tối `quan` (khách, bếp, phục vụ, tiền, uy tín) và test của quán. Đọc lại code `gather`, lưu bằng chứng, viết `docs/verification/`, ghi standup, tạo Release `v1.0.0`.
- Phase 2–4: phần đề mới thuộc buổi sáng hoặc giao diện thì Chiến nhận, thuộc buổi tối hoặc QA thì Thịnh nhận.

Checklist chi tiết từng việc: [`docs/plan/phan-cong.md`](docs/plan/phan-cong.md).

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: nhóm chat riêng của hai người; việc gì cần quyết thì nói ngay ở đó.
- Khi bất đồng về thiết kế: mỗi người nói 2 phút. Chưa thống nhất được thì Integrator (Chiến) quyết và ghi lý do vào `docs/clarify.md`.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trong kênh, người dự phòng vào giúp hoặc nhận luôn phần đó.
- Giờ standup giữa phase: giữa mỗi phase, mỗi người ghi một dòng vào `docs/standup.md`.
- Cách đọc code của nhau: Thịnh đọc và chạy test phần `gather`, Chiến đọc phần `quan` trước khi gắn tag.
- Cách làm việc với Git: push thẳng `main`, commit nhỏ, `git pull --rebase` trước khi push, chạy test trước khi push. Mỗi người chỉ sửa file module của mình; file chung (`game.contract.json`, `docs/contracts/`, `AGENTS.md`) do Chiến sửa. Chiến gắn tag.
