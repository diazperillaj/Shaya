import { useState } from "react";
import { useLocation } from "react-router-dom";
import MainLayout from "../components/layout/MainLayout";
import { menuItems } from "../config/menuConfig";

export default function Dashboard() {
  // Vista inicial: la que se pidió al volver desde otra ruta (p. ej. Cultivo)
  const location = useLocation();
  const [activeMenuItem, setActiveMenuItemState] = useState<number>(
    () => (location.state as { menuItem?: number } | null)?.menuItem ?? 0
  );
  // Módulo anterior: el Asistente lo usa para sugerir preguntas del contexto
  // desde el que venía el usuario (ej. Clientes → preguntas de clientes).
  const [previousMenuItem, setPreviousMenuItem] = useState<number | null>(null);

  const setActiveMenuItem = (id: number): void => {
    if (id !== activeMenuItem) {
      setPreviousMenuItem(activeMenuItem);
    }
    setActiveMenuItemState(id);
  };

  const active = menuItems.find((m) => m.id === activeMenuItem);
  const Component = active?.component;
  const extraProps = active?.props ?? {};

  return (
    <MainLayout setActiveMenuItem={setActiveMenuItem}>
      <div
        className={
          // fluid (ej. chat): ocupa todo el alto y maneja su propio scroll.
          // Resto de páginas: comportamiento original (tablas anchas).
          active?.fluid ? "h-full min-h-0" : "min-w-[700px] overflow-x-auto p-4"
        }
      >
        {Component ? (
          <Component
            setActiveMenuItem={setActiveMenuItem}
            previousMenuItem={previousMenuItem}
            {...extraProps}
          />
        ) : (
          <h1>Inicio</h1>
        )}
      </div>
    </MainLayout>
  );
}
