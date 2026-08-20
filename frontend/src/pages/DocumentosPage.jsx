import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useMeta } from '../hooks/useMeta'
import { useToast } from '../hooks/useToast'
import { AprovacaoBadge } from '../components/Badges'
import Modal from '../components/Modal'

const BLANK = {
  tipo: 'politica_ti', titulo: '', descricao: '', versao: '1.0',
  autor_id: '', projeto_id: '', sistema_id: '', data_validade: '', aprovador_ids: [],
}

export default function DocumentosPage() {
  const { meta } = useMeta()
  const showToast = useToast()
  const [documentos, setDocumentos] = useState(null)
  const [creating, setCreating] = useState(null)
  const [detail, setDetail] = useState(null)

  const load = () => api.get('/documentos').then(setDocumentos).catch((e) => showToast(e.message, 'error'))
  useEffect(() => { load() }, [])

  const openDetail = async (id) => {
    const doc = await api.get(`/documentos/${id}`)
    setDetail(doc)
  }

  const create = async (form) => {
    try {
      await api.post('/documentos', form)
      showToast('Documento criado.')
      setCreating(null)
      load()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const enviarAprovacao = async (id) => {
    try {
      const doc = await api.post(`/documentos/${id}/enviar-aprovacao`)
      setDetail(doc)
      showToast('Documento enviado para aprovação.')
      load()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const decidir = async (documentoId, etapaId, status) => {
    const comentario = status === 'rejeitado' ? prompt('Motivo da rejeição (opcional):') || '' : ''
    try {
      const doc = await api.put(`/documentos/${documentoId}/etapas/${etapaId}`, { status, comentario })
      setDetail(doc)
      showToast(status === 'aprovado' ? 'Etapa aprovada.' : 'Etapa rejeitada.')
      load()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="kicker">Fluxos documentais</div>
          <h1>Documentos</h1>
          <div className="subtitle">Políticas de TI e contratos, com fluxo de aprovação e assinatura digital.</div>
        </div>
        <div className="actions">
          <button className="btn primary" onClick={() => setCreating({ ...BLANK })}>+ Novo documento</button>
        </div>
      </div>

      <div className="card table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Documento</th>
              <th>Tipo</th>
              <th>Status</th>
              <th>Autor</th>
              <th>Versão</th>
              <th>Vínculo</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {documentos?.map((d) => (
              <tr key={d.id}>
                <td><strong>{d.titulo}</strong></td>
                <td>{meta.enums.tipo_documento_labels[d.tipo]}</td>
                <td><AprovacaoBadge status={d.status_aprovacao} /></td>
                <td>{d.autor_nome}</td>
                <td className="mono">{d.versao}</td>
                <td>{[d.projeto_nome, d.sistema_nome].filter(Boolean).join(' · ') || '—'}</td>
                <td><button className="btn small" onClick={() => openDetail(d.id)}>Abrir</button></td>
              </tr>
            ))}
            {documentos?.length === 0 && (
              <tr><td colSpan={7} className="empty-state">Nenhum documento cadastrado ainda.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {creating && (
        <Modal title="Novo documento" onClose={() => setCreating(null)} width={640}>
          <DocumentoForm initial={creating} meta={meta} onCancel={() => setCreating(null)} onSave={create} />
        </Modal>
      )}

      {detail && (
        <Modal title={detail.titulo} onClose={() => setDetail(null)} width={640}>
          <DocumentoDetail
            doc={detail}
            meta={meta}
            onEnviarAprovacao={() => enviarAprovacao(detail.id)}
            onDecidir={decidir}
            reload={() => openDetail(detail.id)}
          />
        </Modal>
      )}
    </div>
  )
}

function DocumentoForm({ initial, meta, onCancel, onSave }) {
  const [form, setForm] = useState(initial)
  const [novoAprovador, setNovoAprovador] = useState('')
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const addAprovador = () => {
    if (!novoAprovador || form.aprovador_ids.includes(Number(novoAprovador))) return
    setForm({ ...form, aprovador_ids: [...form.aprovador_ids, Number(novoAprovador)] })
    setNovoAprovador('')
  }
  const removeAprovador = (id) => setForm({ ...form, aprovador_ids: form.aprovador_ids.filter((x) => x !== id) })
  const nomeUsuario = (id) => meta.usuarios.find((u) => u.id === id)?.nome || id

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
          <label>Tipo</label>
          <select value={form.tipo} onChange={set('tipo')}>
            {meta.enums.tipos_documento.map((t) => (
              <option key={t} value={t}>{meta.enums.tipo_documento_labels[t]}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Versão</label>
          <input value={form.versao} onChange={set('versao')} />
        </div>
        <div className="form-field">
          <label>Autor</label>
          <select required value={form.autor_id} onChange={set('autor_id')}>
            <option value="">Selecione…</option>
            {meta.usuarios.map((u) => (
              <option key={u.id} value={u.id}>{u.nome}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Validade (contratos)</label>
          <input type="date" value={form.data_validade || ''} onChange={set('data_validade')} />
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
        <div className="form-field full">
          <label>Fluxo de aprovação (ordem de aprovadores)</label>
          <div style={{ display: 'flex', gap: 8 }}>
            <select value={novoAprovador} onChange={(e) => setNovoAprovador(e.target.value)}>
              <option value="">Selecione um aprovador…</option>
              {meta.usuarios.map((u) => (
                <option key={u.id} value={u.id}>{u.nome}</option>
              ))}
            </select>
            <button type="button" className="btn small" onClick={addAprovador}>+ Adicionar</button>
          </div>
          {form.aprovador_ids.length > 0 && (
            <ol style={{ margin: '10px 0 0', paddingLeft: 20, fontSize: 13 }}>
              {form.aprovador_ids.map((id) => (
                <li key={id} style={{ marginBottom: 4 }}>
                  {nomeUsuario(id)}{' '}
                  <button type="button" className="btn small" onClick={() => removeAprovador(id)}>remover</button>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
      <div className="form-actions">
        <button type="button" className="btn" onClick={onCancel}>Cancelar</button>
        <button type="submit" className="btn primary">Criar documento</button>
      </div>
    </form>
  )
}

function DocumentoDetail({ doc, meta, onEnviarAprovacao, onDecidir, reload }) {
  const showToast = useToast()
  const [signForm, setSignForm] = useState({ signatario_id: '', signatario_email: '', provedor: 'docusign' })

  const addSignature = async () => {
    try {
      await api.post(`/documentos/${doc.id}/assinaturas`, signForm)
      showToast('Signatário adicionado.')
      reload()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const sendSignature = async (assinaturaId) => {
    try {
      await api.post(`/documentos/${doc.id}/assinaturas/${assinaturaId}/enviar`)
      showToast('Enviado para assinatura (integração de exemplo).')
      reload()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  return (
    <div className="doc-detail">
      <div className="doc-detail-head">
        <AprovacaoBadge status={doc.status_aprovacao} />
        <span className="mono" style={{ color: 'var(--ink-400)', fontSize: 12 }}>v{doc.versao}</span>
      </div>
      <p style={{ fontSize: 13.5, color: 'var(--ink-600)', margin: '10px 0 0' }}>{doc.descricao || 'Sem descrição.'}</p>

      <h4 style={{ marginTop: 22, fontSize: 13.5 }}>Fluxo de aprovação</h4>
      {doc.etapas.length === 0 && <p className="empty-state" style={{ padding: 12 }}>Nenhum aprovador cadastrado.</p>}
      <ol className="approval-flow">
        {doc.etapas.map((etapa) => (
          <li key={etapa.id} className={`approval-step status-${etapa.status}`}>
            <div>
              <strong>{etapa.aprovador_nome}</strong>
              <span className="mono" style={{ fontSize: 11, color: 'var(--ink-400)', marginLeft: 6 }}>#{etapa.ordem}</span>
              {etapa.comentario && <div style={{ fontSize: 12, color: 'var(--ink-600)' }}>{etapa.comentario}</div>}
            </div>
            {etapa.status === 'pendente' && doc.status_aprovacao === 'em_aprovacao' ? (
              <div style={{ display: 'flex', gap: 6 }}>
                <button className="btn small" onClick={() => onDecidir(doc.id, etapa.id, 'aprovado')}>Aprovar</button>
                <button className="btn small danger" onClick={() => onDecidir(doc.id, etapa.id, 'rejeitado')}>Rejeitar</button>
              </div>
            ) : (
              <span className={`badge ${etapa.status === 'aprovado' ? 'rag-green' : etapa.status === 'rejeitado' ? 'rag-red' : 'neutral'}`}>
                {etapa.status === 'pendente' ? 'Aguardando' : etapa.status === 'aprovado' ? 'Aprovado' : 'Rejeitado'}
              </span>
            )}
          </li>
        ))}
      </ol>
      {doc.status_aprovacao === 'rascunho' && (
        <button className="btn primary small" style={{ marginTop: 8 }} onClick={onEnviarAprovacao}>Enviar para aprovação</button>
      )}

      <h4 style={{ marginTop: 22, fontSize: 13.5 }}>Assinatura digital</h4>
      <p style={{ fontSize: 12, color: 'var(--ink-400)', margin: '2px 0 10px' }}>
        Arquitetura pronta para integração real com DocuSign, Clicksign ou D4Sign — o botão "Enviar" abaixo aciona um stub.
      </p>
      {doc.assinaturas.map((s) => (
        <div key={s.id} className="signature-row">
          <div>
            <strong>{s.signatario_nome || s.signatario_email || 'Signatário externo'}</strong>
            <div style={{ fontSize: 11.5, color: 'var(--ink-400)' }}>{s.provedor} {s.url_assinatura && `· ${s.url_assinatura}`}</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className={`badge ${s.status === 'assinado' ? 'rag-green' : s.status === 'recusado' ? 'rag-red' : 'neutral'}`}>{s.status}</span>
            {s.status === 'pendente' && <button className="btn small" onClick={() => sendSignature(s.id)}>Enviar</button>}
          </div>
        </div>
      ))}

      <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
        <select value={signForm.signatario_id} onChange={(e) => setSignForm({ ...signForm, signatario_id: e.target.value })}>
          <option value="">Signatário interno…</option>
          {meta.usuarios.map((u) => (
            <option key={u.id} value={u.id}>{u.nome}</option>
          ))}
        </select>
        <input
          placeholder="ou e-mail externo"
          value={signForm.signatario_email}
          onChange={(e) => setSignForm({ ...signForm, signatario_email: e.target.value })}
        />
        <select value={signForm.provedor} onChange={(e) => setSignForm({ ...signForm, provedor: e.target.value })}>
          {meta.enums.provedores_assinatura.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <button className="btn small" onClick={addSignature}>+ Adicionar signatário</button>
      </div>
    </div>
  )
}
