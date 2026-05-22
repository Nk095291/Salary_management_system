import { useState } from 'react';
import type { Employee, EmployeePayload } from '../types/api';
import {
  CURRENCIES,
  EMPLOYEE_STATUSES,
  EMPLOYMENT_TYPES,
  GENDERS,
  SENIORITY_LEVELS,
} from '../types/api';

export type EmployeeFormMode = 'create' | 'edit';

interface EmployeeFormProps {
  mode: EmployeeFormMode;
  initial?: Employee | null;
  onSubmit: (data: EmployeePayload) => Promise<void>;
  onCancel: () => void;
}

const emptyForm = (): EmployeePayload => ({
  first_name: '',
  last_name: '',
  personal_email: '',
  company_email: '',
  gender: 'Male',
  date_of_birth: null,
  department: '',
  job_title: '',
  seniority_level: 'Mid',
  employment_type: 'Full-time',
  country: '',
  salary: '0',
  currency: 'USD',
  date_joining: new Date().toISOString().slice(0, 10),
  date_relieving: null,
  status: 'Active',
});

function toFormState(employee: Employee): EmployeePayload {
  return {
    first_name: employee.first_name,
    last_name: employee.last_name,
    personal_email: employee.personal_email,
    company_email: employee.company_email,
    gender: employee.gender,
    date_of_birth: employee.date_of_birth,
    department: employee.department,
    job_title: employee.job_title,
    seniority_level: employee.seniority_level,
    employment_type: employee.employment_type,
    country: employee.country,
    salary: employee.salary,
    currency: employee.currency,
    date_joining: employee.date_joining,
    date_relieving: employee.date_relieving,
    status: employee.status,
  };
}

export function EmployeeForm({
  mode,
  initial,
  onSubmit,
  onCancel,
}: EmployeeFormProps) {
  const [form, setForm] = useState<EmployeePayload>(
    initial ? toFormState(initial) : emptyForm(),
  );
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  function update<K extends keyof EmployeePayload>(
    key: K,
    value: EmployeePayload[K],
  ) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const payload: EmployeePayload = {
        ...form,
        date_of_birth: form.date_of_birth || null,
        date_relieving: form.date_relieving || null,
      };
      await onSubmit(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="form form-grid" onSubmit={handleSubmit}>
      {mode === 'edit' && initial && (
        <label className="full-width">
          Employee ID
          <input type="text" value={initial.employee_id} readOnly disabled />
        </label>
      )}
      <label>
        First name
        <input
          value={form.first_name}
          onChange={(e) => update('first_name', e.target.value)}
          required
        />
      </label>
      <label>
        Last name
        <input
          value={form.last_name}
          onChange={(e) => update('last_name', e.target.value)}
          required
        />
      </label>
      <label>
        Personal email
        <input
          type="email"
          value={form.personal_email}
          onChange={(e) => update('personal_email', e.target.value)}
          required
        />
      </label>
      <label>
        Company email
        <input
          type="email"
          value={form.company_email}
          onChange={(e) => update('company_email', e.target.value)}
          required
        />
      </label>
      <label>
        Gender
        <select
          value={form.gender}
          onChange={(e) => update('gender', e.target.value as EmployeePayload['gender'])}
        >
          {GENDERS.map((g) => (
            <option key={g} value={g}>
              {g}
            </option>
          ))}
        </select>
      </label>
      <label>
        Date of birth
        <input
          type="date"
          value={form.date_of_birth ?? ''}
          onChange={(e) =>
            update('date_of_birth', e.target.value || null)
          }
        />
      </label>
      <label>
        Department
        <input
          value={form.department}
          onChange={(e) => update('department', e.target.value)}
          required
        />
      </label>
      <label>
        Job title
        <input
          value={form.job_title}
          onChange={(e) => update('job_title', e.target.value)}
          required
        />
      </label>
      <label>
        Seniority
        <select
          value={form.seniority_level}
          onChange={(e) =>
            update('seniority_level', e.target.value as EmployeePayload['seniority_level'])
          }
        >
          {SENIORITY_LEVELS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>
      <label>
        Employment type
        <select
          value={form.employment_type}
          onChange={(e) =>
            update('employment_type', e.target.value as EmployeePayload['employment_type'])
          }
        >
          {EMPLOYMENT_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>
      <label>
        Country
        <input
          value={form.country}
          onChange={(e) => update('country', e.target.value)}
          required
        />
      </label>
      <label>
        Salary
        <input
          type="number"
          min="0"
          step="0.01"
          value={form.salary}
          onChange={(e) => update('salary', e.target.value)}
          required
        />
      </label>
      <label>
        Currency
        <select
          value={form.currency}
          onChange={(e) => update('currency', e.target.value as EmployeePayload['currency'])}
        >
          {CURRENCIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </label>
      <label>
        Date joining
        <input
          type="date"
          value={form.date_joining}
          onChange={(e) => update('date_joining', e.target.value)}
          required
        />
      </label>
      <label>
        Date relieving
        <input
          type="date"
          value={form.date_relieving ?? ''}
          onChange={(e) =>
            update('date_relieving', e.target.value || null)
          }
        />
      </label>
      <label>
        Status
        <select
          value={form.status}
          onChange={(e) => update('status', e.target.value as EmployeePayload['status'])}
        >
          {EMPLOYEE_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>
      {error && <p className="error full-width">{error}</p>}
      <div className="form-actions full-width">
        <button type="button" className="btn btn-ghost" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Saving…' : mode === 'create' ? 'Create' : 'Save changes'}
        </button>
      </div>
    </form>
  );
}
