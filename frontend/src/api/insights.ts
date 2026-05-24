import { apiRequest } from './client';
import type {
  CountryInsight,
  DepartmentInsight,
  InsightsOverview,
  JobTitleInsight,
  PayEquityInsight,
} from '../types/api';

export function getInsightsOverview(): Promise<InsightsOverview> {
  return apiRequest<InsightsOverview>('/api/insights/overview/');
}

export function getInsightsByCountry(): Promise<CountryInsight[]> {
  return apiRequest<CountryInsight[]>('/api/insights/by-country/');
}

export function getInsightsByDepartment(): Promise<DepartmentInsight[]> {
  return apiRequest<DepartmentInsight[]>('/api/insights/by-department/');
}

export interface JobTitleInsightsFilters {
  countries?: string[];
  departments?: string[];
  job_titles?: string[];
}

export function getInsightsByJobTitle(
  filters: JobTitleInsightsFilters = {},
): Promise<JobTitleInsight[]> {
  const params = new URLSearchParams();
  if (filters.countries) {
    for (const country of filters.countries) {
      params.append('countries', country);
    }
  }
  if (filters.departments) {
    for (const department of filters.departments) {
      params.append('departments', department);
    }
  }
  if (filters.job_titles) {
    for (const jobTitle of filters.job_titles) {
      params.append('job_titles', jobTitle);
    }
  }
  const qs = params.toString();
  return apiRequest<JobTitleInsight[]>(
    qs ? `/api/insights/by-job-title/?${qs}` : '/api/insights/by-job-title/',
  );
}

export function getInsightsPayEquity(): Promise<PayEquityInsight[]> {
  return apiRequest<PayEquityInsight[]>('/api/insights/pay-equity/');
}
