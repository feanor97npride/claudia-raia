import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request

from .. import constants as c
from ..extensions import db
from ..models import Assinatura, Documento, EtapaAprovacao
from ..utils import error, parse_date

bp = Blueprint("documentos", __name__, url_prefix="/api/documentos")


@bp.get("")
def list_documentos():
    query = Documento.query
    tipo = request.args.get("tipo")
    status = request.args.get("status_aprovacao")
    if tipo:
        query = query.filter_by(tipo=tipo)
    if status:
        query = query.filter_by(status_aprovacao=status)
    items = query.order_by(Documento.atualizado_em.desc()).all()
    return jsonify([d.to_dict() for d in items])


def _apply_fields(item, payload, is_new=False):
    if "titulo" in payload:
        titulo = (payload.get("titulo") or "").strip()
        if not titulo:
            return "Título é obrigatório."
        item.titulo = titulo
    elif is_new:
        return "Título é obrigatório."

    if "tipo" in payload:
        if payload["tipo"] not in c.TIPOS_DOCUMENTO:
            return "Tipo de documento inválido."
        item.tipo = payload["tipo"]
    if "descricao" in payload:
        item.descricao = payload.get("descricao") or ""
    if "versao" in payload:
        item.versao = payload.get("versao") or "1.0"
    if "projeto_id" in payload:
        item.projeto_id = payload.get("projeto_id") or None
    if "sistema_id" in payload:
        item.sistema_id = payload.get("sistema_id") or None
    if "autor_id" in payload:
        if not payload.get("autor_id"):
            return "Autor é obrigatório."
        item.autor_id = payload["autor_id"]
    elif is_new:
        return "Autor é obrigatório."
    if "arquivo_url" in payload:
        item.arquivo_url = payload.get("arquivo_url") or ""
    if "data_validade" in payload:
        item.data_validade = parse_date(payload.get("data_validade"))
    return None


@bp.post("")
def create_documento():
    payload = request.get_json(force=True) or {}
    item = Documento(tipo="politica_ti", status_aprovacao="rascunho")
    err = _apply_fields(item, payload, is_new=True)
    if err:
        return error(err)
    db.session.add(item)
    db.session.flush()

    for index, aprovador_id in enumerate(payload.get("aprovador_ids") or [], start=1):
        db.session.add(EtapaAprovacao(documento_id=item.id, ordem=index, aprovador_id=aprovador_id))

    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.get("/<int:documento_id>")
def get_documento(documento_id):
    item = Documento.query.get_or_404(documento_id)
    return jsonify(item.to_dict())


@bp.put("/<int:documento_id>")
def update_documento(documento_id):
    item = Documento.query.get_or_404(documento_id)
    payload = request.get_json(force=True) or {}
    err = _apply_fields(item, payload)
    if err:
        return error(err)
    if "status_aprovacao" in payload:
        if payload["status_aprovacao"] not in c.STATUS_APROVACAO_DOC:
            return error("Status de aprovação inválido.")
        item.status_aprovacao = payload["status_aprovacao"]
    db.session.commit()
    return jsonify(item.to_dict())


@bp.delete("/<int:documento_id>")
def delete_documento(documento_id):
    item = Documento.query.get_or_404(documento_id)
    db.session.delete(item)
    db.session.commit()
    return "", 204


@bp.post("/<int:documento_id>/enviar-aprovacao")
def enviar_aprovacao(documento_id):
    item = Documento.query.get_or_404(documento_id)
    if not item.etapas:
        return error("Cadastre ao menos um aprovador antes de enviar para aprovação.")
    item.status_aprovacao = "em_aprovacao"
    db.session.commit()
    return jsonify(item.to_dict())


@bp.put("/<int:documento_id>/etapas/<int:etapa_id>")
def decidir_etapa(documento_id, etapa_id):
    etapa = EtapaAprovacao.query.filter_by(id=etapa_id, documento_id=documento_id).first_or_404()
    payload = request.get_json(force=True) or {}
    decisao = payload.get("status")
    if decisao not in ("aprovado", "rejeitado"):
        return error("Decisão deve ser 'aprovado' ou 'rejeitado'.")

    etapa.status = decisao
    etapa.comentario = payload.get("comentario", "")
    etapa.decidido_em = datetime.utcnow()

    documento = etapa.documento
    if decisao == "rejeitado":
        documento.status_aprovacao = "rejeitado"
    elif all(e.status == "aprovado" for e in documento.etapas):
        documento.status_aprovacao = "aprovado"

    db.session.commit()
    return jsonify(documento.to_dict())


@bp.post("/<int:documento_id>/assinaturas")
def criar_assinatura(documento_id):
    Documento.query.get_or_404(documento_id)
    payload = request.get_json(force=True) or {}
    provedor = payload.get("provedor", "docusign")
    if provedor not in c.PROVEDORES_ASSINATURA:
        return error("Provedor de assinatura não suportado.")

    item = Assinatura(
        documento_id=documento_id,
        signatario_id=payload.get("signatario_id") or None,
        signatario_email=payload.get("signatario_email") or "",
        provedor=provedor,
        status="pendente",
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.post("/<int:documento_id>/assinaturas/<int:assinatura_id>/enviar")
def enviar_assinatura(documento_id, assinatura_id):
    """Stub for the digital-signature provider integration.

    Marks the request as sent and fabricates a tracking id/URL so the UI has
    something to point at. Swap this body for a real call to the DocuSign /
    Clicksign / D4Sign API — the `provedor` field already selects which one.
    """
    item = Assinatura.query.filter_by(id=assinatura_id, documento_id=documento_id).first_or_404()
    item.status = "enviado"
    item.id_externo = f"stub-{uuid.uuid4().hex[:12]}"
    item.url_assinatura = f"https://exemplo-{item.provedor}.invalid/assinar/{item.id_externo}"
    db.session.commit()
    return jsonify(item.to_dict())
