import { apiRequest } from './client';
import type {
  DepartmentOption,
  Employee,
  EmployeePayload,
  PaginatedResponse,
} from '../types/api';

export interface EmployeeListParams {
  page?: number;
  page_size?: number;
  departments?: string[];
  countries?: string[];
  status?: string;
}

export async function listEmployees(
  params: EmployeeListParams = {},
): Promise<PaginatedResponse<Employee>> {
  const search = new URLSearchParams();
  if (params.page) search.set('page', String(params.page));
  if (params.page_size) search.set('page_size', String(params.page_size));
  if (params.departments) {
    for (const d of params.departments) {
      search.append('departments', d);
    }
  }
  if (params.countries) {
    for (const c of params.countries) {
      search.append('countries', c);
    }
  }
  if (params.status) search.set('status', params.status);

  const qs = search.toString();
  const path = qs ? `/api/employees/?${qs}` : '/api/employees/';
  return apiRequest<PaginatedResponse<Employee>>(path);
}

export async function getDepartments(): Promise<DepartmentOption[]> {
  return apiRequest<DepartmentOption[]>('/api/employees/departments/');
}

export async function getCountries(): Promise<string[]> {
  return apiRequest<string[]>('/api/employees/countries/');
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
