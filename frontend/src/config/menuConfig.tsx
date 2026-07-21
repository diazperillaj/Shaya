import type { LucideIcon } from "lucide-react";
import {
  Home,
  ShoppingBag,
  Coffee,
  Newspaper,
  Store,
  Users,
  Wheat,
  Clipboard,
  PersonStanding,
  UserCog,
  ArrowRightLeft,
  Receipt,
  Bot,
} from "lucide-react";
import type { ComponentType } from "react";

import DashboardPage from "../features/dashboard/DashboardPage";
import SalesPage from "../features/sales/SalesPage";
import RoastedCoffeePage from "../features/roasted_coffee/RoastedCoffeePage";
import InventoryProcessedPage from "../features/processes/InventoryProcessedPage";
import FairsPage from "../features/fairs/FairsPage";
import CustomersPage from "../features/customers/CustomersPage";
import ProductsPage from "../features/products/ProductsPage";
import InventorysPage from "../features/inventory/InventoryPage";
import FarmersPage from "../features/farmers/FarmersPage";
import MovementsPage from "../features/roasted_movements/MovementsPage";
import UsersPage from "../features/users/UsersPage";
import ExpensesPage from "../features/expenses/ExpensesPage";
import ChatPage from "../features/chat/ChatPage";

export interface MenuItem {
  id: number;
  name: string;
  icon: LucideIcon;
  label: string;
  component: ComponentType<any>;
  props?: Record<string, unknown>;
  /** true = la página ocupa todo el alto y maneja su propio scroll (ej. chat) */
  fluid?: boolean;
}

export const menuItems: MenuItem[] = [
  {
    id: 0,
    name: "Inicio",
    icon: Home,
    label: "home",
    component: DashboardPage,
  },
  {
    id: 1,
    name: "Ventas",
    icon: ShoppingBag,
    label: "sales",
    component: SalesPage,
  },
  {
    id: 11,
    name: "Gastos",
    icon: Receipt,
    label: "expenses",
    component: ExpensesPage,
  },
  {
    id: 2,
    name: "Maquilado",
    icon: Coffee,
    label: "roasted_coffee",
    component: RoastedCoffeePage,
  },
  {
    id: 3,
    name: "Procesos",
    icon: Newspaper,
    label: "processes",
    component: InventoryProcessedPage,
  },
  { id: 4, name: "Ferias", icon: Store, label: "fairs", component: FairsPage },
  {
    id: 5,
    name: "Clientes",
    icon: Users,
    label: "clients",
    component: CustomersPage,
  },
  {
    id: 6,
    name: "Productos",
    icon: Wheat,
    label: "products",
    component: ProductsPage,
  },
  {
    id: 7,
    name: "Inventario",
    icon: Clipboard,
    label: "inventory",
    component: InventorysPage,
  },
  {
    id: 8,
    name: "Caficultores",
    icon: PersonStanding,
    label: "farmers",
    component: FarmersPage,
  },
  {
    id: 9,
    name: "Movimientos",
    icon: ArrowRightLeft,
    label: "movements",
    component: MovementsPage,
  },
  {
    id: 10,
    name: "Usuarios",
    icon: UserCog,
    label: "users",
    component: UsersPage,
  },
  {
    id: 12,
    name: "Asistente",
    icon: Bot,
    label: "assistant",
    component: ChatPage,
    fluid: true,
  },
];
