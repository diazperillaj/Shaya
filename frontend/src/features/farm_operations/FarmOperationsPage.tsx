import { Navigate, Route, Routes } from 'react-router-dom'
import MainLayout from '../../components/layout/MainLayout'
import FarmHomePage from './home/FarmHomePage'

/**
 * Módulo de cultivo, montado en `/cultivo/*`.
 *
 * A diferencia del resto de la app, que cambia de sección desde el menú del
 * inicio, el cultivo usa rutas con URL: es jerárquico (finca → lote → ciclo)
 * y las alertas enlazan a entidades concretas. Cada sección nueva del módulo
 * se agrega aquí como una ruta.
 */
export default function FarmOperationsPage() {
  return (
    <MainLayout>
      <Routes>
        <Route index element={<FarmHomePage />} />
        <Route path="*" element={<Navigate to="/cultivo" replace />} />
      </Routes>
    </MainLayout>
  )
}
