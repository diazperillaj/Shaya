// src/features/roasted_coffee/RoastedCoffeePage.tsx
import { useEffect, useState } from 'react'
import { Search, Coffee } from 'lucide-react'

import DataTable from '../../components/ui/DataTable'
import { RoastedCoffeeColumns } from './models/columns'
import type { RoastedCoffeeRow } from './models/types'
import { fetchRoastedCoffees } from './services/roasted_coffee.api'

export default function RoastedCoffeePage() {
  const [data, setData] = useState<RoastedCoffeeRow[]>([])
  const [search, setSearch] = useState('')

  const loadRoastedCoffees = async (): Promise<void> => {
    try {
      const rows = await fetchRoastedCoffees({ search })
      setData(rows)
    } catch {
      setData([])
    }
  }

  useEffect(() => {
    loadRoastedCoffees()
  }, [search])

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-emerald-100 rounded-xl">
          <Coffee className="w-6 h-6 text-emerald-800" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Maquilado</h1>
          <p className="text-sm text-gray-400">{data.length} lote{data.length !== 1 ? 's' : ''} registrado{data.length !== 1 ? 's' : ''}</p>
        </div>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar maquilado…"
          className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
        />
      </div>

      <DataTable
        columns={RoastedCoffeeColumns}
        data={data}
        isAdmin={false}
      />
    </div>
  )
}
