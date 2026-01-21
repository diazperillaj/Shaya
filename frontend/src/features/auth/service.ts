import type { LoginPayload, User } from "./schema"

const API_URL = "http://localhost:8000/api/v1/auth"

export async function login(payload: LoginPayload): Promise<void> {
  const res = await fetch(`${API_URL}/login`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.detail || "Error al iniciar sesión")
  }
}

export async function getMe(): Promise<User> {
  const res = await fetch(`${API_URL}/me`, {
    credentials: "include",
  })

  if (!res.ok) {
    throw new Error("No autenticado")
  }

  return res.json()
}

export async function logout(): Promise<void> {
  await fetch(`${API_URL}/logout`, {
    method: "POST",
    credentials: "include",
  })
}
