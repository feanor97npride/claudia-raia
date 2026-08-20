from datetime import date, timedelta

from .extensions import db
from .models import (
    Area, Ativo, Assinatura, Demanda, Documento, EtapaAprovacao,
    Projeto, Sistema, Usuario, log_status,
)


def seed_data():
    if Usuario.query.count() > 0:
        print("Banco já possui dados, seed ignorado.")
        return

    infra = Area(nome="Infraestrutura", sigla="INFRA")
    apps = Area(nome="Aplicações", sigla="APPS")
    seguranca = Area(nome="Segurança da Informação", sigla="SEC")
    negocio = Area(nome="Áreas de Negócio", sigla="NEG")
    db.session.add_all([infra, apps, seguranca, negocio])
    db.session.flush()

    marina = Usuario(nome="Marina Duarte", email="marina.duarte@empresa.com", area_id=infra.id, papel="gestor_ti")
    caio = Usuario(nome="Caio Ferreira", email="caio.ferreira@empresa.com", area_id=apps.id, papel="analista")
    julia = Usuario(nome="Júlia Nakamura", email="julia.nakamura@empresa.com", area_id=seguranca.id, papel="aprovador")
    rafael = Usuario(nome="Rafael Prado", email="rafael.prado@empresa.com", area_id=infra.id, papel="analista")
    beatriz = Usuario(nome="Beatriz Lins", email="beatriz.lins@empresa.com", area_id=apps.id, papel="gestor_ti")
    admin = Usuario(nome="Administrador TI", email="admin@empresa.com", papel="admin")
    db.session.add_all([marina, caio, julia, rafael, beatriz, admin])
    db.session.flush()

    sap = Sistema(
        nome="SAP ECC (Produção)", descricao="Ambiente produtivo SAP legado.",
        categoria="aplicacao", criticidade="critica", ambiente="producao",
        fornecedor="SAP", owner_id=marina.id, status_rag="amber",
        data_fim_suporte=date(2027, 12, 31),
    )
    crm = Sistema(
        nome="CRM Salesforce", descricao="Plataforma comercial em rollout.",
        categoria="aplicacao", criticidade="alta", ambiente="producao",
        fornecedor="Salesforce", owner_id=beatriz.id, status_rag="green",
    )
    intranet = Sistema(
        nome="Portal Corporativo Intranet", descricao="Portal interno de comunicação.",
        categoria="aplicacao", criticidade="alta", ambiente="producao",
        fornecedor="Interno", owner_id=caio.id, status_rag="green",
    )
    exchange = Sistema(
        nome="Servidor de E-mail Exchange", descricao="Cluster de e-mail corporativo.",
        categoria="infraestrutura", criticidade="critica", ambiente="producao",
        fornecedor="Microsoft", owner_id=rafael.id, status_rag="red",
    )
    db.session.add_all([sap, crm, intranet, exchange])
    db.session.flush()

    erp = Projeto(
        nome="Migração ERP SAP S/4HANA", descricao="Migração do SAP ECC para S/4HANA.",
        fase="execucao", criticidade="critica", status_rag="amber", owner_id=marina.id,
        data_inicio=date.today() - timedelta(days=90), data_fim_prevista=date.today() + timedelta(days=45),
    )
    erp.areas = [infra, negocio]
    erp.sistemas = [sap]

    crm_proj = Projeto(
        nome="Implantação CRM Salesforce", descricao="Rollout do novo CRM para a equipe comercial.",
        fase="homologacao", criticidade="alta", status_rag="green", owner_id=beatriz.id,
        data_inicio=date.today() - timedelta(days=60), data_fim_prevista=date.today() + timedelta(days=20),
    )
    crm_proj.areas = [apps, negocio]
    crm_proj.sistemas = [crm]

    datacenter = Projeto(
        nome="Renovação Datacenter", descricao="Substituição de servidores físicos end-of-life.",
        fase="planejamento", criticidade="alta", status_rag="red", owner_id=rafael.id,
        data_inicio=date.today() - timedelta(days=30), data_fim_prevista=date.today() - timedelta(days=5),
    )
    datacenter.areas = [infra]
    datacenter.sistemas = [exchange]

    db.session.add_all([erp, crm_proj, datacenter])
    db.session.flush()

    demandas = [
        Demanda(titulo="Homologar módulo financeiro S/4HANA", prioridade="critica",
                responsavel_id=marina.id, projeto_id=erp.id, sistema_id=sap.id,
                status_kanban="em_andamento", ordem_kanban=0,
                data_prazo=date.today() + timedelta(days=10)),
        Demanda(titulo="Migrar base de fornecedores", prioridade="alta",
                responsavel_id=rafael.id, projeto_id=erp.id, sistema_id=sap.id,
                status_kanban="nao_iniciado", ordem_kanban=0,
                data_prazo=date.today() + timedelta(days=25)),
        Demanda(titulo="Corrigir integração de pedidos CRM x ERP", prioridade="alta",
                responsavel_id=caio.id, projeto_id=crm_proj.id, sistema_id=crm.id,
                status_kanban="em_atraso", ordem_kanban=0,
                data_prazo=date.today() - timedelta(days=3)),
        Demanda(titulo="Treinamento da equipe comercial no CRM", prioridade="media",
                responsavel_id=beatriz.id, projeto_id=crm_proj.id,
                status_kanban="concluido", ordem_kanban=0,
                data_prazo=date.today() - timedelta(days=15), data_conclusao=date.today() - timedelta(days=12)),
        Demanda(titulo="Cotar servidores de substituição", prioridade="critica",
                responsavel_id=rafael.id, projeto_id=datacenter.id,
                status_kanban="em_atraso", ordem_kanban=1,
                data_prazo=date.today() - timedelta(days=8)),
        Demanda(titulo="Investigar instabilidade recorrente no Exchange", prioridade="critica",
                responsavel_id=rafael.id, sistema_id=exchange.id,
                status_kanban="em_andamento", ordem_kanban=1,
                data_prazo=date.today() + timedelta(days=2)),
        Demanda(titulo="Atualizar runbook do Portal Intranet", prioridade="baixa",
                responsavel_id=caio.id, sistema_id=intranet.id,
                status_kanban="nao_iniciado", ordem_kanban=1,
                data_prazo=date.today() + timedelta(days=40)),
        Demanda(titulo="Revisar política de backup do datacenter", prioridade="media",
                responsavel_id=julia.id, projeto_id=datacenter.id,
                status_kanban="concluido", ordem_kanban=1,
                data_prazo=date.today() - timedelta(days=20), data_conclusao=date.today() - timedelta(days=18)),
    ]
    db.session.add_all(demandas)
    db.session.flush()
    for demanda in demandas:
        log_status("demanda", demanda.id, demanda.status_kanban, usuario_id=demanda.responsavel_id, nota="Demanda criada (seed).")

    ativos = [
        Ativo(tipo="hardware", nome="Notebook Dell Latitude 5420", sistema_id=None,
              numero_serie="DL5420-0012", fabricante="Dell", quantidade=1, status="em_uso",
              responsavel_id=caio.id, localizacao="Matriz SP - 4º andar",
              data_aquisicao=date.today() - timedelta(days=400), origem_importacao="manual"),
        Ativo(tipo="hardware", nome="Servidor Rack PowerEdge R740", sistema_id=exchange.id,
              numero_serie="PE-R740-081", fabricante="Dell", quantidade=1, status="manutencao",
              responsavel_id=rafael.id, localizacao="Datacenter SP - Rack 12",
              data_aquisicao=date.today() - timedelta(days=1500), origem_importacao="manual"),
        Ativo(tipo="licenca_software", nome="Licenças SAP ECC (usuários nomeados)", sistema_id=sap.id,
              chave_licenca="SAP-LIC-2200X", fabricante="SAP", quantidade=250, status="em_uso",
              responsavel_id=marina.id, data_expiracao=date(2027, 12, 31), origem_importacao="xml"),
        Ativo(tipo="assinatura_saas", nome="Salesforce Sales Cloud", sistema_id=crm.id,
              fabricante="Salesforce", quantidade=80, status="em_uso",
              responsavel_id=beatriz.id, data_expiracao=date.today() + timedelta(days=200),
              origem_importacao="xml"),
        Ativo(tipo="hardware", nome="Notebook Lenovo ThinkPad T14 (estoque)", sistema_id=None,
              numero_serie="TP-T14-0099", fabricante="Lenovo", quantidade=3, status="estoque",
              localizacao="Matriz SP - Almoxarifado TI", origem_importacao="manual"),
        Ativo(tipo="licenca_software", nome="Microsoft 365 E3", sistema_id=exchange.id,
              chave_licenca="M365-E3-CORP", fabricante="Microsoft", quantidade=420, status="em_uso",
              responsavel_id=rafael.id, data_expiracao=date.today() + timedelta(days=90),
              origem_importacao="xml"),
    ]
    db.session.add_all(ativos)

    politica_seguranca = Documento(
        tipo="politica_ti", titulo="Política de Controle de Acesso", versao="2.1",
        status_aprovacao="em_aprovacao", autor_id=julia.id, sistema_id=None,
        descricao="Regras de concessão e revisão periódica de acessos a sistemas corporativos.",
    )
    contrato_dc = Documento(
        tipo="contrato", titulo="Contrato de Colocation — Datacenter SP", versao="1.0",
        status_aprovacao="aprovado", autor_id=marina.id, projeto_id=datacenter.id,
        descricao="Renovação do contrato de colocation para os novos racks.",
        data_validade=date.today() + timedelta(days=700),
    )
    aditivo_sap = Documento(
        tipo="termo_aditivo", titulo="Aditivo de Suporte SAP — Ano 2", versao="1.0",
        status_aprovacao="rascunho", autor_id=marina.id, projeto_id=erp.id, sistema_id=sap.id,
        descricao="Extensão do contrato de suporte SAP para o segundo ano do projeto.",
    )
    db.session.add_all([politica_seguranca, contrato_dc, aditivo_sap])
    db.session.flush()

    db.session.add_all([
        EtapaAprovacao(documento_id=politica_seguranca.id, ordem=1, aprovador_id=marina.id, status="aprovado",
                       comentario="De acordo.", decidido_em=None),
        EtapaAprovacao(documento_id=politica_seguranca.id, ordem=2, aprovador_id=beatriz.id, status="pendente"),
        EtapaAprovacao(documento_id=contrato_dc.id, ordem=1, aprovador_id=julia.id, status="aprovado"),
        EtapaAprovacao(documento_id=aditivo_sap.id, ordem=1, aprovador_id=marina.id, status="pendente"),
    ])

    db.session.add(
        Assinatura(documento_id=contrato_dc.id, signatario_id=marina.id, provedor="clicksign",
                   status="assinado", id_externo="stub-demo-0001",
                   url_assinatura="https://exemplo-clicksign.invalid/assinar/stub-demo-0001")
    )

    db.session.commit()

    for it in [sap, crm, intranet, exchange]:
        log_status("sistema", it.id, it.status_rag, usuario_id=it.owner_id, nota="Sistema cadastrado (seed).")
    for it in [erp, crm_proj, datacenter]:
        log_status("projeto", it.id, it.status_rag, usuario_id=it.owner_id, nota="Projeto criado (seed).")
    db.session.commit()

    print(f"Seed concluído: {len(demandas)} demandas, {len(ativos)} ativos, 3 documentos, 4 sistemas, 3 projetos, 6 usuários.")


if __name__ == "__main__":
    from . import create_app

    app = create_app()
    with app.app_context():
        seed_data()
