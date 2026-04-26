import type { Product, ProductsQuery } from "../models/types";
import { mapProductFromApi } from "../mapper/product.mapper";

const BASE_URL = "http://localhost:8000/api/v1/products";

/* =======================
   GET
======================= */
export const fetchProducts = async (
  filters?: ProductsQuery,
): Promise<Product[]> => {
  const query = new URLSearchParams();

  if (filters?.search) query.append("search", filters?.search);

  const res = await fetch(`${BASE_URL}/get?${query.toString()}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Error obteniendo productos");

  const data = await res.json();

  console.log(data);

  return data.map(mapProductFromApi);
};

/* =======================
   CREATE
======================= */
export const createProduct = async (Product: Product): Promise<Product> => {
  const payload = {
    name: Product.name,
    quantity: Product.quantity,
    type: Product.type || 'processed',
    description: Product.description,
  };

  const res = await fetch(`${BASE_URL}/create`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || "Error creando producto");
  }

  if (!res.ok) throw new Error("Error creando producto");

  return mapProductFromApi(data);
};

/* =======================
   UPDATE
======================= */
export const updateProduct = async (Product: Product): Promise<Product> => {
  const payload = {
    name: Product.name,
    quantity: Product.quantity,
    type: Product.type || 'processed',
    description: Product.description,
  };

  const res = await fetch(`${BASE_URL}/update/${Product.id}`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();

  console.log(data.detail);

  if (!res.ok) {
    throw new Error(data.detail || "Error creando producto");
  }

  if (!res.ok) throw new Error("Error creando producto");

  return mapProductFromApi(data);
};

/* =======================
   DELETE
======================= */

export const deleteProduct = async (id: number): Promise<void> => {
  const res = await fetch(`${BASE_URL}/delete/${id}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!res.ok) throw new Error("Error eliminando producto");
};
