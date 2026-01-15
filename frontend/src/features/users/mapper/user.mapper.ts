export const mapUserFromApi = (u: any) => ({
  id: u.id,
  name: u.person.full_name,
  document: u.person.document,
  username: u.username,
  email: u.person.email,
  phone: u.person.phone,
  role: u.role,
  observation: u.person.observation,
})
