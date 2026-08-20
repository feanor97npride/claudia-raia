import os
import sys
from datetime import datetime, date

from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_file
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import charts
import exports

IS_SERVERLESS = bool(os.environ.get("VERCEL"))
DB_DIR = "/tmp" if IS_SERVERLESS else BASE_DIR

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(DB_DIR, 'rag_tracker.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "dev-rag-tracker-secret"

db = SQLAlchemy(app)

STATUSES = ["green", "amber", "red"]

ENTITY_TYPES = {
    "projects": {
        "singular": "Projeto",
        "plural": "Projetos",
        "icon": "🗂️",
        "category_label": "Fase",
        "category_options": ["Planejamento", "Execução", "Homologação", "Implantação", "Encerrado"],
        "metric_label_default": "Progresso (%)",
        "has_due_date": True,
    },
    "systems": {
        "singular": "Sistema",
        "plural": "Sistemas / Aplicações",
        "icon": "🖥️",
        "category_label": "Criticidade",
        "category_options": ["Crítica", "Alta", "Média", "Baixa"],
        "metric_label_default": "Uptime (%)",
        "has_due_date": False,
    },
    "kpis": {
        "singular": "KPI",
        "plural": "KPIs / Métricas",
        "icon": "📊",
        "category_label": "Categoria",
        "category_options": ["Disponibilidade", "Performance", "Capacidade", "Segurança", "Atendimento"],
        "metric_label_default": "Valor",
        "has_due_date": False,
    },
    "risks": {
        "singular": "Risco",
        "plural": "Riscos / Issues",
        "icon": "⚠️",
        "category_label": "Severidade",
        "category_options": ["Crítica", "Alta", "Média", "Baixa"],
        "metric_label_default": "Exposição",
        "has_due_date": True,
    },
}


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(20), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    owner = db.Column(db.String(120), default="")
    category = db.Column(db.String(80), default="")
    status = db.Column(db.String(10), nullable=False, default="green")
    due_date = db.Column(db.Date, nullable=True)
    metric_label = db.Column(db.String(80), default="")
    metric_value = db.Column(db.Float, nullable=True)
    metric_target = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    history = db.relationship(
        "StatusHistory", backref="item", cascade="all, delete-orphan",
        order_by="desc(StatusHistory.changed_at)"
    )

    @property
    def meta(self):
        return ENTITY_TYPES[self.entity_type]

    @property
    def is_overdue(self):
        return bool(self.due_date and self.due_date < date.today() and self.status != "green")


class StatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    note = db.Column(db.Text, default="")
    changed_by = db.Column(db.String(120), default="")
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)


def get_meta_or_404(entity_type):
    if entity_type not in ENTITY_TYPES:
        abort(404)
    return ENTITY_TYPES[entity_type]


def parse_float(value):
    value = (value or "").strip().replace(",", ".")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_date(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


@app.context_processor
def inject_globals():
    return {"ENTITY_TYPES": ENTITY_TYPES, "STATUSES": STATUSES}


@app.route("/")
def dashboard():
    items = Item.query.all()
    summary = {}
    for et in ENTITY_TYPES:
        counts = {s: 0 for s in STATUSES}
        for it in items:
            if it.entity_type == et:
                counts[it.status] += 1
        summary[et] = counts

    total_counts = {s: sum(summary[et][s] for et in ENTITY_TYPES) for s in STATUSES}

    red_items = sorted(
        [i for i in items if i.status == "red"], key=lambda i: i.updated_at, reverse=True
    )
    amber_items = sorted(
        [i for i in items if i.status == "amber"], key=lambda i: i.updated_at, reverse=True
    )

    recent_history = (
        StatusHistory.query.order_by(StatusHistory.changed_at.desc()).limit(15).all()
    )

    trend_days = 30
    trend_series = charts.build_daily_status_counts(items, days=trend_days)
    trend_svg = charts.render_trend_svg(trend_series)

    return render_template(
        "dashboard.html",
        summary=summary,
        total_counts=total_counts,
        red_items=red_items,
        amber_items=amber_items,
        recent_history=recent_history,
        total_items=len(items),
        trend_svg=trend_svg,
        trend_days=trend_days,
    )


@app.route("/<entity_type>")
def list_items(entity_type):
    meta = get_meta_or_404(entity_type)
    status_filter = request.args.get("status")
    query = Item.query.filter_by(entity_type=entity_type)
    if status_filter in STATUSES:
        query = query.filter_by(status=status_filter)
    items = query.order_by(
        db.case((Item.status == "red", 0), (Item.status == "amber", 1), else_=2),
        Item.name,
    ).all()

    all_of_type = Item.query.filter_by(entity_type=entity_type).all()
    trend_svg = charts.render_trend_svg(charts.build_daily_status_counts(all_of_type, days=30))

    return render_template(
        "list.html", entity_type=entity_type, meta=meta, items=items, status_filter=status_filter,
        trend_svg=trend_svg,
    )


@app.route("/<entity_type>/new", methods=["GET", "POST"])
def new_item(entity_type):
    meta = get_meta_or_404(entity_type)
    if request.method == "POST":
        item = Item(
            entity_type=entity_type,
            name=request.form.get("name", "").strip(),
            description=request.form.get("description", "").strip(),
            owner=request.form.get("owner", "").strip(),
            category=request.form.get("category", "").strip(),
            status=request.form.get("status", "green"),
            due_date=parse_date(request.form.get("due_date")),
            metric_label=request.form.get("metric_label", "").strip() or meta["metric_label_default"],
            metric_value=parse_float(request.form.get("metric_value")),
            metric_target=parse_float(request.form.get("metric_target")),
        )
        if not item.name:
            flash("Nome é obrigatório.", "error")
            return render_template("form.html", entity_type=entity_type, meta=meta, item=item, mode="new")
        db.session.add(item)
        db.session.flush()
        db.session.add(
            StatusHistory(
                item_id=item.id,
                status=item.status,
                note="Item criado.",
                changed_by=request.form.get("owner", "") or "—",
            )
        )
        db.session.commit()
        flash(f"{meta['singular']} criado com sucesso.", "success")
        return redirect(url_for("item_detail", entity_type=entity_type, item_id=item.id))

    return render_template("form.html", entity_type=entity_type, meta=meta, item=None, mode="new")


@app.route("/<entity_type>/<int:item_id>")
def item_detail(entity_type, item_id):
    meta = get_meta_or_404(entity_type)
    item = Item.query.filter_by(entity_type=entity_type, id=item_id).first_or_404()
    status_bar_svg = charts.render_status_bar_svg(item)
    return render_template(
        "detail.html", entity_type=entity_type, meta=meta, item=item, status_bar_svg=status_bar_svg
    )


@app.route("/<entity_type>/<int:item_id>/edit", methods=["GET", "POST"])
def edit_item(entity_type, item_id):
    meta = get_meta_or_404(entity_type)
    item = Item.query.filter_by(entity_type=entity_type, id=item_id).first_or_404()
    if request.method == "POST":
        item.name = request.form.get("name", "").strip()
        item.description = request.form.get("description", "").strip()
        item.owner = request.form.get("owner", "").strip()
        item.category = request.form.get("category", "").strip()
        item.due_date = parse_date(request.form.get("due_date"))
        item.metric_label = request.form.get("metric_label", "").strip() or meta["metric_label_default"]
        item.metric_value = parse_float(request.form.get("metric_value"))
        item.metric_target = parse_float(request.form.get("metric_target"))
        if not item.name:
            flash("Nome é obrigatório.", "error")
            return render_template("form.html", entity_type=entity_type, meta=meta, item=item, mode="edit")
        db.session.commit()
        flash(f"{meta['singular']} atualizado.", "success")
        return redirect(url_for("item_detail", entity_type=entity_type, item_id=item.id))

    return render_template("form.html", entity_type=entity_type, meta=meta, item=item, mode="edit")


@app.route("/<entity_type>/<int:item_id>/status", methods=["POST"])
def update_status(entity_type, item_id):
    meta = get_meta_or_404(entity_type)
    item = Item.query.filter_by(entity_type=entity_type, id=item_id).first_or_404()
    new_status = request.form.get("status")
    note = request.form.get("note", "").strip()
    changed_by = request.form.get("changed_by", "").strip() or item.owner or "—"
    if new_status not in STATUSES:
        flash("Status inválido.", "error")
        return redirect(url_for("item_detail", entity_type=entity_type, item_id=item.id))

    item.status = new_status
    db.session.add(
        StatusHistory(item_id=item.id, status=new_status, note=note, changed_by=changed_by)
    )
    db.session.commit()
    flash("Status atualizado.", "success")
    return redirect(url_for("item_detail", entity_type=entity_type, item_id=item.id))


@app.route("/<entity_type>/<int:item_id>/delete", methods=["POST"])
def delete_item(entity_type, item_id):
    meta = get_meta_or_404(entity_type)
    item = Item.query.filter_by(entity_type=entity_type, id=item_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash(f"{meta['singular']} excluído.", "success")
    return redirect(url_for("list_items", entity_type=entity_type))


def _status_counts(items):
    counts = {s: 0 for s in STATUSES}
    for it in items:
        counts[it.status] += 1
    return counts


@app.route("/<entity_type>/export/excel")
def export_type_excel(entity_type):
    meta = get_meta_or_404(entity_type)
    items = Item.query.filter_by(entity_type=entity_type).order_by(Item.name).all()
    buf = exports.build_excel(
        items_by_type={entity_type: items}, meta_by_type={entity_type: meta}, all_items=items
    )
    fname = f"rag-tracker-{entity_type}-{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
    return send_file(buf, as_attachment=True, download_name=fname,
                      mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route("/<entity_type>/export/pdf")
def export_type_pdf(entity_type):
    meta = get_meta_or_404(entity_type)
    items = Item.query.filter_by(entity_type=entity_type).order_by(
        db.case((Item.status == "red", 0), (Item.status == "amber", 1), else_=2), Item.name
    ).all()
    counts = _status_counts(items)
    sections = [
        ("Vermelho", counts, [i for i in items if i.status == "red"]),
        ("Amarelo", counts, [i for i in items if i.status == "amber"]),
        ("Verde", counts, [i for i in items if i.status == "green"]),
    ]
    buf = exports.build_pdf(meta["plural"], counts, sections)
    fname = f"rag-tracker-{entity_type}-{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return send_file(buf, as_attachment=True, download_name=fname, mimetype="application/pdf")


@app.route("/export/excel")
def export_all_excel():
    all_items = Item.query.all()
    items_by_type = {et: [i for i in all_items if i.entity_type == et] for et in ENTITY_TYPES}
    buf = exports.build_excel(items_by_type=items_by_type, meta_by_type=ENTITY_TYPES, all_items=all_items)
    fname = f"rag-tracker-completo-{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
    return send_file(buf, as_attachment=True, download_name=fname,
                      mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route("/export/pdf")
def export_all_pdf():
    all_items = Item.query.all()
    counts = _status_counts(all_items)
    sections = []
    for et, meta in ENTITY_TYPES.items():
        type_items = sorted(
            [i for i in all_items if i.entity_type == et],
            key=lambda i: (0 if i.status == "red" else 1 if i.status == "amber" else 2, i.name),
        )
        sections.append((meta["plural"], _status_counts(type_items), type_items))
    buf = exports.build_pdf("Todos os itens", counts, sections)
    fname = f"rag-tracker-completo-{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return send_file(buf, as_attachment=True, download_name=fname, mimetype="application/pdf")


with app.app_context():
    db.create_all()
    if IS_SERVERLESS:
        from seed import seed_data
        seed_data(db, Item, StatusHistory)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
