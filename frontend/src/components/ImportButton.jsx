import { useRef, useState } from 'react'
import { api } from '../api/client'
import Modal from './Modal'

export default function ImportButton({ endpoint, label = 'Importar planilha', hint, onDone }) {
  const fileInput = useRef(null)
  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState(null)

  const handleChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImporting(true)
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await api.upload(endpoint, formData)
      setResult(res)
      if (res.criados > 0) onDone?.()
    } catch (err) {
      setResult({ criados: 0, erros: [err.message], avisos: [] })
    } finally {
      setImporting(false)
      if (fileInput.current) fileInput.current.value = ''
    }
  }

  return (
    <>
      <input ref={fileInput} type="file" accept=".xlsx,.csv" hidden onChange={handleChange} />
      <button className="btn" disabled={importing} onClick={() => fileInput.current?.click()} title={hint}>
        {importing ? 'Importando…' : `⇪ ${label}`}
      </button>

      {result && (
        <Modal title="Resultado da importação" onClose={() => setResult(null)} width={560}>
          <div className="import-summary">
            <span className="badge rag-green">{result.criados} criado(s)</span>
            {result.erros?.length > 0 && <span className="badge rag-red">{result.erros.length} erro(s)</span>}
            {result.avisos?.length > 0 && <span className="badge rag-amber">{result.avisos.length} aviso(s)</span>}
          </div>

          {result.erros?.length > 0 && (
            <div className="import-list">
              <strong>Erros — linhas não importadas</strong>
              <ul>
                {result.erros.map((msg, i) => <li key={i}>{msg}</li>)}
              </ul>
            </div>
          )}

          {result.avisos?.length > 0 && (
            <div className="import-list">
              <strong>Avisos — importadas com algum campo em branco</strong>
              <ul>
                {result.avisos.map((msg, i) => <li key={i}>{msg}</li>)}
              </ul>
            </div>
          )}

          {result.criados > 0 && !result.erros?.length && !result.avisos?.length && (
            <p>Todas as linhas foram importadas sem problemas.</p>
          )}

          <div className="form-actions">
            <button className="btn primary" onClick={() => setResult(null)}>Fechar</button>
          </div>
        </Modal>
      )}
    </>
  )
}
