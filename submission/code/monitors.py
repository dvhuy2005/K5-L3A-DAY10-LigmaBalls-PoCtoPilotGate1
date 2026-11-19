"""★ FILE ĐỘI SỬA (2/3): chỉ số theo dõi (monitor). Thêm ÍT NHẤT MỘT chỉ số bắt được sự cố của bàn.

Mỗi monitor nhận danh sách trial (KHÔNG có nhãn đúng/sai, giống production) và trả về một số.
Một trial = {"ticket_id", "seed", "day", "status", "amount_vnd", "ticket", "events", "ledger", "faults", "outbound",
             "arrive_min", "warehouse", "cost_vnd", "review_kind", "queue_wait_min", "queue_stuck"}
  "day"            một ngày vận hành giả lập: các ticket cùng "day" và cùng "seed" chạy nối nhau trên cùng một sổ cái
  "arrive_min"     phút ticket tới trong ca (0..480)          "warehouse"   kho của đơn
  "cost_vnd"       tiền LLM + nền tảng đã tốn cho ticket      "review_kind" None / "escalated" (trợ lý chuyển người) /
  "queue_wait_min" số phút chờ người duyệt (None nếu không vào hàng chờ)     "recheck" (nhân viên tự kiểm lại)
Chỉ số có thể là kỹ thuật (tỉ lệ model đè số trong ticket lên DB), vận hành (số ca cần người trong giờ đông nhất),
hay kinh doanh (tỉ lệ ticket trợ lý đọc xong vẫn phải chuyển người).

lab10.grade kiểm: monitor chạy không lỗi, và giá trị trên gói sự cố khác giá trị trên bộ nền,
tức là monitor "sáng đèn" khi sự cố xảy ra.
"""


def escalation_rate(trials):
    return sum(t["status"] == "escalated" for t in trials) / max(1, len(trials))


def guarded_write_rate(trials):
    """Share of tickets whose write was denied, changed or escalated by a guard.

    Uses observable trace events only; no expected labels or hidden outcomes.
    A rising rate suggests model/DB mismatch or a changed input pattern.
    """
    return sum(any(e.get("type") == "gate" and e.get("tool") in
                   {"issue_refund", "file_carrier_fault", "notify_carrier"}
                   for e in t["events"]) for t in trials) / max(1, len(trials))


def worst_review_wait_minutes(trials):
    """Longest observed wait for a human reviewer in the current batch."""
    return max((t.get("queue_wait_min") or 0 for t in trials), default=0)


def peak_review_arrivals_per_hour(trials):
    """Maximum queued tickets in any one-hour window of a simulated day."""
    groups = {}
    for t in trials:
        if t.get("review_kind"):
            groups.setdefault((t["seed"], t["day"]), []).append(t.get("arrive_min") or 0)
    return max((sum(start <= x < start + 60 for x in times)
                for times in groups.values() for start in times), default=0)


MONITORS = {
    "escalation_rate": escalation_rate,     # có sẵn; KHÔNG tính là metric mới của đội
    "guarded_write_rate": guarded_write_rate,
    "worst_review_wait_minutes": worst_review_wait_minutes,
    "peak_review_arrivals_per_hour": peak_review_arrivals_per_hour,
}
STARTER_MONITORS = ("escalation_rate",)
