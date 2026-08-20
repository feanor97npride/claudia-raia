STATUS_RAG = ["green", "amber", "red"]
STATUS_RAG_LABELS = {"green": "Verde", "amber": "Âmbar", "red": "Vermelho"}

STATUS_KANBAN = ["nao_iniciado", "em_andamento", "em_atraso", "concluido"]
STATUS_KANBAN_LABELS = {
    "nao_iniciado": "Não Iniciado",
    "em_andamento": "Em Andamento",
    "em_atraso": "Em Atraso",
    "concluido": "Concluído",
}

PRIORIDADES = ["critica", "alta", "media", "baixa"]
PRIORIDADE_LABELS = {"critica": "Crítica", "alta": "Alta", "media": "Média", "baixa": "Baixa"}

CRITICIDADES = PRIORIDADES
CRITICIDADE_LABELS = PRIORIDADE_LABELS

FASES_PROJETO = ["planejamento", "execucao", "homologacao", "implantacao", "encerrado"]
FASE_LABELS = {
    "planejamento": "Planejamento",
    "execucao": "Execução",
    "homologacao": "Homologação",
    "implantacao": "Implantação",
    "encerrado": "Encerrado",
}

PAPEIS_USUARIO = ["admin", "gestor_ti", "analista", "aprovador", "leitor"]
PAPEL_USUARIO_LABELS = {
    "admin": "Administrador", "gestor_ti": "Gestor de TI", "analista": "Analista",
    "aprovador": "Aprovador", "leitor": "Leitor",
}

CATEGORIAS_SISTEMA = ["aplicacao", "infraestrutura", "licenca"]
CATEGORIA_SISTEMA_LABELS = {
    "aplicacao": "Aplicação", "infraestrutura": "Infraestrutura", "licenca": "Licença",
}

AMBIENTES_SISTEMA = ["producao", "homologacao", "desenvolvimento"]

TIPOS_ATIVO = ["hardware", "licenca_software", "assinatura_saas"]
TIPO_ATIVO_LABELS = {
    "hardware": "Hardware", "licenca_software": "Licença de Software", "assinatura_saas": "Assinatura SaaS",
}

STATUS_ATIVO = ["em_uso", "estoque", "manutencao", "baixado"]
STATUS_ATIVO_LABELS = {
    "em_uso": "Em uso", "estoque": "Em estoque", "manutencao": "Em manutenção", "baixado": "Baixado",
}

ORIGEM_IMPORTACAO = ["manual", "xml"]

TIPOS_DOCUMENTO = ["politica_ti", "contrato", "termo_aditivo"]
TIPO_DOCUMENTO_LABELS = {
    "politica_ti": "Política de TI", "contrato": "Contrato", "termo_aditivo": "Termo Aditivo",
}

STATUS_APROVACAO_DOC = ["rascunho", "em_aprovacao", "aprovado", "rejeitado", "assinado"]
STATUS_APROVACAO_DOC_LABELS = {
    "rascunho": "Rascunho", "em_aprovacao": "Em Aprovação", "aprovado": "Aprovado",
    "rejeitado": "Rejeitado", "assinado": "Assinado",
}

STATUS_ETAPA = ["pendente", "aprovado", "rejeitado"]

PROVEDORES_ASSINATURA = ["docusign", "clicksign", "d4sign"]

STATUS_ASSINATURA = ["pendente", "enviado", "assinado", "recusado"]

ENTIDADES_HISTORICO = ["demanda", "projeto", "sistema", "documento", "ativo"]
