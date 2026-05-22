import { useCallback, useEffect, useState } from 'react';
import {
  createEmployee,
  deleteEmployee,
  listEmployees,
  updateEmployee,
} from '../api/employees';
import { EmployeeForm } from '../components/EmployeeForm';
import type { Employee } from '../types/api';
import { EMPLOYEE_STATUSES } from '../types/api';

export function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [filterDepartment, setFilterDepartment] = useState('');
  const [filterCountry, setFilterCountry] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const [panelOpen, setPanelOpen] = useState(false);
  const [panelMode, setPanelMode] = useState<'create' | 'edit'>('create');
  const [editing, setEditing] = useState<Employee | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await listEmployees({
        page,
        department: filterDepartment || undefined,
        country: filterCountry || undefined,
        status: filterStatus || undefined,
      });
      setEmployees(data.results);
      setCount(data.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load employees.');
    } finally {
      setLoading(false);
    }
  }, [page, filterDepartment, filterCountry, filterStatus]);

  useEffect(() => {
    load();
  }, [load]);

  async function applyFilters(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    setLoading(true);
    setError('');
    try {
      const data = await listEmployees({
        page: 1,
        department: filterDepartment || undefined,
        country: filterCountry || undefined,
        status: filterStatus || undefined,
      });
      setEmployees(data.results);
      setCount(data.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load employees.');
    } finally {
      setLoading(false);
    }
  }

  async function clearFilters() {
    setFilterDepartment('');
    setFilterCountry('');
    setFilterStatus('');
    setPage(1);
    setLoading(true);
    setError('');
    try {
      const data = await listEmployees({ page: 1 });
      setEmployees(data.results);
      setCount(data.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load employees.');
    } finally {
      setLoading(false);
    }
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
    if (!window.confirm(`Delete ${employee.employee_id} (${employee.first_name} ${employee.last_name})?`)) {
      return;
    }
    try {
      await deleteEmployee(employee.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed.');
    }
  }

  const pageSize = 25;
  const totalPages = Math.max(1, Math.ceil(count / pageSize));

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
        <label>
          Department
          <input
            value={filterDepartment}
            onChange={(e) => setFilterDepartment(e.target.value)}
            placeholder="e.g. Engineering"
          />
        </label>
        <label>
          Country
          <input
            value={filterCountry}
            onChange={(e) => setFilterCountry(e.target.value)}
            placeholder="e.g. United States"
          />
        </label>
        <label>
          Status
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
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
                  <td>{emp.employee_id}</td>
                  <td>
                    {emp.first_name} {emp.last_name}
                  </td>
                  <td>{emp.department}</td>
                  <td>{emp.job_title}</td>
                  <td>{emp.country}</td>
                  <td>
                    {emp.currency} {emp.salary}
                  </td>
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
        <button
          type="button"
          className="btn btn-ghost"
          disabled={page <= 1}
          onClick={() => setPage((p) => p - 1)}
        >
          Previous
        </button>
        <span className="muted">
          Page {page} of {totalPages} ({count} total)
        </span>
        <button
          type="button"
          className="btn btn-ghost"
          disabled={page >= totalPages}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
