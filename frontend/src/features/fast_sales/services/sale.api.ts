// src/features/sales/service.ts
import { useAuth } from '../../auth/AuthContext'
import type { Sale, SalesQuery } from '../models/types'
import { mapSaleFromApi } from '../mapper/sale.mapper'

const BASE_URL = "http://localhost:8000/api/v1/fast-sale";
const PRODUCT_URL = "http://localhost:8000/api/v1/products";

/**
 * Hook personalizado para el servicio de ventas.
 * * Se convierte en un hook para poder consumir `useAuth` y
 * asignar automáticamente el vendedor según el usuario activo.
 */

export interface ProductOption {
  label: string
  value: number
}

export const getProducts = async (): Promise<ProductOption[]> => {
  const res = await fetch(`${PRODUCT_URL}/get`, { credentials: 'include' })
  const data = await res.json()

  return data.map((f: any) => ({
    label: `ID: ${f.id} - ${f.name}`,
    value: f.id,
  }))
}

export const useSalesService = () => {
  const { user } = useAuth();

  /* =======================
     GET
  ======================= */
  const fetchSales = async (filters?: SalesQuery): Promise<Sale[]> => {
    const query = new URLSearchParams();

    if (filters?.search) query.append("search", filters.search);

    const res = await fetch(`${BASE_URL}/get?${query.toString()}`, {
      credentials: "include",
    });
    
    if (!res.ok) throw new Error("Error obteniendo ventas");

    const data = await res.json();

    return data.map(mapSaleFromApi);
  };

  /* =======================
     CREATE
  ======================= */
  const createSale = async (sale: Sale): Promise<Sale> => {
    const payload = {
      product_id: sale.product,
      quantity: sale.quantity,
      price: sale.price,
      // Asigna automáticamente el usuario activo. 
      // Ajusta 'user.name' según las propiedades de tu interface User.
      user_id: user?.id || 'Desconocido', 
      description: sale.description,
    };

    const res = await fetch(`${BASE_URL}/create`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Error creando venta");
    }

    return mapSaleFromApi(data);
  };

  /* =======================
     UPDATE
  ======================= */
  const updateSale = async (sale: Sale): Promise<Sale> => {
    const payload = {
      product_id: sale.product,
      quantity: sale.quantity,
      price: sale.price,
      // Mantiene el usuario activo como vendedor al actualizar
      user_id: user?.id || 'Desconocido',
      description: sale.description,
    };

    const res = await fetch(`${BASE_URL}/update/${sale.id}`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Error actualizando venta");
    }

    return mapSaleFromApi(data);
  };

  /* =======================
     DELETE
  ======================= */
  const deleteSale = async (id: number): Promise<void> => {
    const res = await fetch(`${BASE_URL}/delete/${id}`, {
      method: "DELETE",
      credentials: "include",
    });

    if (!res.ok) throw new Error("Error eliminando venta");
  };

  return {
    fetchSales,
    createSale,
    updateSale,
    deleteSale,
  };
};