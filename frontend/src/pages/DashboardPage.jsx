import { useEffect, useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { api } from '../api/client'
import { useMeta } from '../hooks/useMeta'
import { useToast } from '../hooks/useToast'
import './DashboardPage.css'

const CRITICIDADE_COLORS = { critica: '#d43f3f', alta: '#c98a05', media: '#4a63b3', baixa: '#838da3' }
const RAG_COLORS = { green: '#1e9e5a', amber: '#c98a05', red: '#d43f3f' }
const KANBAN_COLORS = { nao_iniciado: '#838da3', em_andamento: '#c98a05', em_atraso: '#d43f3f', concluido: '#1e9e5a' }
const AREA_COLORS = ['#0e7c86', '#3fa8ad', '#7fc6c6', '#155a63', '#a9dcd8', '#4a63b3']

function StatTile({ label, value, tone }) {
  return (
    <div className={`stat-tile${tone ? ` tone-${tone}` : ''}`}>
      <div className="stat-tile-value">{value}</div>
      <div className="stat-tile-label">{label}</div>
    </div>
  )
}

export default function DashboardPage() {
  const { meta } = useMeta()
  const showToast = useToast()
  const [kpis, setKpis] = useState(null)

  useEffect(() => {
    api.get('/dashboard/kpis').then(setKpis).catch((e) => showToast(e.message, 'error'))
  }, [])

  if (!kpis) return <div className="spinner-text">Carregando indicadores…</div>

  const criticidadeData = meta.enums.prioridades.map((p) => ({
    key: p, label: meta.enums.prioridade_labels[p], total: kpis.projetos_por_criticidade[p] || 0,
  }))
  const kanbanData = meta.enums.status_kanban.map((s) => ({
    key: s, label: meta.enums.status_kanban_labels[s], total: kpis.demandas_por_status[s] || 0,
  }))
  const areaData = kpis.projetos_por_area.filter((a) => a.total > 0)
  const ragData = meta.enums.status_rag
    .map((s) => ({ key: s, label: meta.enums.status_rag_labels[s], total: kpis.sistemas_por_status_rag[s] || 0 }))
    .filter((d) => d.total > 0)

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="kicker">Painel executivo</div>
          <h1>Dashboard de KPIs</h1>
          <div className="subtitle">Volume de projetos por criticidade, área impactada e prazos.</div>
        </div>
      </div>

      <div className="stat-grid">
        <StatTile label="Projetos ativos" value={kpis.projetos_total} />
        <StatTile label="Demandas em atraso" value={kpis.demandas_atrasadas} tone={kpis.demandas_atrasadas > 0 ? 'red' : 'green'} />
        <StatTile label="Vencendo em 7 dias" value={kpis.demandas_vencendo_7_dias} tone={kpis.demandas_vencendo_7_dias > 0 ? 'amber' : 'green'} />
        <StatTile label="Documentos p/ aprovar" value={kpis.documentos_pendentes_aprovacao} tone={kpis.documentos_pendentes_aprovacao > 0 ? 'amber' : 'green'} />
        <StatTile label="Ativos no inventário" value={kpis.total_ativos} />
      </div>

      <div className="chart-grid">
        <div className="card chart-card">
          <h3>Projetos por criticidade</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={criticidadeData} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 12, fill: 'var(--ink-600)' }} axisLine={{ stroke: 'var(--line)' }} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: 'var(--ink-600)' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ fontSize: 12.5, borderRadius: 8, border: '1px solid var(--line)' }} />
              <Bar dataKey="total" radius={[5, 5, 0, 0]} maxBarSize={54}>
                {criticidadeData.map((d) => <Cell key={d.key} fill={CRITICIDADE_COLORS[d.key]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card chart-card">
          <h3>Projetos por área impactada</h3>
          {areaData.length === 0 ? (
            <div className="empty-state">Nenhuma área vinculada a projetos ainda.</div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={areaData} dataKey="total" nameKey="area" innerRadius={56} outerRadius={88} paddingAngle={2}>
                  {areaData.map((d, i) => <Cell key={d.area} fill={AREA_COLORS[i % AREA_COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ fontSize: 12.5, borderRadius: 8, border: '1px solid var(--line)' }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card chart-card">
          <h3>Demandas por status (Kanban)</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={kanbanData} layout="vertical" margin={{ top: 8, right: 20, left: 12, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" horizontal={false} />
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: 'var(--ink-600)' }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="label" width={110} tick={{ fontSize: 12, fill: 'var(--ink-600)' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ fontSize: 12.5, borderRadius: 8, border: '1px solid var(--line)' }} />
              <Bar dataKey="total" radius={[0, 5, 5, 0]} maxBarSize={26}>
                {kanbanData.map((d) => <Cell key={d.key} fill={KANBAN_COLORS[d.key]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card chart-card">
          <h3>Sistemas por status RAG</h3>
          {ragData.length === 0 ? (
            <div className="empty-state">Nenhum sistema cadastrado ainda.</div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={ragData} dataKey="total" nameKey="label" innerRadius={56} outerRadius={88} paddingAngle={2}>
                  {ragData.map((d) => <Cell key={d.key} fill={RAG_COLORS[d.key]} />)}
                </Pie>
                <Tooltip contentStyle={{ fontSize: 12.5, borderRadius: 8, border: '1px solid var(--line)' }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}
