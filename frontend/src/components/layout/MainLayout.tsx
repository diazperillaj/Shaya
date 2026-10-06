import React, { useState } from "react";
import { ChevronLeft, ChevronRight, LogOut, Menu } from "lucide-react";
import { logout } from "../../features/auth/service";
import { useAuth } from "../../features/auth/AuthContext";
import { hasRole } from "../../features/auth/roles";
import { useLocation, useNavigate } from "react-router-dom";
import { menuItems, type MenuItem } from "../../config/menuConfig";
import ThemeToggle from "../../theme/ThemeToggle";

/**
 * Tipo de la función encargada de cambiar
 * el item activo del menú.
 */
type SetActiveMenuItem = (item: number) => void;

/**
 * Indica si la pantalla es de celular (menor al breakpoint `md` de
 * Tailwind), donde el sidebar es un panel superpuesto al contenido.
 */
const isSmallScreen = (): boolean =>
  window.matchMedia("(max-width: 767px)").matches;

/**
 * Props del componente Sidebar.
 */
interface SidebarProps {
  /** Contenido principal renderizado a la derecha del sidebar */
  children: React.ReactNode;

  /**
   * Callback para cambiar la vista activa del menú. Solo lo pasa el inicio;
   * desde otras rutas (p. ej. Cultivo), elegir una de esas vistas vuelve al
   * inicio con ella abierta.
   */
  setActiveMenuItem?: SetActiveMenuItem;

  /** Vista del inicio que está abierta (para marcarla en el menú) */
  activeMenuItem?: number;
}

/**
 * Componente Sidebar.
 *
 * Renderiza el menú lateral de navegación de la aplicación,
 * incluyendo:
 * - Logo y branding
 * - Menú de navegación principal, con la sección actual marcada
 * - Modo claro / oscuro, cierre de sesión y botón para colapsar
 *
 * El sidebar controla únicamente su estado visual
 * (abierto/cerrado) y delega la navegación al componente padre.
 */
function Sidebar({ children, setActiveMenuItem, activeMenuItem }: SidebarProps) {
  /**
   * Indica si el sidebar se encuentra expandido.
   * En el celular arranca cerrado para no tapar el contenido.
   */
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => !isSmallScreen());

  /** Hook de navegación de React Router */
  const navigate = useNavigate();
  const { pathname } = useLocation();

  /** Usuario autenticado: el menú muestra solo las secciones de su rol */
  const { user } = useAuth();
  const visibleItems = menuItems.filter((item) => hasRole(user?.role, item.roles));

  /** La sección actual: por su ruta propia, o la vista abierta en el inicio */
  const isActive = (item: MenuItem): boolean =>
    item.path ? pathname.startsWith(item.path) : pathname === "/" && item.id === activeMenuItem;

  /**
   * Abre la sección elegida en el menú.
   *
   * Las secciones con ruta propia navegan a ella; las demás son vistas del
   * inicio y se abren ahí.
   */
  const handleSelect = (item: MenuItem): void => {
    if (item.path) {
      navigate(item.path);
    } else if (setActiveMenuItem) {
      setActiveMenuItem(item.id);
    } else {
      navigate("/", { state: { menuItem: item.id } });
    }

    // En el celular el menú tapa el contenido: se cierra al elegir
    if (isSmallScreen()) {
      setIsSidebarOpen(false);
    }
  };

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
    <div className="flex h-[100dvh] bg-gradient-to-br from-gray-50 to-gray-100 dark:from-[rgb(var(--page))] dark:to-[rgb(var(--page))]">
      {/* Backdrop (solo móvil, con sidebar abierto): al tocar, cierra */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 md:hidden animate-fadeIn"
          onClick={toggleSidebar}
          aria-hidden
        />
      )}

      {/* Botón flotante para abrir (solo móvil, con sidebar cerrado).
          Va superpuesto sobre el contenido: no desplaza el layout. */}
      {!isSidebarOpen && (
        <button
          onClick={toggleSidebar}
          className="fixed bottom-4 left-4 z-50 md:hidden flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-900 text-white shadow-lg transition-[transform,background-color] duration-150 ease-out hover:bg-emerald-800 active:scale-[0.96]"
          aria-label="Abrir menú"
        >
          <Menu className="w-5 h-5" />
        </button>
      )}

      {/* Sidebar.
          Móvil: fixed (overlay, no empuja el contenido); cerrado se oculta
          deslizándose fuera de pantalla.
          Escritorio: relative en el flujo, alterna ancho w-72 / w-20. */}
      <aside
        className={`fixed md:relative z-40 h-[100dvh] flex flex-col bg-gradient-to-b from-emerald-900 via-emerald-800 to-emerald-900 dark:from-[#0c2a21] dark:via-[#0f3328] dark:to-[#0c2a21] dark:border-r dark:border-white/5 text-white transition-[width,transform] duration-300 ease-out shadow-2xl md:shadow-xl ${isSidebarOpen ? "w-72 translate-x-0" : "w-20 -translate-x-full md:translate-x-0"}`}
      >
        {/* Logo/Header */}
        <div className="px-5 py-7 border-b border-white/10">
          <div
            className={`flex items-center gap-3 ${isSidebarOpen ? "justify-start" : "justify-center"}`}
          >
            <div className="w-10 h-10 rounded-xl flex-shrink-0">
              <img src="/logo.png" alt="Shaya Café" className="w-full h-full object-contain" />
            </div>
            {isSidebarOpen && (
              <div className="overflow-hidden text-left">
                <h1 className="text-xl font-bold tracking-tight text-white">
                  Shaya Café
                </h1>
                <p className="text-xs text-emerald-200/80 mt-0.5">
                  Sistema de gestión
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Menu Items */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1 [scrollbar-color:rgb(255_255_255/0.2)_transparent]" aria-label="Secciones">
          {visibleItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item);
            return (
              <button
                type="button"
                key={item.name}
                onClick={() => handleSelect(item)}
                aria-current={active ? "page" : undefined}
                aria-label={isSidebarOpen ? undefined : item.name}
                title={isSidebarOpen ? undefined : item.name}
                className={`group flex w-full items-center gap-4 rounded-xl px-4 py-3 text-left transition-[background-color,color,transform] duration-150 ease-out active:scale-[0.98] focus-visible:outline-white/70 ${isSidebarOpen ? "" : "justify-center"} ${
                  active
                    ? "bg-white/15 text-white shadow-[inset_0_1px_0_rgb(255_255_255/0.08)]"
                    : "text-emerald-100/90 hover:bg-white/10 hover:text-white"
                }`}
              >
                <Icon
                  className={`w-5 h-5 flex-shrink-0 transition-colors duration-150 ${active ? "text-white" : "text-emerald-200 group-hover:text-white"}`}
                />
                {isSidebarOpen && (
                  <span className={`text-sm ${active ? "font-semibold" : "font-medium"}`}>
                    {item.name}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Pie: tema, sesión y colapsar */}
        <div className="px-3 py-3 border-t border-white/10 space-y-1">
          <ThemeToggle showLabel={isSidebarOpen} />
          <button
            type="button"
            onClick={handleLogout}
            aria-label={isSidebarOpen ? undefined : "Cerrar sesión"}
            title={isSidebarOpen ? undefined : "Cerrar sesión"}
            className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-emerald-100 transition-[transform,background-color,color] duration-150 ease-out hover:bg-white/10 hover:text-white active:scale-[0.98] ${isSidebarOpen ? "" : "justify-center"}`}
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            {isSidebarOpen && <span>Cerrar sesión</span>}
          </button>
          <button
            type="button"
            onClick={toggleSidebar}
            className="flex w-full items-center justify-center rounded-xl p-2.5 text-emerald-200 transition-[transform,background-color,color] duration-150 ease-out hover:bg-white/10 hover:text-white active:scale-[0.98]"
            aria-label={isSidebarOpen ? "Contraer el menú" : "Expandir el menú"}
            title={isSidebarOpen ? "Contraer el menú" : "Expandir el menú"}
          >
            {isSidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 px-4 py-6 md:p-8 overflow-auto">{children}</main>
      </div>
    </div>
  );
}

export default Sidebar;
