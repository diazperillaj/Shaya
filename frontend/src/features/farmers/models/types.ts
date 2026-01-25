// src/features/farmers/types.ts
export interface Farmer {
  id: number;
  name: string;
  document: string;
  email: string;
  farm_name: string;
  farm_location: string;
  phone: string;
  observation?: string
}

export interface FarmersQuery {
  search?: string
}


