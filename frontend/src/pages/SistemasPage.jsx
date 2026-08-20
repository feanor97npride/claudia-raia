import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useMeta } from '../hooks/useMeta'
import { useToast } from '../hooks/useToast'
import { RagBadge } from '../components/Badges'
import ImportButton from '../components/ImportButton'
import Modal from '../components/Modal'

const BLANK = {
  nome: '', descricao: '', categoria: 'aplicacao', criticidade: 'media', ambiente: 'producao',
  fornecedor: '', owner_id: '', status_rag: 'green', data_fim_suporte: '',
}

export default function SistemasPage() {
  const { meta, reload: reloadMeta } = useMeta()
  const showToast = useToast()
  const [sistemas, setSistemas] = useState(null)
  const [editing, setEditing] = useState(null)

  const load = () => api.get('/sistemas').then(setSistemas).catch((e) => showToast(e.message, 'error'))
  useEffect(() => { load() }, [])

  const save = async (form) => {
    try {
      if (form.id) {
        await api.put(`/sistemas/${form.id}`, form)
        showToast('Sistema atualizado.')
      } else {
        await api.post('/sistemas', form)
        showToast('Sistema cadastrado.')
      }
      setEditing(null)
      load()
      reloadMeta()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const remove = async (id) => {
    if (!confirm('Excluir este sistema? Ativos e demandas vinculados perderão a referência.')) return
    await api.del(`/sistemas/${id}`)
    showToast('Sistema excluído.')
    load()
    reloadMeta()
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="kicker">Inventário &middot; base ITAM</div>
          <h1>Sistemas &amp; Aplicações</h1>
          <div className="subtitle">Catálogo de aplicações corporativas — base do inventário e das demandas.</div>
        </div>
        <div className="actions">
          <ImportButton
            endpoint="/sistemas/import-planilha"
            label="Importar planilha"
            hint="Colunas: nome, descrição, categoria, criticidade, ambiente, status RAG, fornecedor, responsável (nome/e-mail já cadastrado), fim de suporte"
            onDone={() => { load(); reloadMeta() }}
          />
          <button className="btn primary" onClick={() => setEditing({ ...BLANK })}>
            + Novo sistema
          </button>
        </div>
      </div>

      <div className="card table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Sistema</th>
              <th>Categoria</th>
              <th>Criticidade</th>
              <th>Ambiente</th>
              <th>RAG</th>
              <th>Responsável</th>
              <th>Fim de suporte</th>
              <th>Ativos</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sistemas?.map((s) => (
              <tr key={s.id}>
                <td><strong>{s.nome}</strong></td>
                <td>{meta.enums.categoria_sistema_labels[s.categoria]}</td>
                <td>{meta.enums.prioridade_labels[s.criticidade]}</td>
                <td style={{ textTransform: 'capitalize' }}>{s.ambiente}</td>
                <td><RagBadge status={s.status_rag} /></td>
                <td>{s.owner_nome}</td>
                <td>
                  {s.data_fim_suporte || '—'}
                  {s.data_fim_suporte && new Date(s.data_fim_suporte) < new Date() && (
                    <span className="badge rag-red" style={{ marginLeft: 6 }}>EOL</span>
                  )}
                </td>
                <td>{s.total_ativos}</td>
                <td>
                  <button className="btn small" onClick={() => setEditing(s)}>Editar</button>{' '}
                  <button className="btn small danger" onClick={() => remove(s.id)}>Excluir</button>
                </td>
              </tr>
            ))}
            {sistemas?.length === 0 && (
              <tr>
                <td colSpan={9} className="empty-state">Nenhum sistema cadastrado ainda.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {editing && (
        <Modal title={editing.id ? 'Editar sistema' : 'Novo sistema'} onClose={() => setEditing(null)} width={620}>
          <SistemaForm initial={editing} meta={meta} onCancel={() => setEditing(null)} onSave={save} />
        </Modal>
      )}
    </div>
  )
}

function SistemaForm({ initial, meta, onCancel, onSave }) {
  const [form, setForm] = useState(initial)
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

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
          <label>Categoria</label>
          <select value={form.categoria} onChange={set('categoria')}>
            {meta.enums.categorias_sistema.map((c) => (
              <option key={c} value={c}>{meta.enums.categoria_sistema_labels[c]}</option>
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
          <label>Ambiente</label>
          <select value={form.ambiente} onChange={set('ambiente')}>
            {meta.enums.ambientes_sistema.map((a) => (
              <option key={a} value={a} style={{ textTransform: 'capitalize' }}>{a}</option>
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
          <label>Fornecedor</label>
          <input value={form.fornecedor} onChange={set('fornecedor')} />
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
          <label>Fim de suporte (EOL)</label>
          <input type="date" value={form.data_fim_suporte || ''} onChange={set('data_fim_suporte')} />
        </div>
      </div>
      <div className="form-actions">
        <button type="button" className="btn" onClick={onCancel}>Cancelar</button>
        <button type="submit" className="btn primary">Salvar</button>
      </div>
    </form>
  )
}
