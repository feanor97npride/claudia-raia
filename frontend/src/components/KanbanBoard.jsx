import { useEffect, useMemo, useState } from 'react'
import {
  DndContext, DragOverlay, PointerSensor, closestCorners, useSensor, useSensors,
} from '@dnd-kit/core'
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { useDroppable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { useMeta } from '../hooks/useMeta'
import { PriorityBadge } from './Badges'
import './KanbanBoard.css'

const COLUMN_TONE = {
  nao_iniciado: 'neutral',
  em_andamento: 'amber',
  em_atraso: 'red',
  concluido: 'green',
}

function DemandaCard({ demanda, onOpen, isOverlay }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: demanda.id })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging && !isOverlay ? 0.35 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`kanban-card${isOverlay ? ' overlay' : ''}`}
      {...attributes}
      {...listeners}
      onClick={() => !isOverlay && onOpen(demanda)}
    >
      <div className="kanban-card-top">
        <PriorityBadge prioridade={demanda.prioridade} />
        {demanda.data_prazo && <span className="kanban-card-date mono">{formatDate(demanda.data_prazo)}</span>}
      </div>
      <div className="kanban-card-title">{demanda.titulo}</div>
      <div className="kanban-card-tags">
        {demanda.projeto_nome && <span className="kanban-tag">▤ {demanda.projeto_nome}</span>}
        {demanda.sistema_nome && <span className="kanban-tag">▣ {demanda.sistema_nome}</span>}
      </div>
      <div className="kanban-card-footer">
        <span className="kanban-avatar">{initials(demanda.responsavel_nome)}</span>
        <span className="kanban-owner">{demanda.responsavel_nome}</span>
      </div>
    </div>
  )
}

function initials(name = '') {
  return name.split(' ').filter(Boolean).slice(0, 2).map((p) => p[0]).join('').toUpperCase()
}

function formatDate(iso) {
  const [, m, d] = iso.split('-')
  return `${d}/${m}`
}

function Column({ status, label, items, onOpen }) {
  const { setNodeRef } = useDroppable({ id: status })
  return (
    <div className="kanban-column">
      <div className={`kanban-column-head tone-${COLUMN_TONE[status]}`}>
        <span>{label}</span>
        <span className="kanban-count">{items.length}</span>
      </div>
      <div ref={setNodeRef} className="kanban-column-body">
        <SortableContext items={items.map((d) => d.id)} strategy={verticalListSortingStrategy}>
          {items.map((d) => (
            <DemandaCard key={d.id} demanda={d} onOpen={onOpen} />
          ))}
        </SortableContext>
        {items.length === 0 && <div className="kanban-empty">Sem demandas</div>}
      </div>
    </div>
  )
}

export default function KanbanBoard({ demandas, onBoardChange, onOpen }) {
  const { meta } = useMeta()
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))
  const [activeId, setActiveId] = useState(null)

  const board = useMemo(() => {
    const grouped = {}
    for (const status of meta.enums.status_kanban) grouped[status] = []
    for (const d of demandas) grouped[d.status_kanban]?.push(d)
    for (const status of meta.enums.status_kanban) {
      grouped[status].sort((a, b) => a.ordem_kanban - b.ordem_kanban)
    }
    return grouped
  }, [demandas, meta])

  const [localBoard, setLocalBoard] = useState(board)
  useEffect(() => setLocalBoard(board), [board])

  const findColumn = (id) => {
    if (localBoard[id]) return id
    return Object.keys(localBoard).find((col) => localBoard[col].some((d) => d.id === id))
  }

  const activeDemanda = activeId ? demandas.find((d) => d.id === activeId) : null

  const handleDragStart = (event) => setActiveId(event.active.id)

  const handleDragOver = (event) => {
    const { active, over } = event
    if (!over) return
    const activeCol = findColumn(active.id)
    const overCol = findColumn(over.id)
    if (!activeCol || !overCol || activeCol === overCol) return

    setLocalBoard((prev) => {
      const activeItems = [...prev[activeCol]]
      const overItems = [...prev[overCol]]
      const activeIndex = activeItems.findIndex((d) => d.id === active.id)
      if (activeIndex === -1) return prev
      const [moved] = activeItems.splice(activeIndex, 1)
      const overIndex = overItems.findIndex((d) => d.id === over.id)
      const insertAt = overIndex === -1 ? overItems.length : overIndex
      overItems.splice(insertAt, 0, moved)
      return { ...prev, [activeCol]: activeItems, [overCol]: overItems }
    })
  }

  const handleDragEnd = (event) => {
    const { active, over } = event
    setActiveId(null)
    if (!over) return
    const activeCol = findColumn(active.id)
    const overCol = findColumn(over.id)
    if (!activeCol || !overCol) return

    let finalBoard = localBoard
    if (activeCol === overCol && active.id !== over.id) {
      const items = [...localBoard[activeCol]]
      const from = items.findIndex((d) => d.id === active.id)
      const to = items.findIndex((d) => d.id === over.id)
      items.splice(to, 0, items.splice(from, 1)[0])
      finalBoard = { ...localBoard, [activeCol]: items }
      setLocalBoard(finalBoard)
    }

    const columns = {}
    for (const status of Object.keys(finalBoard)) {
      columns[status] = finalBoard[status].map((d) => d.id)
    }
    onBoardChange(columns)
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div className="kanban-board">
        {meta.enums.status_kanban.map((status) => (
          <Column
            key={status}
            status={status}
            label={meta.enums.status_kanban_labels[status]}
            items={localBoard[status] || []}
            onOpen={onOpen}
          />
        ))}
      </div>
      <DragOverlay>{activeDemanda && <DemandaCard demanda={activeDemanda} onOpen={() => {}} isOverlay />}</DragOverlay>
    </DndContext>
  )
}
