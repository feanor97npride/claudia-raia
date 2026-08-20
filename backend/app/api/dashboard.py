from datetime import date, timedelta

from flask import Blueprint, jsonify
from sqlalchemy import func

from .. import constants as c
from ..extensions import db
from ..models import Area, Ativo, Demanda, Documento, Projeto, Sistema, projeto_area

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def _counts_by(model, column, options):
    rows = db.session.query(column, func.count(model.id)).group_by(column).all()
    counts = {opt: 0 for opt in options}
    for value, total in rows:
        if value in counts:
            counts[value] = total
    return counts


@bp.get("/kpis")
def kpis():
    today = date.today()
    in_7_days = today + timedelta(days=7)

    demandas_por_status = _counts_by(Demanda, Demanda.status_kanban, c.STATUS_KANBAN)
    projetos_por_criticidade = _counts_by(Projeto, Projeto.criticidade, c.CRITICIDADES)
    projetos_por_status_rag = _counts_by(Projeto, Projeto.status_rag, c.STATUS_RAG)
    sistemas_por_status_rag = _counts_by(Sistema, Sistema.status_rag, c.STATUS_RAG)
    sistemas_por_criticidade = _counts_by(Sistema, Sistema.criticidade, c.CRITICIDADES)

    projetos_por_area = (
        db.session.query(Area.nome, func.count(projeto_area.c.projeto_id))
        .join(projeto_area, projeto_area.c.area_id == Area.id)
        .group_by(Area.nome)
        .order_by(Area.nome)
        .all()
    )

    demandas_atrasadas = Demanda.query.filter(Demanda.status_kanban == "em_atraso").count()
    demandas_vencendo_7_dias = Demanda.query.filter(
        Demanda.status_kanban.in_(["nao_iniciado", "em_andamento"]),
        Demanda.data_prazo.isnot(None),
        Demanda.data_prazo <= in_7_days,
        Demanda.data_prazo >= today,
    ).count()

    documentos_pendentes = Documento.query.filter(
        Documento.status_aprovacao.in_(["rascunho", "em_aprovacao"])
    ).count()
    documentos_por_status = _counts_by(Documento, Documento.status_aprovacao, c.STATUS_APROVACAO_DOC)

    total_ativos = Ativo.query.count()
    ativos_por_status = _counts_by(Ativo, Ativo.status, c.STATUS_ATIVO)

    return jsonify({
        "demandas_por_status": demandas_por_status,
        "demandas_atrasadas": demandas_atrasadas,
        "demandas_vencendo_7_dias": demandas_vencendo_7_dias,
        "projetos_total": Projeto.query.count(),
        "projetos_por_criticidade": projetos_por_criticidade,
        "projetos_por_status_rag": projetos_por_status_rag,
        "projetos_por_area": [{"area": nome, "total": total} for nome, total in projetos_por_area],
        "sistemas_total": Sistema.query.count(),
        "sistemas_por_status_rag": sistemas_por_status_rag,
        "sistemas_por_criticidade": sistemas_por_criticidade,
        "documentos_pendentes_aprovacao": documentos_pendentes,
        "documentos_por_status": documentos_por_status,
        "total_ativos": total_ativos,
        "ativos_por_status": ativos_por_status,
    })
