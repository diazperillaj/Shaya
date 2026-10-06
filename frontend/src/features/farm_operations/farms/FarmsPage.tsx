import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CirclePlus, MapPinned, Search, Sprout } from 'lucide-react'
import { useAuth } from '../../auth/AuthContext'
import { Badge, Button, EmptyState, ErrorMessage, Loading, PageHeader } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { fmtNumber, plural } from '../format'
import type { Farm } from '../models/types'
import { fetchFarms } from '../services/farms.api'
import FarmFormDialog from './FarmFormDialog'

/**
 * Entrada del módulo de cultivo: las fincas visibles para el usuario.
 *
 * El administrador ve todas, con su caficultor; un caficultor ve las suyas.
 */
export default function FarmsPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const navigate = useNavigate()

  const [search, setSearch] = useState('')
  const [creating, setCreating] = useState(false)

  const load = useCallback(() => fetchFarms(search), [search])
  const { data: farms, error, loading } = useLoader(load)

  const newFarm = (
    <Button variant="primary" icon={CirclePlus} onClick={() => setCreating(true)}>
      Nueva finca
    </Button>
  )

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        icon={Sprout}
        title={isAdmin ? 'Fincas' : 'Mis fincas'}
        subtitle={farms ? plural(farms.length, 'finca registrada', 'fincas registradas') : undefined}
        actions={newFarm}
      />

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar por nombre, vereda o municipio…"
          className="w-full rounded-xl border border-gray-200 bg-white py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/25"
        />
      </div>

      {error && <ErrorMessage message={error} />}
      {loading && <Loading />}

      {farms && farms.length === 0 && (
        <EmptyState
          icon={MapPinned}
          title={search ? 'Ninguna finca coincide con la búsqueda' : 'Aún no hay fincas registradas'}
          description={search ? undefined : 'Registra la primera finca para empezar a llevar sus lotes.'}
          action={search ? undefined : newFarm}
        />
      )}

      {farms && farms.length > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {farms.map((farm) => (
            <FarmCard
              key={farm.id}
              farm={farm}
              showFarmer={isAdmin}
              onOpen={() => navigate(`/cultivo/fincas/${farm.id}`)}
            />
          ))}
        </div>
      )}

      {creating && (
        <FarmFormDialog
          onClose={() => setCreating(false)}
          onSaved={(farm) => navigate(`/cultivo/fincas/${farm.id}`)}
        />
      )}
    </div>
  )
}

function FarmCard({ farm, showFarmer, onOpen }: { farm: Farm; showFarmer: boolean; onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="flex flex-col gap-3 rounded-2xl border border-gray-100 bg-white p-5 text-left shadow-sm transition hover:border-emerald-200 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="font-semibold text-gray-900">{farm.name}</h2>
          <p className="text-sm text-gray-500">
            {farm.village}, {farm.municipality}
          </p>
        </div>
        {!farm.active && <Badge>Inactiva</Badge>}
      </div>
      {showFarmer && <p className="text-xs text-gray-400">Caficultor: {farm.farmer.full_name}</p>}
      <div className="flex flex-wrap gap-x-5 gap-y-1 border-t border-gray-100 pt-3 text-sm text-gray-600">
        <span>{plural(farm.active_plots, 'lote activo', 'lotes activos')}</span>
        {farm.total_area !== null && <span>{fmtNumber(farm.total_area, 2, 'ha')}</span>}
        {farm.altitude !== null && <span>{fmtNumber(farm.altitude, 0, 'm s.n.m.')}</span>}
      </div>
    </button>
  )
}
