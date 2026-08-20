import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useMeta } from '../hooks/useMeta'
import { useToast } from '../hooks/useToast'
import { KanbanBadge, PriorityBadge } from '../components/Badges'
import DownloadLink from '../components/DownloadLink'
import ImportButton from '../components/ImportButton'
import KanbanBoard from '../components/KanbanBoard'
import Modal from '../components/Modal'

const BLANK = {
  titulo: '', descricao: '', prioridade: 'media', responsavel_id: '',
  projeto_id: '', sistema_id: '', data_prazo: '',
}

export default function DemandasPage() {
  const { meta, reload: reloadMeta } = useMeta()
  const showToast = useToast()
  const [demandas, setDemandas] = useState(null)
  const [view, setView] = useState('kanban')
  const [editing, setEditing] = useState(null)
  const [filters, setFilters] = useState({ status_kanban: '', responsavel_id: '' })

  const load = () => api.get('/demandas').then(setDemandas).catch((e) => showToast(e.message, 'error'))
  useEffect(() => { load() }, [])

  const save = async (form) => {
    try {
      if (form.id) {
        await api.put(`/demandas/${form.id}`, form)
        showToast('Demanda atualizada.')
      } else {
        await api.post('/demandas', form)
        showToast('Demanda criada.')
      }
      setEditing(null)
      load()
      reloadMeta()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const remove = async (id) => {
    if (!confirm('Excluir esta demanda?')) return
    await api.del(`/demandas/${id}`)
    showToast('Demanda excluída.')
    setEditing(null)
    load()
  }

  const onBoardChange = async (columns) => {
    setDemandas((prev) => {
      const byId = Object.fromEntries(prev.map((d) => [d.id, d]))
      const next = [...prev]
      for (const [status, ids] of Object.entries(columns)) {
        ids.forEach((id, index) => {
          const item = byId[id]
          if (item) {
            item.status_kanban = status
            item.ordem_kanban = index
          }
        })
      }
      return next
    })
    try {
      await api.put('/demandas/kanban-batch', { columns })
    } catch (e) {
      showToast(e.message, 'error')
      load()
    }
  }

  const visible = (demandas || []).filter((d) => {
    if (filters.status_kanban && d.status_kanban !== filters.status_kanban) return false
    if (filters.responsavel_id && String(d.responsavel_id) !== filters.responsavel_id) return false
    return true
  })

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="kicker">Gestão visual</div>
          <h1>Demandas</h1>
          <div className="subtitle">Board Kanban e lista das tarefas táticas de TI.</div>
        </div>
        <div className="actions">
          <div className="view-toggle">
            <button className={view === 'kanban' ? 'active' : ''} onClick={() => setView('kanban')}>Kanban</button>
            <button className={view === 'lista' ? 'active' : ''} onClick={() => setView('lista')}>Lista</button>
          </div>
          <DownloadLink path="/demandas/exportar" label="⇩ Exportar lista" />
          <DownloadLink path="/demandas/modelo-planilha" label="⇩ Baixar modelo" />
          <ImportButton
            endpoint="/demandas/import-planilha"
            label="Importar planilha"
            hint="Colunas: título, descrição, prioridade, responsável (nome/e-mail já cadastrado), projeto, sistema, prazo, status"
            onDone={load}
          />
          <button className="btn primary" onClick={() => setEditing({ ...BLANK })}>+ Nova demanda</button>
        </div>
      </div>

      {view === 'lista' && (
        <div className="filters-row">
          <select value={filters.status_kanban} onChange={(e) => setFilters({ ...filters, status_kanban: e.target.value })}>
            <option value="">Todos os status</option>
            {meta.enums.status_kanban.map((s) => (
              <option key={s} value={s}>{meta.enums.status_kanban_labels[s]}</option>
            ))}
          </select>
          <select value={filters.responsavel_id} onChange={(e) => setFilters({ ...filters, responsavel_id: e.target.value })}>
            <option value="">Todos os responsáveis</option>
            {meta.usuarios.map((u) => (
              <option key={u.id} value={u.id}>{u.nome}</option>
            ))}
          </select>
        </div>
      )}

      {!demandas && <div className="spinner-text">Carregando…</div>}

      {demandas && view === 'kanban' && (
        <KanbanBoard demandas={demandas} onBoardChange={onBoardChange} onOpen={setEditing} />
      )}

      {demandas && view === 'lista' && (
        <div className="card table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Demanda</th>
                <th>Status</th>
                <th>Prioridade</th>
                <th>Responsável</th>
                <th>Projeto / Sistema</th>
                <th>Prazo</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {visible.map((d) => (
                <tr key={d.id}>
                  <td><strong>{d.titulo}</strong></td>
                  <td><KanbanBadge status={d.status_kanban} /></td>
                  <td><PriorityBadge prioridade={d.prioridade} /></td>
                  <td>{d.responsavel_nome}</td>
                  <td>{[d.projeto_nome, d.sistema_nome].filter(Boolean).join(' · ') || '—'}</td>
                  <td>{d.data_prazo || '—'}</td>
                  <td><button className="btn small" onClick={() => setEditing(d)}>Editar</button></td>
                </tr>
              ))}
              {visible.length === 0 && (
                <tr><td colSpan={7} className="empty-state">Nenhuma demanda encontrada.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <Modal title={editing.id ? 'Editar demanda' : 'Nova demanda'} onClose={() => setEditing(null)} width={600}>
          <DemandaForm initial={editing} meta={meta} onCancel={() => setEditing(null)} onSave={save} onDelete={editing.id ? () => remove(editing.id) : null} />
        </Modal>
      )}
    </div>
  )
}

function DemandaForm({ initial, meta, onCancel, onSave, onDelete }) {
  const [form, setForm] = useState(initial)
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSave(form) }}>
      <div className="form-grid">
        <div className="form-field full">
          <label>Título</label>
          <input required value={form.titulo} onChange={set('titulo')} />
        </div>
        <div className="form-field full">
          <label>Descrição</label>
          <textarea rows={2} value={form.descricao} onChange={set('descricao')} />
        </div>
        <div className="form-field">
          <label>Prioridade</label>
          <select value={form.prioridade} onChange={set('prioridade')}>
            {meta.enums.prioridades.map((p) => (
              <option key={p} value={p}>{meta.enums.prioridade_labels[p]}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Responsável</label>
          <select required value={form.responsavel_id} onChange={set('responsavel_id')}>
            <option value="">Selecione…</option>
            {meta.usuarios.map((u) => (
              <option key={u.id} value={u.id}>{u.nome}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Projeto (opcional)</label>
          <select value={form.projeto_id || ''} onChange={set('projeto_id')}>
            <option value="">Nenhum</option>
            {meta.projetos.map((p) => (
              <option key={p.id} value={p.id}>{p.nome}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Sistema (opcional)</label>
          <select value={form.sistema_id || ''} onChange={set('sistema_id')}>
            <option value="">Nenhum</option>
            {meta.sistemas.map((s) => (
              <option key={s.id} value={s.id}>{s.nome}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Prazo</label>
          <input type="date" value={form.data_prazo || ''} onChange={set('data_prazo')} />
        </div>
        {form.id && (
          <div className="form-field">
            <label>Status Kanban</label>
            <select value={form.status_kanban} onChange={set('status_kanban')}>
              {meta.enums.status_kanban.map((s) => (
                <option key={s} value={s}>{meta.enums.status_kanban_labels[s]}</option>
              ))}
            </select>
          </div>
        )}
      </div>
      <div className="form-actions">
        {onDelete && <button type="button" className="btn danger" style={{ marginRight: 'auto' }} onClick={onDelete}>Excluir</button>}
        <button type="button" className="btn" onClick={onCancel}>Cancelar</button>
        <button type="submit" className="btn primary">Salvar</button>
      </div>
    </form>
  )
}
