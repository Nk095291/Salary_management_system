export const GENDERS = [
  'Male',
  'Female',
  'Non-binary',
  'Prefer not to say',
] as const;

export const SENIORITY_LEVELS = [
  'Junior',
  'Mid',
  'Senior',
  'Lead',
  'Principal',
] as const;

export const EMPLOYMENT_TYPES = [
  'Full-time',
  'Part-time',
  'Contract',
  'Internship',
] as const;

export const EMPLOYEE_STATUSES = [
  'Active',
  'On Leave',
  'Terminated',
] as const;

export const CURRENCIES = ['USD', 'INR', 'GBP', 'EUR', 'AUD', 'CAD'] as const;

export type Gender = (typeof GENDERS)[number];
export type SeniorityLevel = (typeof SENIORITY_LEVELS)[number];
export type EmploymentType = (typeof EMPLOYMENT_TYPES)[number];
export type EmployeeStatus = (typeof EMPLOYEE_STATUSES)[number];
export type Currency = (typeof CURRENCIES)[number];

export interface EmployeeSummary {
  id: number;
  job_title: string;
  department: string;
  country: string;
}

export interface HRUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  employee: EmployeeSummary | null;
}

export interface Employee {
  id: number;
  first_name: string;
  last_name: string;
  personal_email: string;
  company_email: string;
  gender: Gender;
  date_of_birth: string | null;
  department: string;
  job_title: string;
  seniority_level: SeniorityLevel;
  employment_type: EmploymentType;
  country: string;
  salary: string;
  currency: Currency;
  date_joining: string;
  date_relieving: string | null;
  status: EmployeeStatus;
  created_at: string;
  updated_at: string;
}

export type EmployeePayload = Omit<
  Employee,
  'id' | 'created_at' | 'updated_at'
>;

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface ApiErrorBody {
  detail?: string;
  [key: string]: string | string[] | undefined;
}
