from flask import Blueprint, jsonify

from .. import constants as c
from ..extensions import db
from ..models import Area, Projeto, Sistema, Usuario

bp = Blueprint("meta", __name__, url_prefix="/api")


@bp.get("/meta")
def meta():
    usuarios = Usuario.query.filter_by(ativo=True).order_by(Usuario.nome).all()
    areas = Area.query.order_by(Area.nome).all()
    sistemas = Sistema.query.order_by(Sistema.nome).all()
    projetos = Projeto.query.order_by(Projeto.nome).all()

    return jsonify({
        "usuarios": [u.to_dict() for u in usuarios],
        "areas": [a.to_dict() for a in areas],
        "sistemas": [{"id": s.id, "nome": s.nome, "criticidade": s.criticidade} for s in sistemas],
        "projetos": [{"id": p.id, "nome": p.nome} for p in projetos],
        "enums": {
            "status_rag": c.STATUS_RAG,
            "status_rag_labels": c.STATUS_RAG_LABELS,
            "status_kanban": c.STATUS_KANBAN,
            "status_kanban_labels": c.STATUS_KANBAN_LABELS,
            "prioridades": c.PRIORIDADES,
            "prioridade_labels": c.PRIORIDADE_LABELS,
            "fases_projeto": c.FASES_PROJETO,
            "fase_labels": c.FASE_LABELS,
            "categorias_sistema": c.CATEGORIAS_SISTEMA,
            "categoria_sistema_labels": c.CATEGORIA_SISTEMA_LABELS,
            "ambientes_sistema": c.AMBIENTES_SISTEMA,
            "tipos_ativo": c.TIPOS_ATIVO,
            "tipo_ativo_labels": c.TIPO_ATIVO_LABELS,
            "status_ativo": c.STATUS_ATIVO,
            "status_ativo_labels": c.STATUS_ATIVO_LABELS,
            "tipos_documento": c.TIPOS_DOCUMENTO,
            "tipo_documento_labels": c.TIPO_DOCUMENTO_LABELS,
            "status_aprovacao_doc": c.STATUS_APROVACAO_DOC,
            "status_aprovacao_doc_labels": c.STATUS_APROVACAO_DOC_LABELS,
            "provedores_assinatura": c.PROVEDORES_ASSINATURA,
        },
    })
