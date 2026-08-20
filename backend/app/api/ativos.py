import xml.etree.ElementTree as ET

from flask import Blueprint, jsonify, request

from .. import constants as c
from ..extensions import db
from ..models import Ativo, Sistema
from ..utils import error, parse_date

bp = Blueprint("ativos", __name__, url_prefix="/api/ativos")


@bp.get("")
def list_ativos():
    query = Ativo.query
    tipo = request.args.get("tipo")
    status = request.args.get("status")
    sistema_id = request.args.get("sistema_id")
    if tipo:
        query = query.filter_by(tipo=tipo)
    if status:
        query = query.filter_by(status=status)
    if sistema_id:
        query = query.filter_by(sistema_id=sistema_id)
    items = query.order_by(Ativo.nome).all()
    return jsonify([a.to_dict() for a in items])


def _apply_fields(item, payload, is_new=False):
    if "nome" in payload:
        nome = (payload.get("nome") or "").strip()
        if not nome:
            return "Nome é obrigatório."
        item.nome = nome
    elif is_new:
        return "Nome é obrigatório."

    if "tipo" in payload:
        if payload["tipo"] not in c.TIPOS_ATIVO:
            return "Tipo de ativo inválido."
        item.tipo = payload["tipo"]
    if "sistema_id" in payload:
        item.sistema_id = payload.get("sistema_id") or None
    if "numero_serie" in payload:
        item.numero_serie = payload.get("numero_serie") or ""
    if "chave_licenca" in payload:
        item.chave_licenca = payload.get("chave_licenca") or ""
    if "fabricante" in payload:
        item.fabricante = payload.get("fabricante") or ""
    if "quantidade" in payload:
        try:
            item.quantidade = max(1, int(payload.get("quantidade") or 1))
        except (TypeError, ValueError):
            return "Quantidade inválida."
    if "status" in payload:
        if payload["status"] not in c.STATUS_ATIVO:
            return "Status inválido."
        item.status = payload["status"]
    if "responsavel_id" in payload:
        item.responsavel_id = payload.get("responsavel_id") or None
    if "localizacao" in payload:
        item.localizacao = payload.get("localizacao") or ""
    if "data_aquisicao" in payload:
        item.data_aquisicao = parse_date(payload.get("data_aquisicao"))
    if "data_expiracao" in payload:
        item.data_expiracao = parse_date(payload.get("data_expiracao"))
    return None


@bp.post("")
def create_ativo():
    payload = request.get_json(force=True) or {}
    item = Ativo(tipo="hardware", status="estoque", origem_importacao="manual")
    err = _apply_fields(item, payload, is_new=True)
    if err:
        return error(err)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.put("/<int:ativo_id>")
def update_ativo(ativo_id):
    item = Ativo.query.get_or_404(ativo_id)
    payload = request.get_json(force=True) or {}
    err = _apply_fields(item, payload)
    if err:
        return error(err)
    db.session.commit()
    return jsonify(item.to_dict())


@bp.delete("/<int:ativo_id>")
def delete_ativo(ativo_id):
    item = Ativo.query.get_or_404(ativo_id)
    db.session.delete(item)
    db.session.commit()
    return "", 204


@bp.patch("/bulk")
def bulk_update():
    """Mass asset movement: apply the same field changes to many assets at once."""
    payload = request.get_json(force=True) or {}
    ids = payload.get("ids") or []
    fields = payload.get("fields") or {}
    if not ids:
        return error("Nenhum ativo selecionado.")
    if not fields:
        return error("Nenhuma alteração informada.")

    allowed = {"status", "localizacao", "responsavel_id", "sistema_id"}
    unknown = set(fields) - allowed
    if unknown:
        return error(f"Campos não suportados para atualização em massa: {', '.join(unknown)}")
    if "status" in fields and fields["status"] not in c.STATUS_ATIVO:
        return error("Status inválido.")

    items = Ativo.query.filter(Ativo.id.in_(ids)).all()
    for item in items:
        if "status" in fields:
            item.status = fields["status"]
        if "localizacao" in fields:
            item.localizacao = fields["localizacao"] or ""
        if "responsavel_id" in fields:
            item.responsavel_id = fields["responsavel_id"] or None
        if "sistema_id" in fields:
            item.sistema_id = fields["sistema_id"] or None
    db.session.commit()
    return jsonify({"atualizados": len(items)})


def _text(el, tag, default=""):
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else default


@bp.post("/import-xml")
def import_xml():
    """Bulk-imports assets from an XML file. Expected shape:

    <ativos>
      <ativo>
        <tipo>hardware</tipo>
        <nome>Notebook Dell Latitude 5420</nome>
        <numero_serie>SN12345</numero_serie>
        <fabricante>Dell</fabricante>
        <quantidade>1</quantidade>
        <status>estoque</status>
        <localizacao>Filial SP</localizacao>
        <sistema_nome>Portal Corporativo Intranet</sistema_nome>
        <data_aquisicao>2024-01-15</data_aquisicao>
        <data_expiracao>2027-01-15</data_expiracao>
      </ativo>
    </ativos>
    """
    upload = request.files.get("file")
    if not upload:
        return error("Envie um arquivo XML no campo 'file'.")

    raw = upload.read()
    if len(raw) > 5 * 1024 * 1024:
        return error("Arquivo excede o limite de 5 MB.")

    # Reject DTDs/external entities outright rather than relying on the
    # stdlib parser's entity-expansion defaults for untrusted uploads.
    lowered = raw.lower()
    if b"<!doctype" in lowered or b"<!entity" in lowered:
        return error("Arquivo XML com DOCTYPE/ENTITY não é permitido.")

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        return error(f"XML inválido: {exc}")

    sistemas_by_nome = {s.nome.strip().lower(): s.id for s in Sistema.query.all()}

    criados = 0
    erros = []
    nodes = root.findall("ativo") if root.tag != "ativo" else [root]
    for index, node in enumerate(nodes, start=1):
        nome = _text(node, "nome")
        if not nome:
            erros.append(f"Item {index}: campo <nome> ausente ou vazio.")
            continue
        tipo = _text(node, "tipo", "hardware")
        if tipo not in c.TIPOS_ATIVO:
            erros.append(f"Item {index} ({nome}): tipo '{tipo}' inválido, use {', '.join(c.TIPOS_ATIVO)}.")
            continue
        status = _text(node, "status", "estoque")
        if status not in c.STATUS_ATIVO:
            erros.append(f"Item {index} ({nome}): status '{status}' inválido.")
            continue
        try:
            quantidade = int(_text(node, "quantidade", "1") or "1")
        except ValueError:
            erros.append(f"Item {index} ({nome}): quantidade inválida.")
            continue

        sistema_nome = _text(node, "sistema_nome").strip().lower()
        sistema_id = sistemas_by_nome.get(sistema_nome) if sistema_nome else None

        item = Ativo(
            tipo=tipo,
            nome=nome,
            sistema_id=sistema_id,
            numero_serie=_text(node, "numero_serie"),
            chave_licenca=_text(node, "chave_licenca"),
            fabricante=_text(node, "fabricante"),
            quantidade=max(1, quantidade),
            status=status,
            localizacao=_text(node, "localizacao"),
            data_aquisicao=parse_date(_text(node, "data_aquisicao")),
            data_expiracao=parse_date(_text(node, "data_expiracao")),
            origem_importacao="xml",
        )
        db.session.add(item)
        criados += 1

    if criados:
        db.session.commit()
    else:
        db.session.rollback()

    return jsonify({"criados": criados, "erros": erros})
