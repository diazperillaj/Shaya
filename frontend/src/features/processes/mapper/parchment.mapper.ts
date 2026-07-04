// features/parchment/mapper/parchment.mapper.ts

// ─────────────────────────────────────────────────────────────
// TIPOS
// ─────────────────────────────────────────────────────────────
export interface Parchment {
  id: number;
  altitude: string;
  variety: string;
  remaining_quantity: number;
  observation: string | null;

  farmer: {
    id: number;
    farm_name: string;
    municipality: string;
    village: string;

    person: {
      id: number;
      full_name: string;
      document: string;
      phone: string;
      email: string | null;
    };
  };
}

// ─────────────────────────────────────────────────────────────
// MAPPER
// ─────────────────────────────────────────────────────────────
export const mapParchmentFromApi = (p: any): Parchment => ({
  id: Number(p.id),
  altitude: p.altitude,
  variety: p.variety,
  remaining_quantity: Number(p.remaining_quantity),
  observation: p.observation ?? null,

  farmer: {
    id: Number(p.farmer.id),
    farm_name: p.farmer.farm_name,
    municipality: p.farmer.municipality,
    village: p.farmer.village,

    person: {
      id: Number(p.farmer.person.id),
      full_name: p.farmer.person.full_name,
      document: p.farmer.person.document,
      phone: p.farmer.person.phone,
      email: p.farmer.person.email,
    },
  },
})