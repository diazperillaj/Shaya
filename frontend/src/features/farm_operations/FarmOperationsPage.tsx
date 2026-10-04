import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'
import { FlaskConical, KeyRound, LayoutDashboard, MapPinned } from 'lucide-react'
import MainLayout from '../../components/layout/MainLayout'
import { useAuth } from '../auth/AuthContext'
import RequireRole from '../auth/RequireRole'
import FarmerAccountsPage from './accounts/FarmerAccountsPage'
import FarmDashboardPage from './dashboard/FarmDashboardPage'
import FarmDetailPage from './farms/FarmDetailPage'
import FarmsPage from './farms/FarmsPage'
import HarvestPage from './harvests/HarvestPage'
import PaymentsPage from './payroll/PaymentsPage'
import DryingPage from './postharvest/DryingPage'
import PostharvestPage from './postharvest/PostharvestPage'
import { DryingTracePage, ParchmentTracePage } from './postharvest/TraceabilityPage'
import WetProcessingPage from './postharvest/WetProcessingPage'
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
    label: 'Resumen',
    icon: LayoutDashboard,
    matches: (path) => path === '/cultivo' || path === '/cultivo/',
  },
  {
    to: '/cultivo/fincas',
    label: 'Fincas',
    icon: MapPinned,
    matches: (path) =>
      ['/cultivo/fincas', '/cultivo/lotes', '/cultivo/cosechas', '/cultivo/beneficios', '/cultivo/secados', '/cultivo/trazabilidad']
        .some((prefix) => path.startsWith(prefix)),
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
          <Route index element={<FarmDashboardPage />} />
          <Route path="fincas" element={<FarmsPage />} />
          <Route path="fincas/:farmId" element={<FarmDetailPage />} />
          <Route path="fincas/:farmId/pagos" element={<PaymentsPage />} />
          <Route path="fincas/:farmId/poscosecha" element={<PostharvestPage />} />
          <Route path="beneficios/:wetProcessingId" element={<WetProcessingPage />} />
          <Route path="secados/:dryingId" element={<DryingPage />} />
          <Route path="secados/:dryingId/trazabilidad" element={<DryingTracePage />} />
          <Route path="trazabilidad/pergamino/:parchmentId" element={<ParchmentTracePage />} />
          <Route path="lotes/:plotId" element={<PlotDetailPage />} />
          <Route path="cosechas/:harvestId" element={<HarvestPage />} />
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
