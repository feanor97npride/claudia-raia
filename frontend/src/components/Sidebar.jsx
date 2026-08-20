import { NavLink } from 'react-router-dom'
import './Sidebar.css'

const NAV = [
  { to: '/', label: 'Dashboard', icon: '◧', end: true },
  { to: '/demandas', label: 'Demandas', icon: '☑' },
  { to: '/projetos', label: 'Projetos', icon: '▤' },
  { to: '/sistemas', label: 'Sistemas', icon: '▣' },
  { to: '/inventario', label: 'Inventário', icon: '▦' },
  { to: '/documentos', label: 'Documentos', icon: '▥' },
  { to: '/usuarios', label: 'Usuários', icon: '◍' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-brand-mark">GT</span>
        <div>
          <div className="sidebar-brand-name">Governança de TI</div>
          <div className="sidebar-brand-sub">Controle tático &amp; ativos</div>
        </div>
      </div>
      <nav className="sidebar-nav">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
          >
            <span className="sidebar-link-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">Protótipo interno &middot; v0.1</div>
    </aside>
  )
}
