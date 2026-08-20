from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Area
from ..utils import error

bp = Blueprint("areas", __name__, url_prefix="/api/areas")


@bp.get("")
def list_areas():
    items = Area.query.order_by(Area.nome).all()
    return jsonify([a.to_dict() for a in items])


@bp.post("")
def create_area():
    payload = request.get_json(force=True) or {}
    nome = (payload.get("nome") or "").strip()
    if not nome:
        return error("Nome é obrigatório.")
    item = Area(nome=nome, sigla=(payload.get("sigla") or "").strip())
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.delete("/<int:area_id>")
def delete_area(area_id):
    item = Area.query.get_or_404(area_id)
    if item.usuarios:
        return error("Não é possível excluir uma área com usuários vinculados.")
    db.session.delete(item)
    db.session.commit()
    return "", 204
