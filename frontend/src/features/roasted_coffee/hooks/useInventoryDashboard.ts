import { useEffect, useState } from 'react'
import { fetchInventoryDashboard } from '../services/roasted_coffee.api'
import type { InventoryDashboard } from '../models/types'

interface UseInventoryDashboardResult {
  data: InventoryDashboard | null
  loading: boolean
  error: string | null
  refresh: () => void
}

export function useInventoryDashboard(): UseInventoryDashboardResult {
  const [data, setData] = useState<InventoryDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const result = await fetchInventoryDashboard()
        if (!cancelled) setData(result)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Error cargando el inventario')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [tick])

  return { data, loading, error, refresh: () => setTick((t) => t + 1) }
}
