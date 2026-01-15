// src/features/users/types.ts
export interface User {
  id: number;
  name: string;
  document: string;
  username: string;
  hashed_password?: string;
  email: string;
  phone: string;
  role: string;
  observation?: string
}
