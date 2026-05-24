import { useCallback, useEffect, useState } from 'react';
import {
  createEmployee,
  deleteEmployee,
  getCountries,
  getDepartments,
  listEmployees,
  updateEmployee,
} from '../api/employees';
import { CountryLabel } from '../components/CountryLabel';
import { EmployeeForm } from '../components/EmployeeForm';
import { MultiSelect } from '../components/MultiSelect';
import type { Employee } from '../types/api';
import { EMPLOYEE_STATUSES } from '../types/api';
import { formatSalary } from '../utils/currency';

const PAGE_SIZE = 25;

type PageItem = number | 'ellipsis';

function getPaginationRange(current: number, total: number): PageItem[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  const leftSibling = Math.max(current - 2, 1);
  const rightSibling = Math.min(current + 2, total);
  const showLeftEllipsis = leftSibling > 2;
  const showRightEllipsis = rightSibling < total - 1;

  if (!showLeftEllipsis && showRightEllipsis) {
    return [...Array.from({ length: 5 }, (_, i) => i + 1), 'ellipsis', total];
  }

  if (showLeftEllipsis && !showRightEllipsis) {
    return [
      1,
      'ellipsis',
      ...Array.from({ length: 5 }, (_, i) => total - 4 + i),
    ];
  }

  if (showLeftEllipsis && showRightEllipsis) {
    return [
      1,
      'ellipsis',
      ...Array.from({ length: rightSibling - leftSibling + 1 }, (_, i) => leftSibling + i),
      'ellipsis',
      total,
    ];
  }

  return Array.from({ length: total }, (_, i) => i + 1);
}

export function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [departmentOptions, setDepartmentOptions] = useState<string[]>([]);
  const [countryOptions, setCountryOptions] = useState<string[]>([]);

  const [draftDepartments, setDraftDepartments] = useState<string[]>([]);
  const [draftCountries, setDraftCountries] = useState<string[]>([]);
  const [draftStatus, setDraftStatus] = useState('');

  const [appliedDepartments, setAppliedDepartments] = useState<string[]>([]);
  const [appliedCountries, setAppliedCountries] = useState<string[]>([]);
  const [appliedStatus, setAppliedStatus] = useState('');

  const [panelOpen, setPanelOpen] = useState(false);
  const [panelMode, setPanelMode] = useState<'create' | 'edit'>('create');
  const [editing, setEditing] = useState<Employee | null>(null);

  useEffect(() => {
    async function loadOptions() {
      try {
        const [depts, countries] = await Promise.all([
          getDepartments(),
          getCountries(),
        ]);
        setDepartmentOptions(depts);
        setCountryOptions(countries);
      } catch {
        // Filters still work if options fail; user can retry via refresh
      }
    }
    loadOptions();
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await listEmployees({
        page,
        departments: appliedDepartments.length ? appliedDepartments : undefined,
        countries: appliedCountries.length ? appliedCountries : undefined,
        status: appliedStatus || undefined,
      });
      setEmployees(data.results);
      setCount(data.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load employees.');
    } finally {
      setLoading(false);
    }
  }, [page, appliedDepartments, appliedCountries, appliedStatus]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE));
  const pageNumbers = getPaginationRange(page, totalPages);

  function applyFilters(e: React.FormEvent) {
    e.preventDefault();
    setAppliedDepartments(draftDepartments);
    setAppliedCountries(draftCountries);
    setAppliedStatus(draftStatus);
    setPage(1);
  }

  function clearFilters() {
    setDraftDepartments([]);
    setDraftCountries([]);
    setDraftStatus('');
    setAppliedDepartments([]);
    setAppliedCountries([]);
    setAppliedStatus('');
    setPage(1);
  }

  function goToPage(target: number) {
    const clamped = Math.min(Math.max(1, target), totalPages);
    setPage(clamped);
  }

  function openCreate() {
    setPanelMode('create');
    setEditing(null);
    setPanelOpen(true);
  }

  function openEdit(employee: Employee) {
    setPanelMode('edit');
    setEditing(employee);
    setPanelOpen(true);
  }

  function closePanel() {
    setPanelOpen(false);
    setEditing(null);
  }

  async function handleDelete(employee: Employee) {
    if (!window.confirm(`Delete #${employee.id} (${employee.first_name} ${employee.last_name})?`)) {
      return;
    }
    try {
      await deleteEmployee(employee.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed.');
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Employees</h2>
          <p className="muted">Manage organization employees.</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          Add employee
        </button>
      </div>

      <form className="filters card" onSubmit={applyFilters}>
        <MultiSelect
          label="Department"
          options={departmentOptions}
          value={draftDepartments}
          onChange={setDraftDepartments}
          placeholder="All departments"
          searchPlaceholder="Search departments…"
        />
        <MultiSelect
          label="Country"
          options={countryOptions}
          value={draftCountries}
          onChange={setDraftCountries}
          placeholder="All countries"
          searchPlaceholder="Search countries…"
          renderOption={(c) => <CountryLabel country={c} />}
        />
        <label>
          Status
          <select
            value={draftStatus}
            onChange={(e) => setDraftStatus(e.target.value)}
          >
            <option value="">All</option>
            {EMPLOYEE_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <div className="filters-actions">
          <button type="submit" className="btn btn-primary">
            Apply filters
          </button>
          <button type="button" className="btn btn-ghost" onClick={clearFilters}>
            Clear
          </button>
        </div>
      </form>

      {error && <p className="error">{error}</p>}

      {panelOpen && (
        <div className="card panel">
          <h3>{panelMode === 'create' ? 'Add employee' : 'Edit employee'}</h3>
          <EmployeeForm
            mode={panelMode}
            initial={editing}
            onCancel={closePanel}
            onSubmit={async (data) => {
              if (panelMode === 'create') {
                await createEmployee(data);
              } else if (editing) {
                await updateEmployee(editing.id, data);
              }
              closePanel();
              await load();
            }}
          />
        </div>
      )}

      <div className="table-wrap card">
        {loading ? (
          <p className="muted table-message">Loading employees…</p>
        ) : employees.length === 0 ? (
          <p className="muted table-message">No employees found.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Department</th>
                <th>Job title</th>
                <th>Country</th>
                <th>Salary</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((emp) => (
                <tr key={emp.id}>
                  <td>{emp.id}</td>
                  <td>
                    {emp.first_name} {emp.last_name}
                  </td>
                  <td>{emp.department}</td>
                  <td>{emp.job_title}</td>
                  <td>
                    <CountryLabel country={emp.country} />
                  </td>
                  <td>{formatSalary(emp.salary, emp.currency)}</td>
                  <td>
                    <span className={`badge badge-${emp.status.toLowerCase().replace(/\s/g, '-')}`}>
                      {emp.status}
                    </span>
                  </td>
                  <td className="actions-cell">
                    <button
                      type="button"
                      className="btn btn-sm btn-ghost"
                      onClick={() => openEdit(emp)}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="btn btn-sm btn-danger"
                      onClick={() => handleDelete(emp)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="pagination">
        <div className="pagination-controls">
          <button
            type="button"
            className="btn btn-ghost"
            disabled={page <= 1}
            onClick={() => goToPage(page - 1)}
          >
            Previous
          </button>
          <div className="page-numbers">
            {pageNumbers.map((item, index) =>
              item === 'ellipsis' ? (
                <span key={`ellipsis-${index}`} className="page-ellipsis" aria-hidden>
                  …
                </span>
              ) : (
                <button
                  key={item}
                  type="button"
                  className={`btn btn-sm ${item === page ? 'btn-primary' : 'btn-ghost'}`}
                  aria-current={item === page ? 'page' : undefined}
                  onClick={() => goToPage(item)}
                >
                  {item}
                </button>
              ),
            )}
          </div>
          <button
            type="button"
            className="btn btn-ghost"
            disabled={page >= totalPages}
            onClick={() => goToPage(page + 1)}
          >
            Next
          </button>
        </div>
        <span className="muted">
          Page {page} of {totalPages} ({count} total)
        </span>
      </div>
    </div>
  );
}
