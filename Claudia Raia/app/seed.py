from datetime import date, timedelta


def seed_data(db, Item, StatusHistory):
    if Item.query.count() > 0:
        print("Banco já possui dados, seed ignorado.")
    else:
        items = [
            Item(entity_type="projects", name="Migração ERP SAP S/4HANA", owner="Time Infra",
                 category="Execução", status="amber",
                 description="Migração do ambiente SAP ECC para S/4HANA.",
                 due_date=date.today() + timedelta(days=45),
                 metric_label="Progresso (%)", metric_value=62, metric_target=100),
            Item(entity_type="projects", name="Implantação CRM Salesforce", owner="Time Aplicações",
                 category="Homologação", status="green",
                 description="Rollout do novo CRM para equipe comercial.",
                 due_date=date.today() + timedelta(days=20),
                 metric_label="Progresso (%)", metric_value=88, metric_target=100),
            Item(entity_type="projects", name="Renovação Datacenter", owner="Time Infra",
                 category="Planejamento", status="red",
                 description="Substituição de servidores físicos end-of-life.",
                 due_date=date.today() - timedelta(days=5),
                 metric_label="Progresso (%)", metric_value=15, metric_target=100),

            Item(entity_type="systems", name="Portal Corporativo Intranet", owner="Time Web",
                 category="Alta", status="green",
                 description="Portal interno de comunicação e serviços.",
                 metric_label="Uptime (%)", metric_value=99.8, metric_target=99.9),
            Item(entity_type="systems", name="SAP ECC (Produção)", owner="Time Infra",
                 category="Crítica", status="amber",
                 description="Ambiente produtivo SAP legado.",
                 metric_label="Uptime (%)", metric_value=98.2, metric_target=99.9),
            Item(entity_type="systems", name="Servidor de E-mail Exchange", owner="Time Infra",
                 category="Crítica", status="red",
                 description="Instabilidade recorrente no cluster de e-mail.",
                 metric_label="Uptime (%)", metric_value=94.1, metric_target=99.9),

            Item(entity_type="kpis", name="SLA Atendimento Help Desk", owner="Service Desk",
                 category="Atendimento", status="green",
                 description="Percentual de chamados atendidos dentro do SLA.",
                 metric_label="% dentro do SLA", metric_value=96, metric_target=95),
            Item(entity_type="kpis", name="Tickets Críticos Abertos", owner="Service Desk",
                 category="Disponibilidade", status="amber",
                 description="Volume de incidentes críticos em aberto.",
                 metric_label="Qtd. tickets", metric_value=7, metric_target=3),

            Item(entity_type="risks", name="Fim de suporte Windows Server 2012", owner="Time Infra",
                 category="Alta", status="red",
                 description="Servidores legados sem suporte de segurança do fabricante.",
                 due_date=date.today() + timedelta(days=10),
                 metric_label="Exposição", metric_value=8, metric_target=2),
            Item(entity_type="risks", name="Dependência de fornecedor único (backup)", owner="Time Infra",
                 category="Média", status="amber",
                 description="Solução de backup depende de um único fornecedor.",
                 due_date=date.today() + timedelta(days=90),
                 metric_label="Exposição", metric_value=5, metric_target=2),
        ]
        db.session.add_all(items)
        db.session.flush()
        for it in items:
            db.session.add(StatusHistory(item_id=it.id, status=it.status, note="Item criado (seed).", changed_by=it.owner))
        db.session.commit()
        print(f"{len(items)} itens de exemplo criados.")


if __name__ == "__main__":
    from app import app, db, Item, StatusHistory
    with app.app_context():
        seed_data(db, Item, StatusHistory)
