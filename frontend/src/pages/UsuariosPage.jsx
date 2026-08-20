import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useMeta } from '../hooks/useMeta'
import { useToast } from '../hooks/useToast'
import Modal from '../components/Modal'

const BLANK = { nome: '', email: '', area_id: '', papel: 'analista', ativo: true }

export default function UsuariosPage() {
  const { meta, reload: reloadMeta } = useMeta()
  const showToast = useToast()
  const [usuarios, setUsuarios] = useState(null)
  const [editing, setEditing] = useState(null)

  const load = () =>
    api.get('/usuarios?incluir_inativos=1').then(setUsuarios).catch((e) => showToast(e.message, 'error'))
  useEffect(() => { load() }, [])

  const save = async (form) => {
    try {
      const payload = { ...form, area_id: form.area_id || null }
      if (form.id) {
        await api.put(`/usuarios/${form.id}`, payload)
        showToast('Usuário atualizado.')
      } else {
        await api.post('/usuarios', payload)
        showToast('Usuário cadastrado.')
      }
      setEditing(null)
      load()
      reloadMeta()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const toggleAtivo = async (u) => {
    await api.put(`/usuarios/${u.id}`, { ativo: !u.ativo })
    load()
    reloadMeta()
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="kicker">Governança &middot; acessos</div>
          <h1>Usuários</h1>
          <div className="subtitle">
            Quem pode ser dono de sistemas e projetos, responsável por demandas e aprovador de documentos.
          </div>
        </div>
        <div className="actions">
          <button className="btn primary" onClick={() => setEditing({ ...BLANK })}>
            + Novo usuário
          </button>
        </div>
      </div>

      <div className="card table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Nome</th>
              <th>E-mail</th>
              <th>Área</th>
              <th>Papel</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {usuarios?.map((u) => (
              <tr key={u.id}>
                <td><strong>{u.nome}</strong></td>
                <td>{u.email}</td>
                <td>{u.area_nome || '—'}</td>
                <td>{meta.enums.papel_usuario_labels[u.papel]}</td>
                <td>
                  <span className={`badge ${u.ativo ? 'rag-green' : 'neutral'}`}>
                    {u.ativo ? 'Ativo' : 'Inativo'}
                  </span>
                </td>
                <td>
                  <button className="btn small" onClick={() => setEditing(u)}>Editar</button>{' '}
                  <button className="btn small danger" onClick={() => toggleAtivo(u)}>
                    {u.ativo ? 'Desativar' : 'Reativar'}
                  </button>
                </td>
              </tr>
            ))}
            {usuarios?.length === 0 && (
              <tr>
                <td colSpan={6} className="empty-state">
                  Nenhum usuário cadastrado ainda — crie o primeiro para poder atribuir donos e responsáveis.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {editing && (
        <Modal title={editing.id ? 'Editar usuário' : 'Novo usuário'} onClose={() => setEditing(null)} width={520}>
          <UsuarioForm initial={editing} meta={meta} reloadMeta={reloadMeta} onCancel={() => setEditing(null)} onSave={save} />
        </Modal>
      )}
    </div>
  )
}

function UsuarioForm({ initial, meta, reloadMeta, onCancel, onSave }) {
  const showToast = useToast()
  const [form, setForm] = useState(initial)
  const [novaArea, setNovaArea] = useState('')
  const [addingArea, setAddingArea] = useState(false)
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const criarArea = async () => {
    const nome = novaArea.trim()
    if (!nome) return
    setAddingArea(true)
    try {
      const area = await api.post('/areas', { nome })
      await reloadMeta()
      setForm((f) => ({ ...f, area_id: area.id }))
      setNovaArea('')
    } catch (e) {
      showToast(e.message, 'error')
    } finally {
      setAddingArea(false)
    }
  }

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSave(form) }}>
      <div className="form-grid">
        <div className="form-field full">
          <label>Nome</label>
          <input required value={form.nome} onChange={set('nome')} />
        </div>
        <div className="form-field full">
          <label>E-mail</label>
          <input required type="email" value={form.email} onChange={set('email')} />
        </div>
        <div className="form-field">
          <label>Papel</label>
          <select value={form.papel} onChange={set('papel')}>
            {meta.enums.papeis_usuario.map((p) => (
              <option key={p} value={p}>{meta.enums.papel_usuario_labels[p]}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Área</label>
          <select value={form.area_id || ''} onChange={set('area_id')}>
            <option value="">Sem área</option>
            {meta.areas.map((a) => (
              <option key={a.id} value={a.id}>{a.nome}</option>
            ))}
          </select>
        </div>
        <div className="form-field full">
          <label>Nova área (opcional)</label>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              placeholder="Ex.: Financeiro"
              value={novaArea}
              onChange={(e) => setNovaArea(e.target.value)}
            />
            <button type="button" className="btn small" disabled={addingArea || !novaArea.trim()} onClick={criarArea}>
              Adicionar
            </button>
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
