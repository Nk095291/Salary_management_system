import { useCallback, useEffect, useMemo, useState } from 'react';
import { getDepartments } from '../api/employees';
import {
  getInsightsByCountry,
  getInsightsByDepartment,
  getInsightsByJobTitle,
  getInsightsOverview,
  getInsightsPayEquity,
} from '../api/insights';
import { CountryLabel } from '../components/CountryLabel';
import { MultiSelect } from '../components/MultiSelect';
import type {
  CountryInsight,
  DepartmentInsight,
  DepartmentOption,
  InsightsOverview,
  JobTitleInsight,
  PayEquityInsight,
} from '../types/api';
import { GENDERS } from '../types/api';
import { formatSalary } from '../utils/currency';

type InsightsTab = 'overview' | 'country' | 'department' | 'job-title' | 'pay-equity';

const TABS: { id: InsightsTab; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'country', label: 'By country' },
  { id: 'department', label: 'By department' },
  { id: 'job-title', label: 'By job title' },
  { id: 'pay-equity', label: 'Pay equity' },
];

function formatCount(value: number): string {
  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 0,
  }).format(value);
}

function formatAvg(value: number): string {
  return value > 0 ? formatSalary(value) : '—';
}

export function InsightsPage() {
  const [activeTab, setActiveTab] = useState<InsightsTab>('overview');
  const [overview, setOverview] = useState<InsightsOverview | null>(null);
  const [countries, setCountries] = useState<CountryInsight[]>([]);
  const [departments, setDepartments] = useState<DepartmentInsight[]>([]);
  const [payEquity, setPayEquity] = useState<PayEquityInsight[]>([]);
  const [jobTitles, setJobTitles] = useState<JobTitleInsight[]>([]);
  const [departmentOptions, setDepartmentOptions] = useState<DepartmentOption[]>([]);

  const [selectedCountries, setSelectedCountries] = useState<string[]>([]);
  const [selectedDepartments, setSelectedDepartments] = useState<string[]>([]);
  const [selectedJobTitles, setSelectedJobTitles] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [jobTitleLoading, setJobTitleLoading] = useState(false);
  const [error, setError] = useState('');

  const countryOptions = useMemo(
    () => countries.map((c) => c.country),
    [countries],
  );

  const departmentFilterOptions = useMemo(
    () => departmentOptions.map((d) => d.name),
    [departmentOptions],
  );

  const jobTitleOptions = useMemo(() => {
    const sourceDepartments = selectedDepartments.length
      ? departmentOptions.filter((d) => selectedDepartments.includes(d.name))
      : departmentOptions;
    const titles = new Set<string>();
    for (const dept of sourceDepartments) {
      for (const title of dept.job_titles) {
        titles.add(title);
      }
    }
    return [...titles].sort();
  }, [departmentOptions, selectedDepartments]);

  const loadMain = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [overviewData, countryData, departmentData, equityData, deptOptions] =
        await Promise.all([
          getInsightsOverview(),
          getInsightsByCountry(),
          getInsightsByDepartment(),
          getInsightsPayEquity(),
          getDepartments(),
        ]);
      setOverview(overviewData);
      setCountries(countryData);
      setDepartments(departmentData);
      setPayEquity(equityData);
      setDepartmentOptions(deptOptions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load insights.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMain();
  }, [loadMain]);

  useEffect(() => {
    let cancelled = false;
    async function loadJobTitles() {
      setJobTitleLoading(true);
      try {
        const data = await getInsightsByJobTitle({
          countries: selectedCountries.length ? selectedCountries : undefined,
          departments: selectedDepartments.length ? selectedDepartments : undefined,
          job_titles: selectedJobTitles.length ? selectedJobTitles : undefined,
        });
        if (!cancelled) {
          setJobTitles(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Failed to load job title insights.',
          );
        }
      } finally {
        if (!cancelled) {
          setJobTitleLoading(false);
        }
      }
    }
    loadJobTitles();
    return () => {
      cancelled = true;
    };
  }, [selectedCountries, selectedDepartments, selectedJobTitles]);

  useEffect(() => {
    setSelectedJobTitles((prev) => prev.filter((title) => jobTitleOptions.includes(title)));
  }, [jobTitleOptions]);

  if (loading) {
    return (
      <div className="page">
        <p className="muted">Loading salary insights…</p>
      </div>
    );
  }

  return (
    <div className="page insights-page">
      <div className="page-header">
        <div>
          <h2>Salary insights</h2>
          <p className="muted">Organization-wide compensation analytics for active employees.</p>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="insights-tabs" role="tablist" aria-label="Insights sections">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`insights-tab${activeTab === tab.id ? ' insights-tab--active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && overview && (
        <section className="card insights-panel" role="tabpanel">
          <h3>Overview</h3>
          <div className="stat-grid">
            <div className="stat-card">
              <span className="stat-label">Total employees</span>
              <span className="stat-value">{formatCount(overview.total_employees)}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Average salary</span>
              <span className="stat-value">{formatSalary(overview.avg_salary)}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Highest-paid country</span>
              <span className="stat-value">
                {overview.highest_paid_country ? (
                  <CountryLabel country={overview.highest_paid_country} />
                ) : (
                  '—'
                )}
              </span>
            </div>
          </div>
          <h4 className="subsection-title">Gender distribution (%)</h4>
          <div className="stat-grid">
            {GENDERS.map((gender) => (
              <div key={gender} className="stat-card">
                <span className="stat-label">{gender}</span>
                <span className="stat-value">{overview.gender_distribution[gender] ?? 0}%</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {activeTab === 'country' && (
        <section className="card insights-panel" role="tabpanel">
          <h3>By country</h3>
          {countries.length === 0 ? (
            <p className="muted table-message">No country data available.</p>
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Country</th>
                    <th className="col-num">Headcount</th>
                    <th className="col-num">Min</th>
                    <th className="col-num">Max</th>
                    <th className="col-num">Avg</th>
                    <th className="col-num">Median</th>
                  </tr>
                </thead>
                <tbody>
                  {countries.map((row) => (
                    <tr key={row.country}>
                      <td>
                        <CountryLabel country={row.country} />
                      </td>
                      <td className="col-num">{formatCount(row.headcount)}</td>
                      <td className="col-num">{formatSalary(row.min_salary)}</td>
                      <td className="col-num">{formatSalary(row.max_salary)}</td>
                      <td className="col-num">{formatSalary(row.avg_salary)}</td>
                      <td className="col-num">{formatSalary(row.median_salary)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {activeTab === 'department' && (
        <section className="card insights-panel" role="tabpanel">
          <h3>By department</h3>
          {departments.length === 0 ? (
            <p className="muted table-message">No department data available.</p>
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Department</th>
                    <th className="col-num">Headcount</th>
                    <th className="col-num">Avg salary</th>
                    <th className="col-num">Total payroll</th>
                  </tr>
                </thead>
                <tbody>
                  {departments.map((row) => (
                    <tr key={row.department}>
                      <td>{row.department}</td>
                      <td className="col-num">{formatCount(row.headcount)}</td>
                      <td className="col-num">{formatSalary(row.avg_salary)}</td>
                      <td className="col-num">{formatSalary(row.total_payroll)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {activeTab === 'job-title' && (
        <section className="card insights-panel" role="tabpanel">
          <h3>By job title</h3>
          <form
            className="filters"
            onSubmit={(e) => {
              e.preventDefault();
            }}
          >
            <MultiSelect
              label="Country"
              options={countryOptions}
              value={selectedCountries}
              onChange={setSelectedCountries}
              placeholder="All countries"
              searchPlaceholder="Search countries…"
              renderOption={(country) => <CountryLabel country={country} />}
            />
            <MultiSelect
              label="Department"
              options={departmentFilterOptions}
              value={selectedDepartments}
              onChange={setSelectedDepartments}
              placeholder="All departments"
              searchPlaceholder="Search departments…"
            />
            <MultiSelect
              label="Job title"
              options={jobTitleOptions}
              value={selectedJobTitles}
              onChange={setSelectedJobTitles}
              placeholder="All job titles"
              searchPlaceholder="Search job titles…"
            />
          </form>
          {jobTitleLoading ? (
            <p className="muted">Loading job titles…</p>
          ) : jobTitles.length === 0 ? (
            <p className="muted table-message">No job title data for the selected filters.</p>
          ) : (
            <div className="job-title-list">
              {jobTitles.map((row) => (
                <div key={row.job_title} className="job-title-card">
                  <div className="job-title-header">
                    <strong>{row.job_title}</strong>
                    <span className="muted">
                      {row.headcount} employees · avg {formatSalary(row.avg_salary)}
                    </span>
                  </div>
                  <div className="seniority-grid">
                    {Object.entries(row.seniority_breakdown).map(([level, avg]) => (
                      <div key={level} className="seniority-item">
                        <span className="stat-label">{level}</span>
                        <span>{formatSalary(avg)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {activeTab === 'pay-equity' && (
        <section className="card insights-panel" role="tabpanel">
          <h3>Pay equity by department</h3>
          <p className="muted panel">Average salary by gender. Gap % compares male vs female averages.</p>
          {payEquity.length === 0 ? (
            <p className="muted table-message">No pay equity data available.</p>
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Department</th>
                    <th className="col-num">Male avg</th>
                    <th className="col-num">Female avg</th>
                    <th className="col-num">Non-binary avg</th>
                    <th className="col-num">Prefer not to say avg</th>
                    <th className="col-num">M vs F gap %</th>
                  </tr>
                </thead>
                <tbody>
                  {payEquity.map((row) => (
                    <tr key={row.department}>
                      <td>{row.department}</td>
                      <td className="col-num">{formatAvg(row.male_avg)}</td>
                      <td className="col-num">{formatAvg(row.female_avg)}</td>
                      <td className="col-num">{formatAvg(row.non_binary_avg)}</td>
                      <td className="col-num">{formatAvg(row.prefer_not_to_say_avg)}</td>
                      <td className="col-num">
                        <span
                          className={
                            row.gap_percent > 5 ? 'gap-high' : 'gap-normal'
                          }
                        >
                          {row.gap_percent}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
