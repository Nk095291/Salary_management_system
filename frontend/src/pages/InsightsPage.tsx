import { useCallback, useEffect, useState } from 'react';
import {
  getInsightsByCountry,
  getInsightsByDepartment,
  getInsightsByJobTitle,
  getInsightsOverview,
  getInsightsPayEquity,
} from '../api/insights';
import { CountryLabel } from '../components/CountryLabel';
import type {
  CountryInsight,
  DepartmentInsight,
  InsightsOverview,
  JobTitleInsight,
  PayEquityInsight,
} from '../types/api';
import { formatSalary } from '../utils/currency';

function formatCount(value: number): string {
  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 0,
  }).format(value);
}

export function InsightsPage() {
  const [overview, setOverview] = useState<InsightsOverview | null>(null);
  const [countries, setCountries] = useState<CountryInsight[]>([]);
  const [departments, setDepartments] = useState<DepartmentInsight[]>([]);
  const [payEquity, setPayEquity] = useState<PayEquityInsight[]>([]);
  const [jobTitles, setJobTitles] = useState<JobTitleInsight[]>([]);

  const [selectedCountry, setSelectedCountry] = useState('');
  const [loading, setLoading] = useState(true);
  const [jobTitleLoading, setJobTitleLoading] = useState(false);
  const [error, setError] = useState('');

  const loadMain = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [overviewData, countryData, departmentData, equityData] =
        await Promise.all([
          getInsightsOverview(),
          getInsightsByCountry(),
          getInsightsByDepartment(),
          getInsightsPayEquity(),
        ]);
      setOverview(overviewData);
      setCountries(countryData);
      setDepartments(departmentData);
      setPayEquity(equityData);
      setSelectedCountry((prev) => prev || countryData[0]?.country || '');
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
    if (!selectedCountry) {
      setJobTitles([]);
      return;
    }
    let cancelled = false;
    async function loadJobTitles() {
      setJobTitleLoading(true);
      try {
        const data = await getInsightsByJobTitle(selectedCountry);
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
  }, [selectedCountry]);

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

      {overview && (
        <section className="card">
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
            {Object.entries(overview.gender_distribution).map(([gender, pct]) => (
              <div key={gender} className="stat-card">
                <span className="stat-label">{gender}</span>
                <span className="stat-value">{pct}%</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="card table-wrap">
        <h3>By country</h3>
        {countries.length === 0 ? (
          <p className="muted table-message">No country data available.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Country</th>
                <th>Headcount</th>
                <th>Min</th>
                <th>Max</th>
                <th>Avg</th>
                <th>Median</th>
              </tr>
            </thead>
            <tbody>
              {countries.map((row) => (
                <tr key={row.country}>
                  <td>
                    <CountryLabel country={row.country} />
                  </td>
                  <td>{row.headcount}</td>
                  <td>{formatSalary(row.min_salary)}</td>
                  <td>{formatSalary(row.max_salary)}</td>
                  <td>{formatSalary(row.avg_salary)}</td>
                  <td>{formatSalary(row.median_salary)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card table-wrap">
        <h3>By department</h3>
        {departments.length === 0 ? (
          <p className="muted table-message">No department data available.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Department</th>
                <th>Headcount</th>
                <th>Avg salary</th>
                <th>Total payroll</th>
              </tr>
            </thead>
            <tbody>
              {departments.map((row) => (
                <tr key={row.department}>
                  <td>{row.department}</td>
                  <td>{row.headcount}</td>
                  <td>{formatSalary(row.avg_salary)}</td>
                  <td>{formatSalary(row.total_payroll)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <h3>By job title</h3>
        <form
          className="filters"
          onSubmit={(e) => {
            e.preventDefault();
          }}
        >
          <label>
            Country
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
            >
              {countries.map((c) => (
                <option key={c.country} value={c.country}>
                  {c.country}
                </option>
              ))}
            </select>
          </label>
        </form>
        {jobTitleLoading ? (
          <p className="muted">Loading job titles…</p>
        ) : jobTitles.length === 0 ? (
          <p className="muted table-message">No job title data for this country.</p>
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

      <section className="card table-wrap">
        <h3>Pay equity (Male vs Female avg by department)</h3>
        {payEquity.length === 0 ? (
          <p className="muted table-message">No pay equity data available.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Department</th>
                <th>Male avg</th>
                <th>Female avg</th>
                <th>Gap %</th>
              </tr>
            </thead>
            <tbody>
              {payEquity.map((row) => (
                <tr key={row.department}>
                  <td>{row.department}</td>
                  <td>{formatSalary(row.male_avg)}</td>
                  <td>{formatSalary(row.female_avg)}</td>
                  <td>
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
        )}
      </section>
    </div>
  );
}
