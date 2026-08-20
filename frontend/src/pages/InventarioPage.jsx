import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import { useMeta } from '../hooks/useMeta'
import { useToast } from '../hooks/useToast'
import { StatusAtivoBadge } from '../components/Badges'
import Modal from '../components/Modal'

const BLANK = {
  tipo: 'hardware', nome: '', sistema_id: '', numero_serie: '', chave_licenca: '',
  fabricante: '', quantidade: 1, status: 'estoque', responsavel_id: '', localizacao: '',
  data_aquisicao: '', data_expiracao: '',
}

export default function InventarioPage() {
  const { meta } = useMeta()
  const showToast = useToast()
  const [ativos, setAtivos] = useState(null)
  const [selected, setSelected] = useState(new Set())
  const [editing, setEditing] = useState(null)
  const [bulkFields, setBulkFields] = useState({ status: '', localizacao: '', responsavel_id: '' })
  const [filters, setFilters] = useState({ tipo: '', status: '' })
  const fileInput = useRef(null)
  const [importing, setImporting] = useState(false)

  const load = () => api.get('/ativos').then(setAtivos).catch((e) => showToast(e.message, 'error'))
  useEffect(() => { load() }, [])

  const visible = (ativos || []).filter((a) => {
    if (filters.tipo && a.tipo !== filters.tipo) return false
    if (filters.status && a.status !== filters.status) return false
    return true
  })

  const toggleOne = (id) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    setSelected((prev) => (prev.size === visible.length ? new Set() : new Set(visible.map((a) => a.id))))
  }

  const save = async (form) => {
    try {
      if (form.id) {
        await api.put(`/ativos/${form.id}`, form)
        showToast('Ativo atualizado.')
      } else {
        await api.post('/ativos', form)
        showToast('Ativo cadastrado.')
      }
      setEditing(null)
      load()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const remove = async (id) => {
    if (!confirm('Excluir este ativo?')) return
    await api.del(`/ativos/${id}`)
    showToast('Ativo excluído.')
    setEditing(null)
    load()
  }

  const applyBulk = async () => {
    const fields = {}
    if (bulkFields.status) fields.status = bulkFields.status
    if (bulkFields.localizacao) fields.localizacao = bulkFields.localizacao
    if (bulkFields.responsavel_id) fields.responsavel_id = Number(bulkFields.responsavel_id)
    if (Object.keys(fields).length === 0) {
      showToast('Escolha ao menos uma alteração para aplicar.', 'error')
      return
    }
    try {
      const res = await api.patch('/ativos/bulk', { ids: [...selected], fields })
      showToast(`${res.atualizados} ativo(s) atualizado(s) em massa.`)
      setSelected(new Set())
      setBulkFields({ status: '', localizacao: '', responsavel_id: '' })
      load()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const handleImport = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImporting(true)
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await api.upload('/ativos/import-xml', formData)
      showToast(`Importação concluída: ${res.criados} ativo(s) criado(s)${res.erros.length ? `, ${res.erros.length} erro(s)` : ''}.`, res.erros.length ? 'error' : 'ok')
      load()
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setImporting(false)
      if (fileInput.current) fileInput.current.value = ''
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="kicker">Inventário avançado &middot; ITAM/SAM</div>
          <h1>Ativos</h1>
          <div className="subtitle">Hardware, licenças de software e assinaturas SaaS corporativas.</div>
        </div>
        <div className="actions">
          <input ref={fileInput} type="file" accept=".xml" hidden onChange={handleImport} />
          <button className="btn" disabled={importing} onClick={() => fileInput.current?.click()}>
            {importing ? 'Importando…' : '⇪ Importar XML'}
          </button>
          <button className="btn primary" onClick={() => setEditing({ ...BLANK })}>+ Novo ativo</button>
        </div>
      </div>

      <div className="filters-row">
        <select value={filters.tipo} onChange={(e) => setFilters({ ...filters, tipo: e.target.value })}>
          <option value="">Todos os tipos</option>
          {meta.enums.tipos_ativo.map((t) => (
            <option key={t} value={t}>{meta.enums.tipo_ativo_labels[t]}</option>
          ))}
        </select>
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
          <option value="">Todos os status</option>
          {meta.enums.status_ativo.map((s) => (
            <option key={s} value={s}>{meta.enums.status_ativo_labels[s]}</option>
          ))}
        </select>
      </div>

      {selected.size > 0 && (
        <div className="bulk-bar">
          <strong>{selected.size} selecionado(s)</strong>
          <select value={bulkFields.status} onChange={(e) => setBulkFields({ ...bulkFields, status: e.target.value })}>
            <option value="">Alterar status…</option>
            {meta.enums.status_ativo.map((s) => (
              <option key={s} value={s}>{meta.enums.status_ativo_labels[s]}</option>
            ))}
          </select>
          <input
            placeholder="Nova localização…"
            value={bulkFields.localizacao}
            onChange={(e) => setBulkFields({ ...bulkFields, localizacao: e.target.value })}
          />
          <select value={bulkFields.responsavel_id} onChange={(e) => setBulkFields({ ...bulkFields, responsavel_id: e.target.value })}>
            <option value="">Alterar responsável…</option>
            {meta.usuarios.map((u) => (
              <option key={u.id} value={u.id}>{u.nome}</option>
            ))}
          </select>
          <button className="btn primary small" onClick={applyBulk}>Aplicar em massa</button>
          <button className="btn small" onClick={() => setSelected(new Set())}>Cancelar seleção</button>
        </div>
      )}

      <div className="card table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th style={{ width: 32 }}>
                <input type="checkbox" checked={visible.length > 0 && selected.size === visible.length} onChange={toggleAll} />
              </th>
              <th>Ativo</th>
              <th>Tipo</th>
              <th>Sistema</th>
              <th>Status</th>
              <th>Responsável</th>
              <th>Localização</th>
              <th>Origem</th>
              <th>Expiração</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {visible.map((a) => (
              <tr key={a.id}>
                <td><input type="checkbox" checked={selected.has(a.id)} onChange={() => toggleOne(a.id)} /></td>
                <td>
                  <strong>{a.nome}</strong>
                  {a.numero_serie && <div style={{ fontSize: 11.5, color: 'var(--ink-400)' }} className="mono">{a.numero_serie}</div>}
                </td>
                <td>{meta.enums.tipo_ativo_labels[a.tipo]}</td>
                <td>{a.sistema_nome || '—'}</td>
                <td><StatusAtivoBadge status={a.status} /></td>
                <td>{a.responsavel_nome || '—'}</td>
                <td>{a.localizacao || '—'}</td>
                <td>
                  <span className={`badge ${a.origem_importacao === 'xml' ? 'neutral' : 'neutral'}`}>
                    {a.origem_importacao === 'xml' ? 'XML' : 'Manual'}
                  </span>
                </td>
                <td>{a.data_expiracao || '—'}</td>
                <td>
                  <button className="btn small" onClick={() => setEditing(a)}>Editar</button>{' '}
                  <button className="btn small danger" onClick={() => remove(a.id)}>Excluir</button>
                </td>
              </tr>
            ))}
            {visible.length === 0 && (
              <tr><td colSpan={10} className="empty-state">Nenhum ativo encontrado.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {editing && (
        <Modal title={editing.id ? 'Editar ativo' : 'Novo ativo'} onClose={() => setEditing(null)} width={620}>
          <AtivoForm initial={editing} meta={meta} onCancel={() => setEditing(null)} onSave={save} />
        </Modal>
      )}
    </div>
  )
}

function AtivoForm({ initial, meta, onCancel, onSave }) {
  const [form, setForm] = useState(initial)
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSave(form) }}>
      <div className="form-grid">
        <div className="form-field full">
          <label>Nome</label>
          <input required value={form.nome} onChange={set('nome')} />
        </div>
        <div className="form-field">
          <label>Tipo</label>
          <select value={form.tipo} onChange={set('tipo')}>
            {meta.enums.tipos_ativo.map((t) => (
              <option key={t} value={t}>{meta.enums.tipo_ativo_labels[t]}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Status</label>
          <select value={form.status} onChange={set('status')}>
            {meta.enums.status_ativo.map((s) => (
              <option key={s} value={s}>{meta.enums.status_ativo_labels[s]}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Sistema vinculado</label>
          <select value={form.sistema_id || ''} onChange={set('sistema_id')}>
            <option value="">Nenhum</option>
            {meta.sistemas.map((s) => (
              <option key={s.id} value={s.id}>{s.nome}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Responsável</label>
          <select value={form.responsavel_id || ''} onChange={set('responsavel_id')}>
            <option value="">Nenhum</option>
            {meta.usuarios.map((u) => (
              <option key={u.id} value={u.id}>{u.nome}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Fabricante</label>
          <input value={form.fabricante} onChange={set('fabricante')} />
        </div>
        <div className="form-field">
          <label>Nº de série</label>
          <input value={form.numero_serie} onChange={set('numero_serie')} />
        </div>
        <div className="form-field">
          <label>Chave de licença</label>
          <input value={form.chave_licenca} onChange={set('chave_licenca')} />
        </div>
        <div className="form-field">
          <label>Quantidade</label>
          <input type="number" min={1} value={form.quantidade} onChange={set('quantidade')} />
        </div>
        <div className="form-field">
          <label>Localização</label>
          <input value={form.localizacao} onChange={set('localizacao')} />
        </div>
        <div className="form-field">
          <label>Aquisição</label>
          <input type="date" value={form.data_aquisicao || ''} onChange={set('data_aquisicao')} />
        </div>
        <div className="form-field">
          <label>Expiração / garantia</label>
          <input type="date" value={form.data_expiracao || ''} onChange={set('data_expiracao')} />
        </div>
      </div>
      <div className="form-actions">
        <button type="button" className="btn" onClick={onCancel}>Cancelar</button>
        <button type="submit" className="btn primary">Salvar</button>
      </div>
    </form>
  )
}
