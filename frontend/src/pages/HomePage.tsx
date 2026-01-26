// src/pages/Dashboard.jsx
import { useState } from "react";
import MainLayout from "../components/layout/MainLayout";
import UsersPage from "../features/users/UsersPage";
import FarmersPage from "../features/farmers/FarmersPage";
import CustomersPage from "../features/customers/CustomersPage";


export default function Dashboard() {
  const [activeMenuItem, setActiveMenuItem] = useState(0);

  console.log(activeMenuItem);

  return (
    <MainLayout setActiveMenuItem={setActiveMenuItem}>
      <div className="min-w-[700px] overflow-x-auto p-4">
        {(() => {
          switch (activeMenuItem) {
            case 0:
              return <h1>Inicio</h1>;
            case 1:
              return <h1>Inventario</h1>;
            case 2:
              return <h1>Ventas</h1>;
            case 3:
              return <CustomersPage />;
            case 4:
              return <FarmersPage />;
            case 5:
              return <UsersPage />;
            default:
              return <h1>Inicio</h1>;
          }
        })()}
      </div>
    </MainLayout>
  );
}
