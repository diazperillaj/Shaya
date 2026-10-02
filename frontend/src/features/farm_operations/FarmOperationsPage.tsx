import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'
import { FlaskConical, KeyRound, MapPinned } from 'lucide-react'
import MainLayout from '../../components/layout/MainLayout'
import { useAuth } from '../auth/AuthContext'
import RequireRole from '../auth/RequireRole'
import FarmerAccountsPage from './accounts/FarmerAccountsPage'
import FarmDetailPage from './farms/FarmDetailPage'
import FarmsPage from './farms/FarmsPage'
import PlotDetailPage from './plots/PlotDetailPage'
import SuppliesPage from './supplies/SuppliesPage'

interface Tab {
  to: string
  label: string
  icon: LucideIcon
  /** Rutas que pertenecen a la pestaña */
  matches: (path: string) => boolean
  adminOnly?: boolean
}

const TABS: Tab[] = [
  {
    to: '/cultivo',
    label: 'Fincas',
    icon: MapPinned,
    matches: (path) =>
      path === '/cultivo' || path.startsWith('/cultivo/fincas') || path.startsWith('/cultivo/lotes'),
  },
  {
    to: '/cultivo/insumos',
    label: 'Insumos',
    icon: FlaskConical,
    matches: (path) => path.startsWith('/cultivo/insumos'),
  },
  {
    to: '/cultivo/cuentas',
    label: 'Cuentas',
    icon: KeyRound,
    matches: (path) => path.startsWith('/cultivo/cuentas'),
    adminOnly: true,
  },
]

/**
 * Módulo de cultivo, montado en `/cultivo/*`.
 *
 * A diferencia del resto de la app, que cambia de sección desde el menú del
 * inicio, el cultivo usa rutas con URL: es jerárquico (finca → lote → ciclo)
 * y las alertas enlazan a entidades concretas. Cada sección nueva del módulo
 * se agrega aquí como una ruta.
 */
export default function FarmOperationsPage() {
  const { user } = useAuth()
  const { pathname } = useLocation()
  const tabs = TABS.filter((tab) => !tab.adminOnly || user?.role === 'admin')

  return (
    <MainLayout>
      <div className="mx-auto flex max-w-6xl flex-col gap-6 text-left">
        <nav className="flex gap-1 overflow-x-auto border-b border-gray-200">
          {tabs.map(({ to, label, icon: Icon, matches }) => {
            const active = matches(pathname)
            return (
              <Link
                key={to}
                to={to}
                className={`-mb-px flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition ${
                  active
                    ? 'border-emerald-800 text-emerald-900'
                    : 'border-transparent text-gray-500 hover:text-gray-800'
                }`}
              >
                <Icon className="h-4 w-4" /> {label}
              </Link>
            )
          })}
        </nav>

        <Routes>
          <Route index element={<FarmsPage />} />
          <Route path="fincas/:farmId" element={<FarmDetailPage />} />
          <Route path="lotes/:plotId" element={<PlotDetailPage />} />
          <Route path="insumos" element={<SuppliesPage />} />
          <Route
            path="cuentas"
            element={
              <RequireRole roles={['admin']}>
                <FarmerAccountsPage />
              </RequireRole>
            }
          />
          <Route path="*" element={<Navigate to="/cultivo" replace />} />
        </Routes>
      </div>
    </MainLayout>
  )
}
