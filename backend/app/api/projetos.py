from flask import Blueprint, jsonify, request

from .. import constants as c
from ..extensions import db
from ..models import Area, Projeto, Sistema, log_status
from ..utils import error, parse_date

bp = Blueprint("projetos", __name__, url_prefix="/api/projetos")


@bp.get("")
def list_projetos():
    query = Projeto.query
    fase = request.args.get("fase")
    status_rag = request.args.get("status_rag")
    if fase:
        query = query.filter_by(fase=fase)
    if status_rag:
        query = query.filter_by(status_rag=status_rag)
    items = query.order_by(Projeto.nome).all()
    return jsonify([p.to_dict() for p in items])


def _apply_fields(item, payload, is_new=False):
    if "nome" in payload:
        nome = (payload.get("nome") or "").strip()
        if not nome:
            return "Nome é obrigatório."
        item.nome = nome
    elif is_new:
        return "Nome é obrigatório."

    if "descricao" in payload:
        item.descricao = payload.get("descricao") or ""
    if "fase" in payload:
        if payload["fase"] not in c.FASES_PROJETO:
            return "Fase inválida."
        item.fase = payload["fase"]
    if "criticidade" in payload:
        if payload["criticidade"] not in c.CRITICIDADES:
            return "Criticidade inválida."
        item.criticidade = payload["criticidade"]
    if "status_rag" in payload:
        if payload["status_rag"] not in c.STATUS_RAG:
            return "Status RAG inválido."
        item.status_rag = payload["status_rag"]
    if "owner_id" in payload:
        if not payload.get("owner_id"):
            return "Responsável (owner) é obrigatório."
        item.owner_id = payload["owner_id"]
    elif is_new:
        return "Responsável (owner) é obrigatório."
    if "data_inicio" in payload:
        item.data_inicio = parse_date(payload.get("data_inicio"))
    if "data_fim_prevista" in payload:
        item.data_fim_prevista = parse_date(payload.get("data_fim_prevista"))
    if "area_ids" in payload:
        item.areas = Area.query.filter(Area.id.in_(payload.get("area_ids") or [])).all()
    if "sistema_ids" in payload:
        item.sistemas = Sistema.query.filter(Sistema.id.in_(payload.get("sistema_ids") or [])).all()
    return None


@bp.post("")
def create_projeto():
    payload = request.get_json(force=True) or {}
    item = Projeto(fase="planejamento", status_rag="green")
    err = _apply_fields(item, payload, is_new=True)
    if err:
        return error(err)
    db.session.add(item)
    db.session.flush()
    log_status("projeto", item.id, item.status_rag, usuario_id=item.owner_id, nota="Projeto criado.")
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.get("/<int:projeto_id>")
def get_projeto(projeto_id):
    item = Projeto.query.get_or_404(projeto_id)
    return jsonify(item.to_dict())


@bp.put("/<int:projeto_id>")
def update_projeto(projeto_id):
    item = Projeto.query.get_or_404(projeto_id)
    payload = request.get_json(force=True) or {}
    status_before = item.status_rag
    err = _apply_fields(item, payload)
    if err:
        return error(err)
    if item.status_rag != status_before:
        log_status("projeto", item.id, item.status_rag, usuario_id=item.owner_id, nota=payload.get("nota", ""))
    db.session.commit()
    return jsonify(item.to_dict())


@bp.delete("/<int:projeto_id>")
def delete_projeto(projeto_id):
    item = Projeto.query.get_or_404(projeto_id)
    db.session.delete(item)
    db.session.commit()
    return "", 204
