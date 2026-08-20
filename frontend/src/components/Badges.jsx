import { useMeta } from '../hooks/useMeta'

export function RagBadge({ status }) {
  const { meta } = useMeta()
  const label = meta?.enums.status_rag_labels[status] || status
  return (
    <span className={`badge rag-${status}`}>
      <span className="dot" />
      {label}
    </span>
  )
}

export function PriorityBadge({ prioridade }) {
  const { meta } = useMeta()
  const label = meta?.enums.prioridade_labels[prioridade] || prioridade
  return <span className={`badge pr-${prioridade}`}>{label}</span>
}

export function KanbanBadge({ status }) {
  const { meta } = useMeta()
  const label = meta?.enums.status_kanban_labels[status] || status
  const tone = { nao_iniciado: 'neutral', em_andamento: 'rag-amber', em_atraso: 'rag-red', concluido: 'rag-green' }[
    status
  ]
  return <span className={`badge ${tone}`}>{label}</span>
}

export function StatusAtivoBadge({ status }) {
  const { meta } = useMeta()
  const label = meta?.enums.status_ativo_labels[status] || status
  const tone = { em_uso: 'rag-green', estoque: 'neutral', manutencao: 'rag-amber', baixado: 'rag-red' }[status]
  return <span className={`badge ${tone}`}>{label}</span>
}

export function AprovacaoBadge({ status }) {
  const { meta } = useMeta()
  const label = meta?.enums.status_aprovacao_doc_labels[status] || status
  const tone = {
    rascunho: 'neutral',
    em_aprovacao: 'rag-amber',
    aprovado: 'rag-green',
    rejeitado: 'rag-red',
    assinado: 'rag-green',
  }[status]
  return <span className={`badge ${tone}`}>{label}</span>
}
