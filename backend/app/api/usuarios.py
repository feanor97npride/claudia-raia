from flask import Blueprint, jsonify, request

from .. import constants as c
from ..extensions import db
from ..models import Area, Usuario
from ..utils import error

bp = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")


@bp.get("")
def list_usuarios():
    incluir_inativos = request.args.get("incluir_inativos") == "1"
    query = Usuario.query if incluir_inativos else Usuario.query.filter_by(ativo=True)
    items = query.order_by(Usuario.nome).all()
    return jsonify([u.to_dict() for u in items])


def _apply_fields(item, payload, is_new=False):
    if "nome" in payload:
        nome = (payload.get("nome") or "").strip()
        if not nome:
            return "Nome é obrigatório."
        item.nome = nome
    elif is_new:
        return "Nome é obrigatório."

    if "email" in payload:
        email = (payload.get("email") or "").strip().lower()
        if not email:
            return "E-mail é obrigatório."
        existing = Usuario.query.filter_by(email=email).first()
        if existing and existing.id != item.id:
            return "Já existe um usuário com este e-mail."
        item.email = email
    elif is_new:
        return "E-mail é obrigatório."

    if "area_id" in payload:
        area_id = payload.get("area_id") or None
        if area_id and not Area.query.get(area_id):
            return "Área inválida."
        item.area_id = area_id
    if "papel" in payload:
        if payload["papel"] not in c.PAPEIS_USUARIO:
            return "Papel inválido."
        item.papel = payload["papel"]
    if "ativo" in payload:
        item.ativo = bool(payload["ativo"])
    return None


@bp.post("")
def create_usuario():
    payload = request.get_json(force=True) or {}
    item = Usuario(papel="analista", ativo=True)
    err = _apply_fields(item, payload, is_new=True)
    if err:
        return error(err)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.put("/<int:usuario_id>")
def update_usuario(usuario_id):
    item = Usuario.query.get_or_404(usuario_id)
    payload = request.get_json(force=True) or {}
    err = _apply_fields(item, payload)
    if err:
        return error(err)
    db.session.commit()
    return jsonify(item.to_dict())


@bp.delete("/<int:usuario_id>")
def delete_usuario(usuario_id):
    item = Usuario.query.get_or_404(usuario_id)
    item.ativo = False
    db.session.commit()
    return "", 204
