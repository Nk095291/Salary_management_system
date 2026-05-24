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

export function getInsightsByJobTitle(country: string): Promise<JobTitleInsight[]> {
  const params = new URLSearchParams({ country });
  return apiRequest<JobTitleInsight[]>(
    `/api/insights/by-job-title/?${params.toString()}`,
  );
}

export function getInsightsPayEquity(): Promise<PayEquityInsight[]> {
  return apiRequest<PayEquityInsight[]>('/api/insights/pay-equity/');
}
