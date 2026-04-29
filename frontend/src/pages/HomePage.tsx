// src/pages/Dashboard.jsx
import { useState } from "react";
import MainLayout from "../components/layout/MainLayout";
import UsersPage from "../features/users/UsersPage";
import FarmersPage from "../features/farmers/FarmersPage";
import CustomersPage from "../features/customers/CustomersPage";
import InventorysPage from "../features/inventory/InventoryPage";
import InventoryProcessedPage from "../features/inventoryProcessed/InventoryProcessedPage";
import ProductsPage from "../features/products/ProductsPage";
import SalesPage from "../features/fast_sales/SalesPage";


export default function Dashboard() {
  const [activeMenuItem, setActiveMenuItem] = useState(0);

  return (
    <MainLayout setActiveMenuItem={setActiveMenuItem}>
      <div className="min-w-[700px] overflow-x-auto p-4">
        {(() => {
          switch (activeMenuItem) {
            case 0:
              return <h1>Inicio</h1>;
            case 1:
              return <InventoryProcessedPage setActiveMenuItem={setActiveMenuItem} />;
            case 2:
              return <SalesPage />;
            case 3:
              return <CustomersPage />;
            case 4:
              return <FarmersPage />;
            case 5:
              return <UsersPage />;
            case 6:
              return <InventorysPage setActiveMenuItem={setActiveMenuItem} />;
            case 7:
              return <ProductsPage  />;
            default:
              return <h1>Inicio</h1>;
          }
        })()}
      </div>
    </MainLayout>
  );
}
