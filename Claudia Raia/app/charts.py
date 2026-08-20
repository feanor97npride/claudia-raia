from datetime import date, datetime, timedelta

COLORS = {"green": "#1e9e5a", "amber": "#c98a05", "red": "#d43f3f"}
STATUS_LABELS = {"green": "Verde", "amber": "Amarelo", "red": "Vermelho"}


def build_daily_status_counts(items, days=30):
    """For a list of Item objects, reconstruct daily RAG counts for the last `days` days
    by replaying each item's status history."""
    # history timestamps are stored via datetime.utcnow(), so anchor "today" to UTC too
    # to avoid an off-by-one day near local midnight.
    end = datetime.utcnow().date()
    start = end - timedelta(days=days - 1)
    date_range = [start + timedelta(days=i) for i in range(days)]

    per_item_events = []
    for it in items:
        events = sorted(it.history, key=lambda h: h.changed_at)
        if not events:
            continue
        per_item_events.append(events)

    series = []
    for d in date_range:
        counts = {"green": 0, "amber": 0, "red": 0}
        for events in per_item_events:
            current_status = None
            for ev in events:
                if ev.changed_at.date() <= d:
                    current_status = ev.status
                else:
                    break
            if current_status:
                counts[current_status] += 1
        series.append({"date": d, **counts})
    return series


def render_trend_svg(series, width=760, height=230, title=None):
    if not series or all(p["green"] + p["amber"] + p["red"] == 0 for p in series):
        return (
            f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
            f'<text x="{width/2}" y="{height/2}" text-anchor="middle" '
            f'font-size="13" fill="#98a2b3" font-family="Segoe UI, sans-serif">'
            f'Sem histórico suficiente para exibir tendência.</text></svg>'
        )

    pad_l, pad_r, pad_t, pad_b = 42, 16, 18, 30
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    max_y = max(p["green"] + p["amber"] + p["red"] for p in series)
    max_y = max(max_y, 1)
    # round up to a friendly step
    step = max(1, round(max_y / 4))
    max_y = step * 4 if step * 4 >= max_y else step * 5

    n = len(series)

    def x_at(i):
        if n == 1:
            return pad_l + plot_w / 2
        return pad_l + (plot_w * i / (n - 1))

    def y_at(v):
        return pad_t + plot_h - (plot_h * v / max_y)

    svg = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, Arial, sans-serif">']

    # gridlines + y labels
    for g in range(0, 5):
        val = round(max_y * g / 4)
        y = y_at(val)
        svg.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}" stroke="#e3e7ed" stroke-width="1"/>')
        svg.append(f'<text x="{pad_l - 8}" y="{y+4:.1f}" text-anchor="end" font-size="10.5" fill="#8a93a6">{val}</text>')

    # x labels: first, middle, last
    label_idx = sorted(set([0, n // 2, n - 1]))
    for i in label_idx:
        d = series[i]["date"]
        svg.append(
            f'<text x="{x_at(i):.1f}" y="{height - 8}" text-anchor="middle" font-size="10.5" fill="#8a93a6">{d.strftime("%d/%m")}</text>'
        )

    # lines per status
    for key in ("green", "amber", "red"):
        points = " ".join(f"{x_at(i):.1f},{y_at(p[key]):.1f}" for i, p in enumerate(series))
        svg.append(f'<polyline points="{points}" fill="none" stroke="{COLORS[key]}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')
        last = series[-1]
        svg.append(f'<circle cx="{x_at(n-1):.1f}" cy="{y_at(last[key]):.1f}" r="3.5" fill="{COLORS[key]}"/>')

    # legend
    lx = pad_l
    ly = 12
    for key in ("green", "amber", "red"):
        svg.append(f'<circle cx="{lx}" cy="{ly}" r="4" fill="{COLORS[key]}"/>')
        svg.append(f'<text x="{lx+8}" y="{ly+4}" font-size="11" fill="#4b5468">{STATUS_LABELS[key]}</text>')
        lx += 78

    svg.append("</svg>")
    return "".join(svg)


def render_status_bar_svg(item, width=720, height=46):
    """Horizontal timeline bar showing status segments from creation to now."""
    events = sorted(item.history, key=lambda h: h.changed_at)
    if not events:
        return ""

    start = events[0].changed_at
    end_dt = events[-1].changed_at
    from datetime import datetime
    now = datetime.utcnow()
    total = max((now - start).total_seconds(), 1)

    segments = []
    for i, ev in enumerate(events):
        seg_start = ev.changed_at
        seg_end = events[i + 1].changed_at if i + 1 < len(events) else now
        frac_start = (seg_start - start).total_seconds() / total
        frac_end = (seg_end - start).total_seconds() / total
        segments.append((frac_start, frac_end, ev.status))

    bar_h = 22
    bar_y = 6
    svg = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, Arial, sans-serif">']
    svg.append(f'<rect x="0" y="{bar_y}" width="{width}" height="{bar_h}" rx="6" fill="#f0f2f5"/>')
    for frac_start, frac_end, status in segments:
        x = frac_start * width
        w = max((frac_end - frac_start) * width, 1)
        svg.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{w:.1f}" height="{bar_h}" fill="{COLORS[status]}"/>')
    svg.append(f'<rect x="0" y="{bar_y}" width="{width}" height="{bar_h}" rx="6" fill="none" stroke="#d7dbe3" stroke-width="1"/>')
    svg.append(f'<text x="0" y="{bar_y + bar_h + 16}" font-size="10.5" fill="#8a93a6">{start.strftime("%d/%m/%Y")}</text>')
    svg.append(f'<text x="{width}" y="{bar_y + bar_h + 16}" text-anchor="end" font-size="10.5" fill="#8a93a6">hoje</text>')
    svg.append("</svg>")
    return "".join(svg)
