import { apiRequest } from './client';
import type {
  Employee,
  EmployeePayload,
  PaginatedResponse,
} from '../types/api';

export interface EmployeeListParams {
  page?: number;
  page_size?: number;
  department?: string;
  country?: string;
  status?: string;
}

export async function listEmployees(
  params: EmployeeListParams = {},
): Promise<PaginatedResponse<Employee>> {
  const search = new URLSearchParams();
  if (params.page) search.set('page', String(params.page));
  if (params.page_size) search.set('page_size', String(params.page_size));
  if (params.department) search.set('department', params.department);
  if (params.country) search.set('country', params.country);
  if (params.status) search.set('status', params.status);

  const qs = search.toString();
  const path = qs ? `/api/employees/?${qs}` : '/api/employees/';
  return apiRequest<PaginatedResponse<Employee>>(path);
}

export async function getEmployee(id: number): Promise<Employee> {
  return apiRequest<Employee>(`/api/employees/${id}/`);
}

export async function createEmployee(data: EmployeePayload): Promise<Employee> {
  return apiRequest<Employee>('/api/employees/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateEmployee(
  id: number,
  data: Partial<EmployeePayload>,
): Promise<Employee> {
  return apiRequest<Employee>(`/api/employees/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteEmployee(id: number): Promise<void> {
  return apiRequest<void>(`/api/employees/${id}/`, {
    method: 'DELETE',
  });
}
