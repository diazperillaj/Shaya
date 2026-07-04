import { useState } from "react";
import MainLayout from "../components/layout/MainLayout";
import { menuItems } from "../config/menuConfig";

export default function Dashboard() {
  const [activeMenuItem, setActiveMenuItem] = useState(0);

  const active = menuItems.find((m) => m.id === activeMenuItem);
  const Component = active?.component;
  const extraProps = active?.props ?? {};

  return (
    <MainLayout setActiveMenuItem={setActiveMenuItem}>
      <div className="min-w-[700px] overflow-x-auto p-4">
        {Component ? (
          <Component setActiveMenuItem={setActiveMenuItem} {...extraProps} />
        ) : (
          <h1>Inicio</h1>
        )}
      </div>
    </MainLayout>
  );
}
