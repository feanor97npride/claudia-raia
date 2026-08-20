from datetime import datetime

from flask import Blueprint, jsonify, request, send_file

from .. import constants as c
from ..exports import XLSX_MIMETYPE, build_listing, build_template
from ..extensions import db
from ..imports import find_usuario, get, parse_date_flex, read_rows, resolve_enum
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


@bp.post("/import-planilha")
def import_planilha():
    """Bulk-creates projetos from an uploaded .xlsx/.csv. Expected columns:
    nome, descricao (descrição), fase, criticidade, status_rag (status rag),
    responsavel (responsável/owner — nome ou e-mail, precisa já existir em
    Usuários), data_inicio (início), data_fim_prevista (fim previsto)."""
    upload = request.files.get("file")
    if not upload:
        return error("Envie um arquivo .xlsx ou .csv no campo 'file'.")
    try:
        rows = read_rows(upload)
    except ValueError as exc:
        return error(str(exc))

    criados = 0
    erros = []
    avisos = []

    for index, row in enumerate(rows, start=2):
        nome = get(row, "nome", "projeto")
        if not nome:
            erros.append(f"Linha {index}: nome é obrigatório.")
            continue

        owner_ref = get(row, "responsavel", "responsável", "owner", "responsavel_email")
        usuario = find_usuario(owner_ref)
        if not usuario:
            erros.append(
                f"Linha {index} ({nome}): responsável '{owner_ref}' não encontrado. "
                "Cadastre a pessoa em Usuários primeiro."
            )
            continue

        item = Projeto(
            nome=nome,
            descricao=get(row, "descricao", "descrição"),
            fase=resolve_enum(get(row, "fase"), c.FASES_PROJETO, c.FASE_LABELS, default="planejamento"),
            criticidade=resolve_enum(get(row, "criticidade"), c.CRITICIDADES, c.CRITICIDADE_LABELS, default="media"),
            status_rag=resolve_enum(
                get(row, "status_rag", "status rag", "rag"), c.STATUS_RAG, c.STATUS_RAG_LABELS, default="green"
            ),
            owner_id=usuario.id,
            data_inicio=parse_date_flex(get(row, "data_inicio", "início", "inicio")),
            data_fim_prevista=parse_date_flex(get(row, "data_fim_prevista", "fim previsto", "prazo")),
        )
        db.session.add(item)
        db.session.flush()
        log_status("projeto", item.id, item.status_rag, usuario_id=item.owner_id, nota="Criado via importação de planilha.")
        criados += 1

    if criados:
        db.session.commit()
    else:
        db.session.rollback()

    return jsonify({"criados": criados, "erros": erros, "avisos": avisos})


PROJETO_TEMPLATE_HEADERS = [
    "Nome", "Descrição", "Fase", "Criticidade", "Status RAG", "Responsável", "Data Início", "Data Fim Prevista",
]
PROJETO_TEMPLATE_EXAMPLE = [
    "Migração ERP SAP S/4HANA", "Migração do ambiente SAP ECC para S/4HANA", "Execução", "Alta", "Âmbar",
    "nome.sobrenome@empresa.com", "01/03/2026", "31/12/2026",
]


@bp.get("/modelo-planilha")
def modelo_planilha():
    """Downloads a blank .xlsx with the exact columns import-planilha expects."""
    buf = build_template(
        PROJETO_TEMPLATE_HEADERS,
        example_row=PROJETO_TEMPLATE_EXAMPLE,
        note=(
            "Modelo de importação de Projetos — preencha uma linha por projeto "
            "(a linha abaixo é só um exemplo, pode apagar). "
            "Responsável precisa já existir em Usuários (nome ou e-mail)."
        ),
    )
    return send_file(
        buf, as_attachment=True, download_name="modelo-projetos.xlsx", mimetype=XLSX_MIMETYPE
    )


@bp.get("/exportar")
def exportar():
    """Downloads the current list of projetos as .xlsx."""
    items = Projeto.query.order_by(Projeto.nome).all()
    headers = [
        "Nome", "Fase", "Criticidade", "Status RAG", "Responsável", "Áreas impactadas",
        "Sistemas envolvidos", "Início", "Fim previsto", "Total de demandas",
    ]
    rows = [
        [
            p.nome,
            c.FASE_LABELS.get(p.fase, p.fase),
            c.CRITICIDADE_LABELS.get(p.criticidade, p.criticidade),
            c.STATUS_RAG_LABELS.get(p.status_rag, p.status_rag),
            p.owner.nome if p.owner else "",
            ", ".join(a.nome for a in p.areas),
            ", ".join(s.nome for s in p.sistemas),
            p.data_inicio.strftime("%d/%m/%Y") if p.data_inicio else "",
            p.data_fim_prevista.strftime("%d/%m/%Y") if p.data_fim_prevista else "",
            len(p.demandas),
        ]
        for p in items
    ]
    buf = build_listing(headers, rows)
    fname = f"projetos-{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
    return send_file(buf, as_attachment=True, download_name=fname, mimetype=XLSX_MIMETYPE)
