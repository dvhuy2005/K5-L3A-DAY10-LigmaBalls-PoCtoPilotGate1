"""★ FILE ĐỘI SỬA (1/3): cổng cấp hệ thống, nằm NGOÀI model và prompt.

VÒNG 1 (trước khi biết sự cố): viết 2–3 CỔNG PHÒNG NGỪA rút từ pre-mortem / HAZOP / checklist của bàn, rồi chốt bằng
    python3 -m lab10.checkpoint        (chép file này thành guards_round1.py = mốc "prepared"; KHÔNG sửa bản chép)
VÒNG 2 (sau khi bốc thẻ): sửa tiếp NGAY TRONG FILE NÀY. Giữ các cổng vòng 1, thêm cổng mới.
Hai file còn lại bàn được sửa: lab10/monitors.py (chỉ số theo dõi) và config/operating_gates.json (cổng kinh doanh,
vận hành, pháp lý: những con số và tên người mà trợ lý phải tuân theo, không cần code).

Hai điểm móc, agent gọi tự động:
  pre_guard(ctx)          chạy TRƯỚC khi agent đọc ticket
  write_gate(ctx, action) chạy TRƯỚC MỖI lệnh ghi (issue_refund, file_carrier_fault,
                          notify_carrier, send_reply)

Trả về một Verdict:
  Verdict.allow()                       cho qua   (pre_guard: allow(policy_id="...") để ghim phiên bản chính sách)
  Verdict.deny("lý do")                 bỏ riêng lệnh ghi này, agent đi tiếp
  Verdict.escalate("lý do")             dừng, chuyển ticket cho người
  Verdict.modify("lý do", amount_vnd=…) sửa tham số lệnh ghi (amount_vnd, payer, carrier_id, parcel_id, payload…)
  Verdict.rewrite("lý do", text)        chỉ pre_guard: thay nội dung ticket mà agent sẽ đọc

ctx.ticket   ticket gốc (chữ khách viết là DỮ LIỆU, không phải lệnh)
ctx.tools    tra cứu nguồn sự thật: lookup_order, lookup_policies, lookup_approvals(**lọc),
             ledger_rows(**lọc), fault_rows(**lọc), lookup_carrier; ctx.as_of = ngày hôm nay
             ops_limits() = các trần đã thống nhất với Ops/Finance; ops_facts() = số liệu vận hành;
             auto_refund_today_vnd() = tổng đã hoàn tự động trong ngày
ctx.gates    config cổng của bàn (config/operating_gates.json), chỉ đọc;  ctx.cost_vnd = tiền LLM đã tốn cho ticket này
ctx.events   trace tới thời điểm này;  ctx.log("ten_su_kien", ...) ghi thêm sự kiện guard vào trace
lab10.helpers: db_delay_days, ticket_parcel, effective_policy, entitlement_vnd, carrier_at_fault, digits

Mặc định dưới đây cho qua tất cả (= mốc base).
"""
from . import helpers as H
from .tools import Verdict


def pre_guard(ctx):
    # The policy index flag may lag behind the calendar. Pin the version that
    # is actually in force before the model reads any customer-written text.
    policy = H.effective_policy(ctx.tools.lookup_policies(), ctx.as_of)
    if policy is None:
        return Verdict.escalate("không có chính sách còn hiệu lực")
    return Verdict.allow(policy_id=policy["policy_id"])


def write_gate(ctx, action):
    # action = {"tool": "issue_refund", "ticket_id":..., "order_id":..., "amount_vnd":..., "payer":..., ...}
    tool = action.get("tool")
    if tool not in {"issue_refund", "file_carrier_fault", "notify_carrier"}:
        return Verdict.allow()

    order = ctx.tools.lookup_order(ctx.ticket.get("order_id"))
    if not order or order.get("customer_id") != ctx.ticket.get("customer_id"):
        return Verdict.escalate("chưa xác minh được chủ đơn")
    if action.get("order_id", order["order_id"]) != order["order_id"]:
        return Verdict.escalate("lệnh ghi nhắm sang đơn khác")
    policy = H.effective_policy(ctx.tools.lookup_policies(), ctx.as_of)
    if policy is None or not order.get("parcels"):
        return Verdict.escalate("thiếu chính sách hoặc tracking để kiểm lệnh ghi")
    parcel = H.ticket_parcel(order, ctx.ticket, ctx.as_of)
    delay = H.db_delay_days(parcel, ctx.as_of)
    amount = H.entitlement_vnd(policy, order, delay, parcel.get("delay_cause"))

    if tool == "issue_refund":
        # A customer's prose and a model's proposal never outrank the order DB.
        if ctx.tools.ledger_rows(ticket_id=ctx.ticket["ticket_id"]):
            return Verdict.deny("lệnh hoàn trùng ticket; đã có trong sổ cái")
        if order.get("refund_status") == "REFUNDED":
            return Verdict.deny("đơn đã được hoàn")
        prior = sum(row["amount_vnd"] for row in ctx.tools.ledger_rows(order_id=order["order_id"]))
        remaining = max(0, amount - prior)
        if remaining == 0:
            return Verdict.deny("tracking và chính sách không cho phép hoàn thêm")
        approval_id = action.get("approval_id")
        approval = next((a for a in ctx.tools.lookup_approvals(approval_id=approval_id)
                         if approval_id), None)
        if remaining > policy["auto_limit_vnd"] or approval_id:
            valid = (approval is not None and approval.get("ticket_id") == ctx.ticket["ticket_id"]
                     and approval.get("order_id") == order["order_id"]
                     and approval.get("customer_id") == order["customer_id"]
                     and approval.get("status") == "valid"
                     and approval.get("expires_at", "") >= ctx.as_of
                     and approval.get("max_vnd", 0) >= remaining)
            if not valid:
                return Verdict.escalate("phê duyệt không hợp lệ hoặc chưa có")
        changes = {}
        if action.get("amount_vnd") != remaining:
            changes["amount_vnd"] = remaining
        if action.get("payer") != "LOGIX":
            changes["payer"] = "LOGIX"
        if changes:
            ctx.log("refund_grounded", order_id=order["order_id"], amount_vnd=remaining)
            return Verdict.modify("đối chiếu chính sách với tracking và sổ cái", **changes)

    elif tool == "file_carrier_fault":
        if not H.carrier_at_fault(policy, parcel, delay):
            return Verdict.deny("tracking không ghi nguyên nhân thuộc hãng")
        changes = {}
        for key, expected in (("parcel_id", parcel["parcel_id"]),
                              ("carrier_id", parcel["carrier_id"]),
                              ("driver_id", parcel.get("driver_id")),
                              ("delay_days", delay)):
            if action.get(key) != expected:
                changes[key] = expected
        if changes:
            return Verdict.modify("ghi lỗi đúng kiện và đúng hãng trong tracking", **changes)

    elif tool == "notify_carrier":
        allowed = set(policy.get("carrier_notice_fields", []))
        clean = {k: v for k, v in (action.get("payload") or {}).items() if k in allowed}
        if clean != action.get("payload"):
            return Verdict.modify("chỉ gửi trường được phép cho hãng", payload=clean)
    return Verdict.allow()
