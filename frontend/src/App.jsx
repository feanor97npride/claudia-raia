import { Route, Routes } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import { MetaProvider, useMeta } from './hooks/useMeta'
import { ToastProvider } from './hooks/useToast'
import DashboardPage from './pages/DashboardPage'
import DemandasPage from './pages/DemandasPage'
import ProjetosPage from './pages/ProjetosPage'
import SistemasPage from './pages/SistemasPage'
import InventarioPage from './pages/InventarioPage'
import DocumentosPage from './pages/DocumentosPage'
import UsuariosPage from './pages/UsuariosPage'

function AppShell() {
  const { meta, error } = useMeta()

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        {error && <div className="empty-state">Não foi possível falar com a API: {error}</div>}
        {!error && !meta && <div className="spinner-text">Carregando…</div>}
        {meta && (
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/demandas" element={<DemandasPage />} />
            <Route path="/projetos" element={<ProjetosPage />} />
            <Route path="/sistemas" element={<SistemasPage />} />
            <Route path="/inventario" element={<InventarioPage />} />
            <Route path="/documentos" element={<DocumentosPage />} />
            <Route path="/usuarios" element={<UsuariosPage />} />
          </Routes>
        )}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <MetaProvider>
      <ToastProvider>
        <AppShell />
      </ToastProvider>
    </MetaProvider>
  )
}
