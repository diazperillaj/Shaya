export const mapFarmerFromApi = (u: any) => ({
  id: u.id,
  name: u.person.full_name,
  document: u.person.document,
  email: u.person.email,
  farm_name: u.farm_name,
  farm_location: u.farm_location,
  phone: u.person.phone,
  observation: u.person.observation || "Sin observacion",
})
