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

## Notas de arquitetura

- A coluna **Em Atraso** do Kanban é recalculada a cada carga da lista de demandas (promove
  itens vencidos de "não iniciado"/"em andamento"), simulando uma rotina diária.
- A importação de ativos por XML valida o arquivo linha a linha e rejeita `DOCTYPE`/`ENTITY` para
  evitar XXE; erros por item não interrompem a importação dos demais.
- A assinatura digital está com a modelagem (`assinatura`, `provedor`, `id_externo`) e o endpoint
  `/documentos/<id>/assinaturas/<id>/enviar` prontos para uma integração real (DocuSign, Clicksign,
  D4Sign) — hoje o envio é simulado (stub).
