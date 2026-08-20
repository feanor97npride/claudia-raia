from datetime import date

from flask import Blueprint, jsonify, request

from .. import constants as c
from ..extensions import db
from ..models import Demanda, log_status
from ..utils import error, parse_date

bp = Blueprint("demandas", __name__, url_prefix="/api/demandas")


def recalcular_atrasos():
    """Promotes overdue open demandas to 'em_atraso'. Stands in for a daily job."""
    vencidas = Demanda.query.filter(
        Demanda.status_kanban.in_(["nao_iniciado", "em_andamento"]),
        Demanda.data_prazo.isnot(None),
        Demanda.data_prazo < date.today(),
    ).all()
    for item in vencidas:
        item.status_kanban = "em_atraso"
        log_status("demanda", item.id, "em_atraso", nota="Prazo vencido (recálculo automático).")
    if vencidas:
        db.session.commit()


@bp.get("")
def list_demandas():
    recalcular_atrasos()
    query = Demanda.query
    status = request.args.get("status_kanban")
    projeto_id = request.args.get("projeto_id")
    sistema_id = request.args.get("sistema_id")
    responsavel_id = request.args.get("responsavel_id")
    if status:
        query = query.filter_by(status_kanban=status)
    if projeto_id:
        query = query.filter_by(projeto_id=projeto_id)
    if sistema_id:
        query = query.filter_by(sistema_id=sistema_id)
    if responsavel_id:
        query = query.filter_by(responsavel_id=responsavel_id)
    items = query.order_by(Demanda.status_kanban, Demanda.ordem_kanban).all()
    return jsonify([d.to_dict() for d in items])


def _apply_fields(item, payload, is_new=False):
    if "titulo" in payload:
        titulo = (payload.get("titulo") or "").strip()
        if not titulo:
            return "Título é obrigatório."
        item.titulo = titulo
    elif is_new:
        return "Título é obrigatório."

    if "descricao" in payload:
        item.descricao = payload.get("descricao") or ""
    if "prioridade" in payload:
        if payload["prioridade"] not in c.PRIORIDADES:
            return "Prioridade inválida."
        item.prioridade = payload["prioridade"]
    if "responsavel_id" in payload:
        if not payload.get("responsavel_id"):
            return "Responsável é obrigatório."
        item.responsavel_id = payload["responsavel_id"]
    elif is_new:
        return "Responsável é obrigatório."
    if "projeto_id" in payload:
        item.projeto_id = payload.get("projeto_id") or None
    if "sistema_id" in payload:
        item.sistema_id = payload.get("sistema_id") or None
    if "data_prazo" in payload:
        item.data_prazo = parse_date(payload.get("data_prazo"))
    if "data_conclusao" in payload:
        item.data_conclusao = parse_date(payload.get("data_conclusao"))
    return None


@bp.post("")
def create_demanda():
    payload = request.get_json(force=True) or {}
    item = Demanda(status_kanban="nao_iniciado", ordem_kanban=0)
    err = _apply_fields(item, payload, is_new=True)
    if err:
        return error(err)
    max_ordem = db.session.query(db.func.max(Demanda.ordem_kanban)).filter_by(
        status_kanban=item.status_kanban
    ).scalar() or 0
    item.ordem_kanban = max_ordem + 1
    db.session.add(item)
    db.session.flush()
    log_status("demanda", item.id, item.status_kanban, usuario_id=item.responsavel_id, nota="Demanda criada.")
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.get("/<int:demanda_id>")
def get_demanda(demanda_id):
    item = Demanda.query.get_or_404(demanda_id)
    return jsonify(item.to_dict())


@bp.put("/<int:demanda_id>")
def update_demanda(demanda_id):
    item = Demanda.query.get_or_404(demanda_id)
    payload = request.get_json(force=True) or {}
    err = _apply_fields(item, payload)
    if err:
        return error(err)
    db.session.commit()
    return jsonify(item.to_dict())


@bp.delete("/<int:demanda_id>")
def delete_demanda(demanda_id):
    item = Demanda.query.get_or_404(demanda_id)
    db.session.delete(item)
    db.session.commit()
    return "", 204


@bp.put("/kanban-batch")
def kanban_batch():
    """Persists a full board move: {columns: {status_kanban: [demanda_id, ...]}}.

    Covers both reordering within a column and moving a card across columns in
    a single round trip, matching how drag-and-drop libraries report board state.
    """
    payload = request.get_json(force=True) or {}
    columns = payload.get("columns") or {}
    for status_kanban, ids in columns.items():
        if status_kanban not in c.STATUS_KANBAN:
            return error(f"Coluna inválida: {status_kanban}")
        for index, demanda_id in enumerate(ids):
            item = Demanda.query.get(demanda_id)
            if not item:
                continue
            if item.status_kanban != status_kanban:
                log_status("demanda", item.id, status_kanban, nota="Movido no board Kanban.")
                item.status_kanban = status_kanban
                if status_kanban == "concluido" and not item.data_conclusao:
                    from datetime import date
                    item.data_conclusao = date.today()
            item.ordem_kanban = index
    db.session.commit()
    return jsonify({"ok": True})
