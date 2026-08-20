import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client'

const MetaContext = createContext(null)

export function MetaProvider({ children }) {
  const [meta, setMeta] = useState(null)
  const [error, setError] = useState(null)

  const reload = () => {
    api.get('/meta').then(setMeta).catch((err) => setError(err.message))
  }

  useEffect(reload, [])

  return <MetaContext.Provider value={{ meta, error, reload }}>{children}</MetaContext.Provider>
}

export function useMeta() {
  const ctx = useContext(MetaContext)
  if (!ctx) throw new Error('useMeta deve ser usado dentro de <MetaProvider>')
  return ctx
}
