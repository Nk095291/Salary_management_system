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
  'Terminated',
] as const;

// TODO: Multi-currency — when salary-normalisation across currencies is
//       implemented, restore a CURRENCIES constant and expose currency
//       selection in the employee form and insights aggregation.
export const CURRENCIES = ['USD'] as const;

export const ALLOWED_COUNTRIES = [
  'Australia',
  'Canada',
  'Germany',
  'India',
  'United Kingdom',
  'United States',
] as const;

export type AllowedCountry = (typeof ALLOWED_COUNTRIES)[number];

export interface DepartmentOption {
  name: string;
  job_titles: string[];
}

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

export interface InsightsOverview {
  total_employees: number;
  avg_salary: number;
  highest_paid_country: string | null;
  gender_distribution: Record<string, number>;
}

export interface CountryInsight {
  country: string;
  headcount: number;
  min_salary: number;
  max_salary: number;
  avg_salary: number;
  median_salary: number;
}

export interface DepartmentInsight {
  department: string;
  headcount: number;
  avg_salary: number;
  total_payroll: number;
}

export interface JobTitleInsight {
  job_title: string;
  avg_salary: number;
  headcount: number;
  seniority_breakdown: Record<string, number>;
}

export interface PayEquityInsight {
  department: string;
  male_avg: number;
  female_avg: number;
  gap_percent: number;
}
