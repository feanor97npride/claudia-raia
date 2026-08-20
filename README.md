# Governança de TI

Sistema web para governança de sistemas, controle tático de projetos e gestão de ativos (ITAM/SAM),
substituindo o controle por planilhas manuais.

Módulos: **Demandas** (lista + Kanban), **Projetos**, **Sistemas**, **Inventário** (ITAM/SAM com
movimentação em massa e importação via XML), **Documentos** (políticas/contratos com fluxo de
aprovação e integração de assinatura digital preparada) e **Dashboard de KPIs**.

A proposta de arquitetura relacional (entidades, campos e relacionamentos) está documentada
separadamente e foi validada antes desta implementação.

## Estrutura

```
backend/    API Flask + SQLAlchemy (REST JSON em /api/*)
frontend/   SPA React (Vite)
Claudia Raia/app/   protótipo anterior (RAG Tracker em Flask + Jinja), mantido como referência
```

## Backend

```bash
cd backend
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python run.py    # http://127.0.0.1:5001 — cria o schema e popula dados de exemplo
```

Por padrão usa SQLite local (`backend/governanca_ti.db`). Em produção, defina a variável de
ambiente `DATABASE_URL` apontando para um Postgres gerenciado (ex.: Neon, Vercel Postgres) — o
SQLite em `/tmp` do protótipo anterior não persiste dados entre deploys serverless.

## Frontend

```bash
cd frontend
npm install
npm run dev    # http://127.0.0.1:5173 — proxy de /api para o backend em :5001
```

## Deploy (Vercel)

O `vercel.json` na raiz builda o backend como uma função Python (`backend/index.py`, via
`@vercel/python`) e o frontend como site estático (`frontend/`, via `@vercel/static-build`),
servidos no mesmo domínio: `/api/*` cai na função Flask, o restante serve o SPA React.

Passo pendente (só pode ser feito por quem tem acesso ao painel do Vercel do projeto):

1. Em **Storage → Postgres**, crie um banco Postgres e conecte-o ao projeto `claudia-raia`. Isso
   injeta automaticamente uma variável `POSTGRES_URL` (ou `DATABASE_URL`, dependendo da
   integração) nas env vars do projeto — o backend já lê as duas.
2. Faça um redeploy (ou aguarde o próximo push) para as env vars entrarem em vigor.
3. As tabelas são criadas automaticamente no primeiro request (`db.create_all()` no cold start).
   Não há seed automático em produção — o banco começa vazio.

Sem essa variável configurada, o backend cai de volta para SQLite em `/tmp`, que **não persiste**
entre deploys serverless — funciona para smoke test, não para uso real.

## Notas de arquitetura

- A coluna **Em Atraso** do Kanban é recalculada a cada carga da lista de demandas (promove
  itens vencidos de "não iniciado"/"em andamento"), simulando uma rotina diária.
- A importação de ativos por XML valida o arquivo linha a linha e rejeita `DOCTYPE`/`ENTITY` para
  evitar XXE; erros por item não interrompem a importação dos demais.
- A assinatura digital está com a modelagem (`assinatura`, `provedor`, `id_externo`) e o endpoint
  `/documentos/<id>/assinaturas/<id>/enviar` prontos para uma integração real (DocuSign, Clicksign,
  D4Sign) — hoje o envio é simulado (stub).
