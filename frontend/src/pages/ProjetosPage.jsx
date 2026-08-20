import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useMeta } from '../hooks/useMeta'
import { useToast } from '../hooks/useToast'
import { RagBadge } from '../components/Badges'
import ImportButton from '../components/ImportButton'
import Modal from '../components/Modal'

const BLANK = {
  nome: '', descricao: '', fase: 'planejamento', criticidade: 'media', status_rag: 'green',
  owner_id: '', data_inicio: '', data_fim_prevista: '', area_ids: [], sistema_ids: [],
}

export default function ProjetosPage() {
  const { meta, reload: reloadMeta } = useMeta()
  const showToast = useToast()
  const [projetos, setProjetos] = useState(null)
  const [editing, setEditing] = useState(null)

  const load = () => api.get('/projetos').then(setProjetos).catch((e) => showToast(e.message, 'error'))
  useEffect(() => { load() }, [])

  const save = async (form) => {
    try {
      if (form.id) {
        await api.put(`/projetos/${form.id}`, form)
        showToast('Projeto atualizado.')
      } else {
        await api.post('/projetos', form)
        showToast('Projeto criado.')
      }
      setEditing(null)
      load()
      reloadMeta()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const remove = async (id) => {
    if (!confirm('Excluir este projeto? Esta ação não pode ser desfeita.')) return
    await api.del(`/projetos/${id}`)
    showToast('Projeto excluído.')
    load()
    reloadMeta()
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="kicker">Controle tático</div>
          <h1>Projetos</h1>
          <div className="subtitle">Fase, criticidade e status RAG dos projetos em andamento.</div>
        </div>
        <div className="actions">
          <ImportButton
            endpoint="/projetos/import-planilha"
            label="Importar planilha"
            hint="Colunas: nome, descrição, fase, criticidade, status RAG, responsável (nome/e-mail já cadastrado), data início, data fim prevista"
            onDone={() => { load(); reloadMeta() }}
          />
          <button className="btn primary" onClick={() => setEditing({ ...BLANK })}>
            + Novo projeto
          </button>
        </div>
      </div>

      <div className="card table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Projeto</th>
              <th>Fase</th>
              <th>Criticidade</th>
              <th>RAG</th>
              <th>Responsável</th>
              <th>Prazo</th>
              <th>Demandas</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {projetos?.map((p) => (
              <tr key={p.id}>
                <td>
                  <strong>{p.nome}</strong>
                  {p.areas.length > 0 && (
                    <div style={{ fontSize: 12, color: 'var(--ink-400)', marginTop: 2 }}>
                      {p.areas.map((a) => a.sigla || a.nome).join(' · ')}
                    </div>
                  )}
                </td>
                <td>{meta.enums.fase_labels[p.fase]}</td>
                <td>{meta.enums.prioridade_labels[p.criticidade]}</td>
                <td><RagBadge status={p.status_rag} /></td>
                <td>{p.owner_nome}</td>
                <td>{p.data_fim_prevista || '—'}</td>
                <td>{p.total_demandas}</td>
                <td>
                  <button className="btn small" onClick={() => setEditing({ ...p, area_ids: p.areas.map((a) => a.id), sistema_ids: p.sistemas.map((s) => s.id) })}>
                    Editar
                  </button>{' '}
                  <button className="btn small danger" onClick={() => remove(p.id)}>
                    Excluir
                  </button>
                </td>
              </tr>
            ))}
            {projetos?.length === 0 && (
              <tr>
                <td colSpan={8} className="empty-state">Nenhum projeto cadastrado ainda.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {editing && (
        <Modal title={editing.id ? 'Editar projeto' : 'Novo projeto'} onClose={() => setEditing(null)} width={640}>
          <ProjetoForm initial={editing} meta={meta} onCancel={() => setEditing(null)} onSave={save} />
        </Modal>
      )}
    </div>
  )
}

function ProjetoForm({ initial, meta, onCancel, onSave }) {
  const [form, setForm] = useState(initial)
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })
  const toggleMulti = (field, id) => {
    const current = form[field] || []
    setForm({ ...form, [field]: current.includes(id) ? current.filter((x) => x !== id) : [...current, id] })
  }

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSave(form) }}>
      <div className="form-grid">
        <div className="form-field full">
          <label>Nome</label>
          <input required value={form.nome} onChange={set('nome')} />
        </div>
        <div className="form-field full">
          <label>Descrição</label>
          <textarea rows={2} value={form.descricao} onChange={set('descricao')} />
        </div>
        <div className="form-field">
          <label>Fase</label>
          <select value={form.fase} onChange={set('fase')}>
            {meta.enums.fases_projeto.map((f) => (
              <option key={f} value={f}>{meta.enums.fase_labels[f]}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Criticidade</label>
          <select value={form.criticidade} onChange={set('criticidade')}>
            {meta.enums.prioridades.map((p) => (
              <option key={p} value={p}>{meta.enums.prioridade_labels[p]}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Status RAG</label>
          <select value={form.status_rag} onChange={set('status_rag')}>
            {meta.enums.status_rag.map((s) => (
              <option key={s} value={s}>{meta.enums.status_rag_labels[s]}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Responsável (owner)</label>
          <select required value={form.owner_id} onChange={set('owner_id')}>
            <option value="">Selecione…</option>
            {meta.usuarios.map((u) => (
              <option key={u.id} value={u.id}>{u.nome}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Início</label>
          <input type="date" value={form.data_inicio || ''} onChange={set('data_inicio')} />
        </div>
        <div className="form-field">
          <label>Fim previsto</label>
          <input type="date" value={form.data_fim_prevista || ''} onChange={set('data_fim_prevista')} />
        </div>
        <div className="form-field full">
          <label>Áreas impactadas</label>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {meta.areas.map((a) => (
              <label key={a.id} style={{ display: 'flex', gap: 5, alignItems: 'center', fontSize: 13, fontWeight: 400 }}>
                <input type="checkbox" checked={(form.area_ids || []).includes(a.id)} onChange={() => toggleMulti('area_ids', a.id)} />
                {a.nome}
              </label>
            ))}
          </div>
        </div>
        <div className="form-field full">
          <label>Sistemas envolvidos</label>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {meta.sistemas.map((s) => (
              <label key={s.id} style={{ display: 'flex', gap: 5, alignItems: 'center', fontSize: 13, fontWeight: 400 }}>
                <input type="checkbox" checked={(form.sistema_ids || []).includes(s.id)} onChange={() => toggleMulti('sistema_ids', s.id)} />
                {s.nome}
              </label>
            ))}
          </div>
        </div>
      </div>
      <div className="form-actions">
        <button type="button" className="btn" onClick={onCancel}>Cancelar</button>
        <button type="submit" className="btn primary">Salvar</button>
      </div>
    </form>
  )
}
