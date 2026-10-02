import type { Employee, EmployeePayload } from '../models/types'
import { request } from './http'

export const fetchEmployees = async (farmId: number): Promise<Employee[]> =>
  request<Employee[]>('/employees/get', 'Error obteniendo los empleados', {
    query: { farm_id: farmId },
  })

export const createEmployee = async (farmId: number, payload: EmployeePayload): Promise<Employee> =>
  request<Employee>('/employees/create', 'Error creando el empleado', {
    method: 'POST',
    body: { farm_id: farmId, ...payload },
  })

export const updateEmployee = async (id: number, payload: EmployeePayload): Promise<Employee> =>
  request<Employee>(`/employees/update/${id}`, 'Error actualizando el empleado', {
    method: 'PUT',
    body: payload,
  })

export const setEmployeeActive = async (id: number, active: boolean): Promise<Employee> =>
  request<Employee>(
    `/employees/${id}/${active ? 'activate' : 'deactivate'}`,
    active ? 'Error activando el empleado' : 'Error desactivando el empleado',
    { method: 'POST' },
  )

export const deleteEmployee = async (id: number): Promise<void> => {
  await request(`/employees/delete/${id}`, 'Error eliminando el empleado', { method: 'DELETE' })
}
