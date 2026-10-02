import './App.css'
import { BrowserRouter, Navigate, Routes, Route } from "react-router-dom"
import HomePage from "./pages/HomePage"
import AuthPage from "./features/auth/AuthPage"
import ProtectedRoute from './features/auth/ProtectedRoute'
import RequireRole from './features/auth/RequireRole'
import { FARM_ROLES, STAFF_ROLES } from './features/auth/roles'
import FarmOperationsPage from './features/farm_operations/FarmOperationsPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={ <AuthPage /> } />
        <Route path="/" element={
          <ProtectedRoute>
            <RequireRole roles={STAFF_ROLES}>
              <HomePage />
            </RequireRole>
          </ProtectedRoute>
        } />
        <Route path="/cultivo/*" element={
          <ProtectedRoute>
            <RequireRole roles={FARM_ROLES}>
              <FarmOperationsPage />
            </RequireRole>
          </ProtectedRoute>
        } />
        <Route path="*" element={ <Navigate to="/" replace /> } />
      </Routes>
    </BrowserRouter>
  )
}

export default App
