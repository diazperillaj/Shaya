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
  Sprout,
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
import { FARM_ROLES, STAFF_ROLES, type Role } from "../features/auth/roles";

export interface MenuItem {
  id: number;
  name: string;
  icon: LucideIcon;
  label: string;
  /** Roles que ven la sección en el menú (obligatorio: no hay acceso por defecto) */
  roles: readonly Role[];
  /** Vista que se abre dentro del inicio. No aplica a las secciones con `path`. */
  component?: ComponentType<any>;
  /** Ruta propia de la sección (p. ej. Cultivo); al elegirla se navega a ella */
  path?: string;
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
    roles: STAFF_ROLES,
    component: DashboardPage,
  },
  {
    id: 1,
    name: "Ventas",
    icon: ShoppingBag,
    label: "sales",
    roles: STAFF_ROLES,
    component: SalesPage,
  },
  {
    id: 11,
    name: "Gastos",
    icon: Receipt,
    label: "expenses",
    roles: STAFF_ROLES,
    component: ExpensesPage,
  },
  {
    id: 2,
    name: "Maquilado",
    icon: Coffee,
    label: "roasted_coffee",
    roles: STAFF_ROLES,
    component: RoastedCoffeePage,
  },
  {
    id: 3,
    name: "Procesos",
    icon: Newspaper,
    label: "processes",
    roles: STAFF_ROLES,
    component: InventoryProcessedPage,
  },
  {
    id: 4,
    name: "Ferias",
    icon: Store,
    label: "fairs",
    roles: STAFF_ROLES,
    component: FairsPage,
  },
  {
    id: 5,
    name: "Clientes",
    icon: Users,
    label: "clients",
    roles: STAFF_ROLES,
    component: CustomersPage,
  },
  {
    id: 6,
    name: "Productos",
    icon: Wheat,
    label: "products",
    roles: STAFF_ROLES,
    component: ProductsPage,
  },
  {
    id: 7,
    name: "Inventario",
    icon: Clipboard,
    label: "inventory",
    roles: STAFF_ROLES,
    component: InventorysPage,
  },
  {
    id: 8,
    name: "Caficultores",
    icon: PersonStanding,
    label: "farmers",
    roles: STAFF_ROLES,
    component: FarmersPage,
  },
  {
    id: 13,
    name: "Cultivo",
    icon: Sprout,
    label: "farm_operations",
    roles: FARM_ROLES,
    path: "/cultivo",
  },
  {
    id: 9,
    name: "Movimientos",
    icon: ArrowRightLeft,
    label: "movements",
    roles: STAFF_ROLES,
    component: MovementsPage,
  },
  {
    id: 10,
    name: "Usuarios",
    icon: UserCog,
    label: "users",
    roles: STAFF_ROLES,
    component: UsersPage,
  },
  {
    id: 12,
    name: "Asistente",
    icon: Bot,
    label: "assistant",
    roles: STAFF_ROLES,
    component: ChatPage,
    fluid: true,
  },
];
