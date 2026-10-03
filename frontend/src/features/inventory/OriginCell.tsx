import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

/**
 * Origen de un pergamino: comprado, o producido en una finca del módulo de
 * cultivo. Al administrador le enlaza la trazabilidad hasta los lotes (el
 * resto del personal no tiene acceso al módulo de cultivo).
 */
export default function OriginCell({ parchmentId, dryingId }: { parchmentId: number; dryingId: number | null }) {
  const { user } = useAuth()

  if (dryingId === null) return <span className="text-gray-500">Comprado</span>
  if (user?.role !== 'admin') return <span>Producción propia</span>

  return (
    <Link
      to={`/cultivo/trazabilidad/pergamino/${parchmentId}`}
      className="font-medium text-emerald-800 underline-offset-2 hover:underline"
    >
      Producción propia · ver trazabilidad
    </Link>
  )
}
