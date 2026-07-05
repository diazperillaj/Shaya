import React, { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { logout } from "../../features/auth/service";
import { useNavigate } from "react-router-dom";
import { menuItems } from "../../config/menuConfig";

/**
 * Tipo de la función encargada de cambiar
 * el item activo del menú.
 */
type SetActiveMenuItem = (item: number) => void;

/**
 * Props del componente Sidebar.
 */
interface SidebarProps {
  /** Contenido principal renderizado a la derecha del sidebar */
  children: React.ReactNode;

  /** Callback para cambiar la vista activa del menú */
  setActiveMenuItem: SetActiveMenuItem;
}

/**
 * Componente Sidebar.
 *
 * Renderiza el menú lateral de navegación de la aplicación,
 * incluyendo:
 * - Logo y branding
 * - Menú de navegación principal
 * - Botón para colapsar/expandir
 * - Acción de cierre de sesión
 *
 * El sidebar controla únicamente su estado visual
 * (abierto/cerrado) y delega la navegación al componente padre.
 */
function Sidebar({ children, setActiveMenuItem }: SidebarProps) {
  /**
   * Indica si el sidebar se encuentra expandido.
   */
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  /**
   * Definición de los ítems del menú principal.
   * Cada ítem representa una sección de la aplicación.
   */

  /** Hook de navegación de React Router */
  const navigate = useNavigate();

  /**
   * Maneja el cierre de sesión del usuario.
   *
   * Ejecuta el logout, limpia la sesión y
   * redirige a la pantalla de login.
   */
  const handleLogout = async (): Promise<void> => {
    try {
      await logout();
      navigate("/login");
    } catch (err: any) {
      alert(err.message);
    }
  };

  /**
   * Alterna el estado del sidebar
   * entre expandido y colapsado.
   */
  const toggleSidebar = (): void => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Backdrop (solo móvil, con sidebar abierto): al tocar, cierra */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 md:hidden"
          onClick={toggleSidebar}
          aria-hidden
        />
      )}

      {/* Botón flotante para abrir (solo móvil, con sidebar cerrado).
          Va superpuesto sobre el contenido: no desplaza el layout. */}
      {!isSidebarOpen && (
        <button
          onClick={toggleSidebar}
          className="fixed bottom-4 left-4 z-50 md:hidden p-2 rounded-lg bg-emerald-900 text-white shadow-lg hover:bg-emerald-800 transition-all duration-200"
          aria-label="Abrir menú"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      )}

      {/* Sidebar.
          Móvil: fixed (overlay, no empuja el contenido); cerrado se oculta
          deslizándose fuera de pantalla.
          Escritorio: relative en el flujo, alterna ancho w-72 / w-20. */}
      <div
        className={`fixed md:relative z-40 h-screen flex flex-col bg-gradient-to-b from-emerald-900 via-emerald-800 to-emerald-900 text-white transition-all duration-300 ease-in-out shadow-2xl ${isSidebarOpen ? "w-72 translate-x-0" : "w-20 -translate-x-full md:translate-x-0"}`}
      >
        {/* Logo/Header */}
        <div className="px-6 py-8 border-b border-emerald-700/50">
          <div
            className={`flex items-center gap-3 transition-all duration-300 ${isSidebarOpen ? "justify-start" : "justify-center"}`}
          >
            <div className="w-10 h-10 rounded-xl shadow-lg transform hover:scale-110 transition-transform duration-200 flex-shrink-0">
              <img src="/logo.png" alt="Shaya Café" className="w-full h-full object-contain" />
            </div>
            {isSidebarOpen && (
              <div className="overflow-hidden">
                <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-white to-emerald-100 bg-clip-text text-transparent">
                  Shaya Café
                </h1>
                <p className="text-xs text-emerald-300 mt-0.5">
                  Sistema de gestión
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Menu Items */}
        <nav className="flex-1 overflow-y-auto px-3 py-6 space-y-1 scrollbar-thin scrollbar-thumb-emerald-700 scrollbar-track-transparent">
          {menuItems.map((item, index) => {
            const Icon = item.icon;
            return (
              <div
                key={item.name}
                className={`group relative flex items-center gap-4 px-4 py-3.5 rounded-xl cursor-pointer transition-all duration-200 hover:bg-emerald-800/60 hover:shadow-lg hover:translate-x-1 ${isSidebarOpen ? "" : "justify-center"}`}
                style={{ animationDelay: `${index * 50}ms` }}
                onClick={() => setActiveMenuItem(Number(item.id))}
              >
                <div className="flex items-center justify-center w-5 h-5 text-emerald-200 group-hover:text-white group-hover:scale-110 transition-all duration-200">
                  {<Icon className="w-5 h-5" />}
                </div>

                {isSidebarOpen && (
                  <span className="text-sm font-medium text-emerald-50 group-hover:text-white transition-colors duration-200">
                    {item.name}
                  </span>
                )}
              </div>
            );
          })}
        </nav>

        {/* Toggle Button */}
        <div className="px-4 py-4 border-t border-emerald-700/50">
          <button
            onClick={toggleSidebar}
            className="w-full flex items-center justify-center p-3 rounded-xl bg-emerald-800/50 hover:bg-emerald-700/60 transition-all duration-200 group shadow-lg hover:shadow-xl"
            aria-label={isSidebarOpen ? "Cerrar sidebar" : "Abrir sidebar"}
          >
            {isSidebarOpen ? (
              <ChevronLeft className="w-5 h-5 text-emerald-200 group-hover:text-white transition-colors duration-200" />
            ) : (
              <ChevronRight className="w-5 h-5 text-emerald-200 group-hover:text-white transition-colors duration-200" />
            )}
          </button>
          <p className="cursor-pointer text-xs text-emerald-300 mt-2">
            <a onClick={handleLogout}>Cerrar sesión</a>
          </p>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 p-8 overflow-auto">{children}</main>
      </div>
    </div>
  );
}

export default Sidebar;
