from datetime import datetime

from .extensions import db


def utcnow():
    return datetime.utcnow()


projeto_area = db.Table(
    "projeto_area",
    db.Column("projeto_id", db.Integer, db.ForeignKey("projeto.id"), primary_key=True),
    db.Column("area_id", db.Integer, db.ForeignKey("area.id"), primary_key=True),
)

projeto_sistema = db.Table(
    "projeto_sistema",
    db.Column("projeto_id", db.Integer, db.ForeignKey("projeto.id"), primary_key=True),
    db.Column("sistema_id", db.Integer, db.ForeignKey("sistema.id"), primary_key=True),
)


class Area(db.Model):
    __tablename__ = "area"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    sigla = db.Column(db.String(20), default="")

    usuarios = db.relationship("Usuario", backref="area", lazy="selectin")

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "sigla": self.sigla}


class Usuario(db.Model):
    __tablename__ = "usuario"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False, unique=True)
    area_id = db.Column(db.Integer, db.ForeignKey("area.id"), nullable=True)
    papel = db.Column(db.String(30), nullable=False, default="analista")
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "area_id": self.area_id,
            "area_nome": self.area.nome if self.area else None,
            "papel": self.papel,
            "ativo": self.ativo,
        }


class Sistema(db.Model):
    __tablename__ = "sistema"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(160), nullable=False)
    descricao = db.Column(db.Text, default="")
    categoria = db.Column(db.String(30), nullable=False, default="aplicacao")
    criticidade = db.Column(db.String(20), nullable=False, default="media")
    ambiente = db.Column(db.String(20), nullable=False, default="producao")
    fornecedor = db.Column(db.String(160), default="")
    owner_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    status_rag = db.Column(db.String(10), nullable=False, default="green")
    data_fim_suporte = db.Column(db.Date, nullable=True)
    criado_em = db.Column(db.DateTime, default=utcnow)
    atualizado_em = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    owner = db.relationship("Usuario", foreign_keys=[owner_id], lazy="joined")
    ativos = db.relationship("Ativo", backref="sistema", lazy="selectin")
    projetos = db.relationship("Projeto", secondary=projeto_sistema, back_populates="sistemas")

    def to_dict(self, include_counts=False):
        data = {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "criticidade": self.criticidade,
            "ambiente": self.ambiente,
            "fornecedor": self.fornecedor,
            "owner_id": self.owner_id,
            "owner_nome": self.owner.nome if self.owner else None,
            "status_rag": self.status_rag,
            "data_fim_suporte": self.data_fim_suporte.isoformat() if self.data_fim_suporte else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }
        if include_counts:
            data["total_ativos"] = len(self.ativos)
        return data


class Projeto(db.Model):
    __tablename__ = "projeto"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(160), nullable=False)
    descricao = db.Column(db.Text, default="")
    fase = db.Column(db.String(20), nullable=False, default="planejamento")
    criticidade = db.Column(db.String(20), nullable=False, default="media")
    status_rag = db.Column(db.String(10), nullable=False, default="green")
    owner_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    data_inicio = db.Column(db.Date, nullable=True)
    data_fim_prevista = db.Column(db.Date, nullable=True)
    criado_em = db.Column(db.DateTime, default=utcnow)
    atualizado_em = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    owner = db.relationship("Usuario", foreign_keys=[owner_id], lazy="joined")
    areas = db.relationship("Area", secondary=projeto_area, lazy="selectin")
    sistemas = db.relationship("Sistema", secondary=projeto_sistema, back_populates="projetos", lazy="selectin")
    demandas = db.relationship("Demanda", backref="projeto", lazy="selectin")

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "fase": self.fase,
            "criticidade": self.criticidade,
            "status_rag": self.status_rag,
            "owner_id": self.owner_id,
            "owner_nome": self.owner.nome if self.owner else None,
            "data_inicio": self.data_inicio.isoformat() if self.data_inicio else None,
            "data_fim_prevista": self.data_fim_prevista.isoformat() if self.data_fim_prevista else None,
            "areas": [a.to_dict() for a in self.areas],
            "sistemas": [{"id": s.id, "nome": s.nome} for s in self.sistemas],
            "total_demandas": len(self.demandas),
        }


class Demanda(db.Model):
    __tablename__ = "demanda"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, default="")
    status_kanban = db.Column(db.String(20), nullable=False, default="nao_iniciado")
    prioridade = db.Column(db.String(20), nullable=False, default="media")
    responsavel_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    projeto_id = db.Column(db.Integer, db.ForeignKey("projeto.id"), nullable=True)
    sistema_id = db.Column(db.Integer, db.ForeignKey("sistema.id"), nullable=True)
    data_prazo = db.Column(db.Date, nullable=True)
    data_conclusao = db.Column(db.Date, nullable=True)
    ordem_kanban = db.Column(db.Integer, nullable=False, default=0)
    criado_em = db.Column(db.DateTime, default=utcnow)
    atualizado_em = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    responsavel = db.relationship("Usuario", foreign_keys=[responsavel_id], lazy="joined")
    sistema = db.relationship("Sistema", foreign_keys=[sistema_id], lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "status_kanban": self.status_kanban,
            "prioridade": self.prioridade,
            "responsavel_id": self.responsavel_id,
            "responsavel_nome": self.responsavel.nome if self.responsavel else None,
            "projeto_id": self.projeto_id,
            "projeto_nome": self.projeto.nome if self.projeto else None,
            "sistema_id": self.sistema_id,
            "sistema_nome": self.sistema.nome if self.sistema else None,
            "data_prazo": self.data_prazo.isoformat() if self.data_prazo else None,
            "data_conclusao": self.data_conclusao.isoformat() if self.data_conclusao else None,
            "ordem_kanban": self.ordem_kanban,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }


class Ativo(db.Model):
    __tablename__ = "ativo"
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(30), nullable=False, default="hardware")
    nome = db.Column(db.String(200), nullable=False)
    sistema_id = db.Column(db.Integer, db.ForeignKey("sistema.id"), nullable=True)
    numero_serie = db.Column(db.String(120), default="")
    chave_licenca = db.Column(db.String(200), default="")
    fabricante = db.Column(db.String(160), default="")
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default="estoque")
    responsavel_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)
    localizacao = db.Column(db.String(160), default="")
    data_aquisicao = db.Column(db.Date, nullable=True)
    data_expiracao = db.Column(db.Date, nullable=True)
    origem_importacao = db.Column(db.String(10), nullable=False, default="manual")
    criado_em = db.Column(db.DateTime, default=utcnow)
    atualizado_em = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    responsavel = db.relationship("Usuario", foreign_keys=[responsavel_id], lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "nome": self.nome,
            "sistema_id": self.sistema_id,
            "sistema_nome": self.sistema.nome if self.sistema else None,
            "numero_serie": self.numero_serie,
            "chave_licenca": self.chave_licenca,
            "fabricante": self.fabricante,
            "quantidade": self.quantidade,
            "status": self.status,
            "responsavel_id": self.responsavel_id,
            "responsavel_nome": self.responsavel.nome if self.responsavel else None,
            "localizacao": self.localizacao,
            "data_aquisicao": self.data_aquisicao.isoformat() if self.data_aquisicao else None,
            "data_expiracao": self.data_expiracao.isoformat() if self.data_expiracao else None,
            "origem_importacao": self.origem_importacao,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }


class Documento(db.Model):
    __tablename__ = "documento"
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(30), nullable=False, default="politica_ti")
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, default="")
    versao = db.Column(db.String(20), default="1.0")
    status_aprovacao = db.Column(db.String(20), nullable=False, default="rascunho")
    projeto_id = db.Column(db.Integer, db.ForeignKey("projeto.id"), nullable=True)
    sistema_id = db.Column(db.Integer, db.ForeignKey("sistema.id"), nullable=True)
    autor_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    arquivo_url = db.Column(db.String(400), default="")
    data_validade = db.Column(db.Date, nullable=True)
    criado_em = db.Column(db.DateTime, default=utcnow)
    atualizado_em = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    autor = db.relationship("Usuario", foreign_keys=[autor_id], lazy="joined")
    projeto = db.relationship("Projeto", foreign_keys=[projeto_id], lazy="joined")
    sistema = db.relationship("Sistema", foreign_keys=[sistema_id], lazy="joined")
    etapas = db.relationship(
        "EtapaAprovacao", backref="documento", lazy="selectin",
        order_by="EtapaAprovacao.ordem", cascade="all, delete-orphan",
    )
    assinaturas = db.relationship(
        "Assinatura", backref="documento", lazy="selectin", cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "versao": self.versao,
            "status_aprovacao": self.status_aprovacao,
            "projeto_id": self.projeto_id,
            "projeto_nome": self.projeto.nome if self.projeto else None,
            "sistema_id": self.sistema_id,
            "sistema_nome": self.sistema.nome if self.sistema else None,
            "autor_id": self.autor_id,
            "autor_nome": self.autor.nome if self.autor else None,
            "arquivo_url": self.arquivo_url,
            "data_validade": self.data_validade.isoformat() if self.data_validade else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
            "etapas": [e.to_dict() for e in self.etapas],
            "assinaturas": [a.to_dict() for a in self.assinaturas],
        }


class EtapaAprovacao(db.Model):
    __tablename__ = "etapa_aprovacao"
    id = db.Column(db.Integer, primary_key=True)
    documento_id = db.Column(db.Integer, db.ForeignKey("documento.id"), nullable=False)
    ordem = db.Column(db.Integer, nullable=False, default=1)
    aprovador_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pendente")
    comentario = db.Column(db.Text, default="")
    decidido_em = db.Column(db.DateTime, nullable=True)

    aprovador = db.relationship("Usuario", foreign_keys=[aprovador_id], lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "documento_id": self.documento_id,
            "ordem": self.ordem,
            "aprovador_id": self.aprovador_id,
            "aprovador_nome": self.aprovador.nome if self.aprovador else None,
            "status": self.status,
            "comentario": self.comentario,
            "decidido_em": self.decidido_em.isoformat() if self.decidido_em else None,
        }


class Assinatura(db.Model):
    __tablename__ = "assinatura"
    id = db.Column(db.Integer, primary_key=True)
    documento_id = db.Column(db.Integer, db.ForeignKey("documento.id"), nullable=False)
    signatario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)
    signatario_email = db.Column(db.String(160), default="")
    provedor = db.Column(db.String(20), nullable=False, default="docusign")
    id_externo = db.Column(db.String(200), default="")
    status = db.Column(db.String(20), nullable=False, default="pendente")
    url_assinatura = db.Column(db.String(400), default="")
    assinado_em = db.Column(db.DateTime, nullable=True)

    signatario = db.relationship("Usuario", foreign_keys=[signatario_id], lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "documento_id": self.documento_id,
            "signatario_id": self.signatario_id,
            "signatario_nome": self.signatario.nome if self.signatario else None,
            "signatario_email": self.signatario_email or (self.signatario.email if self.signatario else ""),
            "provedor": self.provedor,
            "id_externo": self.id_externo,
            "status": self.status,
            "url_assinatura": self.url_assinatura,
            "assinado_em": self.assinado_em.isoformat() if self.assinado_em else None,
        }


class HistoricoStatus(db.Model):
    __tablename__ = "historico_status"
    id = db.Column(db.Integer, primary_key=True)
    entidade_tipo = db.Column(db.String(20), nullable=False, index=True)
    entidade_id = db.Column(db.Integer, nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False)
    nota = db.Column(db.Text, default="")
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)
    criado_em = db.Column(db.DateTime, default=utcnow, index=True)

    usuario = db.relationship("Usuario", foreign_keys=[usuario_id], lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "entidade_tipo": self.entidade_tipo,
            "entidade_id": self.entidade_id,
            "status": self.status,
            "nota": self.nota,
            "usuario_nome": self.usuario.nome if self.usuario else None,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
        }


def log_status(entidade_tipo, entidade_id, status, usuario_id=None, nota=""):
    db.session.add(
        HistoricoStatus(
            entidade_tipo=entidade_tipo, entidade_id=entidade_id,
            status=status, usuario_id=usuario_id, nota=nota,
        )
    )
