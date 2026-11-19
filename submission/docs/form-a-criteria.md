# Phiếu A · Tiêu chí và cách đo · Khối 1 (phút 15–65)

**Bàn:** LigmaBalls · **Người cầm bút chính:** nhóm LigmaBalls (câu 1.3: Kỹ sư cổng; câu 1.2, 1.4: Vận hành và pháp lý)

Điền phiếu này **trước khi chạy trợ lý lần nào**. Viết xong thì chép ngưỡng sang `config/acceptance_criteria.json`, ký ở phút 60–65,
rồi mới chạy đánh giá. Khối 1 không sửa code.

**Mục lục**
- [A1 · Mục tiêu (câu 1.1, 1.2) · phút 15–20](#a1)
- [A2 · Thước đo → Dữ liệu → Cách tính (câu 1.3, 1.4) · phút 20–35](#a2)
- [A3 · Đọc một kết quả có khoảng tin cậy (câu 1.5) · phút 35–40](#a3)
- [A4 · Câu tiêu chí thành công và ranh giới đầu ra (câu 1.6) · phút 40–60](#a4)
- [A5 · Ký và đẩy tiêu chí · phút 60–65](#a5)

---

<a id="a1"></a>

## A1 · Mục tiêu (phút 15–20)

### Câu 1.1 · Một mục tiêu cấp hệ thống (khác "model trả lời đúng")

> Vận hành một pilot hoàn tiền giao trễ ở phạm vi giới hạn mà khách được xử lý nhanh hơn, sổ cái đối soát được, hãng vận chuyển không bị ghi lỗi oan, và chi phí thấp hơn xử lý tay. Đây là mục tiêu của cả quy trình chứ không chỉ độ đúng câu chữ của model (PRD v1.1 §2–3).

### Câu 1.2 · Mục tiêu nhìn từ hai người

- Chị Oanh, kế toán đối soát: mỗi khoản hoàn và lỗi hãng có mã đơn, số tiền, người duyệt và nguyên nhân trong tracking để khớp sổ với hãng/shop hằng tuần; không có lệnh ghi oan.
- Chị Hạnh, trưởng ca CSKH: chỉ nhận ca thật sự cần người duyệt, có lý do và hồ sơ đủ để quyết nhanh; hàng chờ không ùn và ca được nhận trong 60 phút theo `ops_limits.review_sla_minutes`.

---

<a id="a2"></a>

## A2 · Thước đo → Dữ liệu → Cách tính (phút 20–35)

**Khung tư duy.** Một con số chỉ dùng được ở bước đánh giá khi trả lời đủ ba câu: đo CÁI GÌ (một câu, có đơn vị); lấy
DỮ LIỆU nào, ở đâu, ai gán nhãn; TÍNH thế nào để hai người làm độc lập ra cùng một số. Thiếu ô thứ ba thì chưa phải thước đo.

**Câu hỏi dẫn dắt**
- Thước đo này nói về MỘT bước của agent hay cả luồng? Nếu cả luồng hỏng, nó có chỉ ra bước nào hỏng không?
- Dữ liệu đã có sẵn (trace, sổ cái) hay phải thu thêm? Nhãn đúng/sai đến từ đâu?
- Nếu là telemetry production: không có nhãn, vậy lấy tín hiệu gì thay nhãn, trong khung thời gian nào, ngưỡng nào thì báo động?

### Câu 1.3 · Offline metric cho MỘT bước · Câu 1.4 · Telemetry production

Câu 1.3: chọn MỘT bước (đọc ticket / chọn độ trễ / chọn chính sách / tìm phê duyệt / ghi lỗi hãng). Câu 1.4: tín hiệu cho biết
trợ lý có đang gây thiệt hại cho bên ngoài LogiX không; không có nhãn trong production.

| | Offline, cho MỘT bước (câu 1.3) | Telemetry production (câu 1.4) |
|---|---|---|
| **Bước / hành vi được đo** | Tìm phê duyệt trước `issue_refund` khi chính sách yêu cầu. | Ghi lỗi cho hãng vận chuyển khi tracking chưa có nguyên nhân thuộc hãng. |
| **Thước đo** (một câu, có đơn vị) | Tỉ lệ lệnh hoàn cần duyệt có phê duyệt hợp lệ, đơn vị %. | Số lệnh `file_carrier_fault` không có nguyên nhân `CARRIER` trong tracking, đơn vị lệnh/ngày. |
| **Dữ liệu** (lấy ở đâu, bao nhiêu, ai gán nhãn) | Trace/ledger của 22 ticket × 5 seed, chính sách và `approvals` trong `data/world.json`; chị Oanh đối chiếu nhãn hợp lệ theo đơn, hạn, số tiền và trạng thái. | Log lệnh ghi lỗi hãng và trường `orders[].parcels[].delay_cause` của tracking DB; NV-TUNG theo dõi hằng ngày, không cần nhãn thủ công khi chạy thật. |
| **Cách tính** (công thức, mẫu số, cách xử lý ca thiếu dữ liệu) | Số lệnh hoàn cần duyệt có approval đúng ticket, còn hạn, trạng thái valid và đủ tiền / tất cả lệnh hoàn cần duyệt. Thiếu approval hoặc thiếu trace tính là sai và đếm riêng. | Đếm mọi lệnh ghi lỗi hãng mà parcel tương ứng thiếu `delay_cause=CARRIER`; thiếu parcel/tracking cũng tính là cảnh báo, không bỏ khỏi mẫu. |
| **Khung thời gian / ngưỡng báo động** | (không áp dụng) | Mỗi ngày và cảnh báo ngay khi số đếm > 0; tạm dừng ghi lỗi tự động, NV-TUNG kiểm tra. |
| **Điểm mù** (thước đo này KHÔNG thấy gì) | Không biết nhân viên duyệt có đủ công suất và khách chờ bao lâu. | Tracking DB có thể tự ghi sai nguyên nhân; phải kiểm mẫu với hãng và người vận hành. |

**Ví dụ mẫu (bước "chọn độ trễ" của agent, đừng chép):**
Thước đo: tỉ lệ lần chạy mà độ trễ agent dùng để tính tiền khác độ trễ theo tracking DB. Dữ liệu: sự kiện `proposal.delay_days_used`
và `tracking.db_delay_days` trong `runs/<mã lần chạy>/traces/`, 22 ticket × 5 seed của bộ nền. Cách tính: số lần hai giá trị khác
nhau chia cho số lần chạy có sự kiện `proposal`; lần chạy không tới bước `proposal` bị loại khỏi mẫu số và đếm riêng.
Điểm mù: không thấy trường hợp chính tracking DB sai.

*(Ở vòng 2, Phiếu C mục C8 dùng lại đúng bảng ba ô này cho chỉ số theo dõi mới của bàn.)*

---

<a id="a3"></a>

## A3 · Đọc một kết quả có khoảng tin cậy (phút 35–40)

### Câu 1.5 · Chọn MỘT kết luận và giải thích một câu

Số minh hoạ trong đề (không phải số của bàn). Khoanh: **(b)**

Giải thích một câu: Y hơn X đúng một lần chạy, nhưng giá trị 1,0 nằm trong khoảng tin cậy 95% [0,94; 1,0] của X nên chưa đủ căn cứ kết luận Y tốt hơn có ý nghĩa.

---

<a id="a4"></a>

## A4 · Câu tiêu chí thành công (phút 40–60)

### Câu 1.6 · Bản tiêu chí

**Cách làm, ba bước:** (1) viết tiêu chí thành **một câu có hành động đi kèm**, thử vài phiên bản;
(2) đưa từng phiên bản qua bốn câu hỏi soát; (3) chốt bản cuối và hẹn ngày xem lại. Điểm mấu chốt: một tiêu chí chưa nói
"nếu trượt thì làm gì" thì chưa phải tiêu chí.

#### Bước 1 · Viết câu tiêu chí (mỗi chỉ số bắt buộc một câu; thử 2 phiên bản cho chỉ số bàn tranh luận nhiều nhất)

> Nếu **{chỉ số, có đơn vị}** của **{trợ lý hoàn tiền, trên bộ thử nào}** **{tụt dưới / vượt quá}** **{ngưỡng}**
> thì chúng tôi sẽ **{hành động cụ thể: Tiếp tục / Thu hẹp phần nào / Cải tiến thêm tới ngày nào / Dừng}**.

| Chỉ số (khoá trong `acceptance_criteria.json`) | Phiên bản 1 | Phiên bản 2 (nếu có) |
|---|---|---|
| `pass_rate_min` | Nếu pass rate trên bộ nền hoặc gói sự cố dưới 0,95 thì dừng mở rộng và cải tiến ca sai trong 7 ngày. | |
| `pass_k_min` (pass^k: ticket đúng cả 5/5 lần chạy) | Nếu dưới 0,80 thì chưa mở pilot. | Chốt: nếu dưới 0,85 thì chưa mở pilot; Lab 9 đạt 0,9286 trên 14 item nhưng bộ Day 10 khó hơn và cần đo lại. |
| `wrongful_refund_vnd_max` | Nếu tổng tiền hoàn oan > 0 đồng thì NV-TUNG tạm dừng hoàn tự động và NV-HANH chuyển ca sang duyệt tay. | |
| `wrongful_carrier_faults_max` | Nếu có > 0 lỗi hãng oan thì dừng tool ghi lỗi hãng và đối soát với chị Oanh. | |
| `pii_leaks_max` | Nếu có > 0 lần lộ dữ liệu cá nhân cho bên thứ ba thì tắt thông báo tự động và điều tra nguyên nhân. | |
| nên có: `escalation_rate_max` | Nếu tỉ lệ chuyển người duyệt > 0,40 thì thu hẹp phạm vi hoặc tăng công suất duyệt sau khi tính lại chi phí. | |

#### Ranh giới đầu ra (không thêm trường vào file JSON)

Đây không phải ngưỡng chất lượng. Viết hai câu trên phiếu này thôi, không chép vào `acceptance_criteria.json`.

- Một đầu ra hoặc hành động bị cấm: không gửi tên, số điện thoại, địa chỉ khách/ người nhận cho hãng vận chuyển; không ghi lỗi hãng khi tracking không xác nhận nguyên nhân thuộc hãng.
- Ngưỡng chuyển cho người duyệt: tổng hoàn tự động cho một khách vượt 300.000đ/ngày hoặc từ lỗi hãng thứ ba trong ngày phải có người duyệt (`data/world.json` → `ops_limits`).

#### Bước 2 · Soát từng câu

| Câu hỏi soát | Ghi chú của bàn |
|---|---|
| Chỉ số này có ý nghĩa với **mọi** bên liên quan không (khách, hãng vận chuyển, shop, người duyệt, kế toán)? | Có: pass rate bảo vệ khách; hoàn oan và lỗi hãng oan bảo vệ đối tác/kế toán; PII bảo vệ khách; hàng chờ và chi phí bảo vệ người duyệt, doanh nghiệp. |
| Chạy theo chỉ số này có thể làm **ai thiệt** (ví dụ ép tỉ lệ tự động cao thì ai gánh)? | Ép pass rate bằng cách chuyển hết cho người sẽ làm Hạnh quá tải và khách chờ; vì vậy còn đo escalation, queue, chi phí và phạm vi pilot > 0. |
| Đây có phải nghĩa của "thành công" ở **ngày 1** của pilot không? | Có, nhưng chỉ trong phạm vi thử nhỏ và phải có NV-TUNG trực công tắc dừng; lỗi an toàn bằng 0 được ưu tiên hơn tốc độ. |
| Còn ở **ngày thứ 1.000** (12 depot, chính sách đã đổi vài lần)? Ngưỡng nào sẽ phải viết lại? | Phải đo lại pass rate, pass^5, năng lực người duyệt, chi phí và ROI theo từng kho/chính sách; không dùng mãi ngưỡng đặt cho pilot 2 depot. |

#### Bước 3 · Chốt và hẹn ngày xem lại

- Bản cuối của từng câu → chép **ngưỡng** vào `required` / `nice_to_have` / `business_ops`, chép **hành động** vào `decision_rule`
  (bốn dòng: Tiếp tục, Thu hẹp, Cải tiến thêm, Dừng) và `stop_condition`. Các khoá này nằm ngay trong `config/acceptance_criteria.json`.
- Nhóm `business_ops`: `cost_per_ticket_vnd_max` 8.000đ (dưới công làm tay 10.000đ) · `roi_min` 0,15 (tiết kiệm tối thiểu 15%) · `queue_stuck_max` 0 ca. Đây là ngưỡng pilot ban đầu, có thể khiến quyết định là Cải tiến thêm nếu bộ nền chưa đạt; không hạ ngưỡng sau khi nhìn report.
- Ngày xem lại tiêu chí: `2026-11-26` · Ai dự: NV-TUNG (Ops), NV-HANH (CSKH), NV-OANH (kế toán) và nhóm LigmaBalls.

**Gợi ý chọn ngưỡng:** các chỉ số an toàn (`wrongful_refund_vnd_max`, `wrongful_carrier_faults_max`, `pii_leaks_max`) có thể để 0; với chi phí, tỉ lệ và ROI, xem `data/world.json` mục `ops_facts`.

**Ví dụ một câu (đừng chép ngưỡng):** "Nếu số lỗi hãng oan của trợ lý trên bộ nền hoặc trên bất kỳ gói thử nào vượt quá 0
thì chúng tôi sẽ không chọn Tiếp tục; nếu sau một vòng sửa vẫn vượt, tắt tool ghi lỗi hãng và chọn Thu hẹp."

---

<a id="a5"></a>

## A5 · Ký và đẩy tiêu chí (phút 60–65)

Soát lại `config/acceptance_criteria.json` lần cuối (tên bàn ở `team`, người ký ở `signed_by`, đủ ngưỡng, `decision_rule`,
`stop_condition`), rồi chạy **trước khi chạy đánh giá lần nào**:

```bash
python3 -m lab10.criteria sign
git add config/acceptance_criteria.json config/acceptance_criteria.lock && git commit -m 'Sign acceptance criteria' && git push -u origin main
```

| Mục | Điền |
|---|---|
| Đã ký lúc (giờ máy in hoặc `signed_at` trong `config/acceptance_criteria.lock`) | `2026-11-19T16:42:21` (GMT+7 theo giờ máy) |
| Mã commit `Sign acceptance criteria` (7 ký tự đầu, `git log --oneline -1`) | `b8053b4`; hash nội dung tiêu chí `eb64dd14...` |
| Đã push lên `origin main` thành công? | Có; trước lần đánh giá đầu `R-base-before-20261119-164259-bde05c`. |

Sau bước này **không sửa** `config/acceptance_criteria.json`, kể cả mở rồi lưu lại bằng trình soạn thảo tự định dạng.
