from flask import Blueprint, jsonify, request

from .. import constants as c
from ..extensions import db
from ..models import Sistema, log_status
from ..utils import error, parse_date

bp = Blueprint("sistemas", __name__, url_prefix="/api/sistemas")


@bp.get("")
def list_sistemas():
    query = Sistema.query
    criticidade = request.args.get("criticidade")
    categoria = request.args.get("categoria")
    status_rag = request.args.get("status_rag")
    if criticidade:
        query = query.filter_by(criticidade=criticidade)
    if categoria:
        query = query.filter_by(categoria=categoria)
    if status_rag:
        query = query.filter_by(status_rag=status_rag)
    items = query.order_by(Sistema.nome).all()
    return jsonify([s.to_dict(include_counts=True) for s in items])


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
    if "categoria" in payload:
        if payload["categoria"] not in c.CATEGORIAS_SISTEMA:
            return "Categoria inválida."
        item.categoria = payload["categoria"]
    if "criticidade" in payload:
        if payload["criticidade"] not in c.CRITICIDADES:
            return "Criticidade inválida."
        item.criticidade = payload["criticidade"]
    if "ambiente" in payload:
        if payload["ambiente"] not in c.AMBIENTES_SISTEMA:
            return "Ambiente inválido."
        item.ambiente = payload["ambiente"]
    if "fornecedor" in payload:
        item.fornecedor = payload.get("fornecedor") or ""
    if "owner_id" in payload:
        if not payload.get("owner_id"):
            return "Responsável (owner) é obrigatório."
        item.owner_id = payload["owner_id"]
    elif is_new:
        return "Responsável (owner) é obrigatório."
    if "status_rag" in payload:
        if payload["status_rag"] not in c.STATUS_RAG:
            return "Status RAG inválido."
        item.status_rag = payload["status_rag"]
    if "data_fim_suporte" in payload:
        item.data_fim_suporte = parse_date(payload.get("data_fim_suporte"))
    return None


@bp.post("")
def create_sistema():
    payload = request.get_json(force=True) or {}
    item = Sistema(categoria="aplicacao", status_rag="green")
    err = _apply_fields(item, payload, is_new=True)
    if err:
        return error(err)
    db.session.add(item)
    db.session.flush()
    log_status("sistema", item.id, item.status_rag, usuario_id=item.owner_id, nota="Sistema cadastrado.")
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.get("/<int:sistema_id>")
def get_sistema(sistema_id):
    item = Sistema.query.get_or_404(sistema_id)
    return jsonify(item.to_dict(include_counts=True))


@bp.put("/<int:sistema_id>")
def update_sistema(sistema_id):
    item = Sistema.query.get_or_404(sistema_id)
    payload = request.get_json(force=True) or {}
    status_before = item.status_rag
    err = _apply_fields(item, payload)
    if err:
        return error(err)
    if item.status_rag != status_before:
        log_status("sistema", item.id, item.status_rag, usuario_id=item.owner_id, nota=payload.get("nota", ""))
    db.session.commit()
    return jsonify(item.to_dict())


@bp.delete("/<int:sistema_id>")
def delete_sistema(sistema_id):
    item = Sistema.query.get_or_404(sistema_id)
    db.session.delete(item)
    db.session.commit()
    return "", 204
