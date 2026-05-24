import { useEffect, useRef, useState } from 'react';
import { getCountries, getDepartments } from '../api/employees';
import type { DepartmentOption, Employee, EmployeePayload } from '../types/api';
import {
  EMPLOYEE_STATUSES,
  EMPLOYMENT_TYPES,
  GENDERS,
  SENIORITY_LEVELS,
} from '../types/api';
import { getCountryFlagUrl } from '../utils/country';

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
  salary: '',
  currency: 'USD', // read-only on backend; always USD
  date_joining: new Date().toISOString().slice(0, 10),
  date_relieving: null,
  status: 'Active',
});

function formatSalaryInput(value: string): string {
  const cleaned = value.replace(/,/g, '');
  if (!cleaned) return '';
  const [intPart, decPart] = cleaned.split('.');
  const formattedInt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return decPart !== undefined ? `${formattedInt}.${decPart}` : formattedInt;
}

function parseSalaryInput(value: string): string {
  const cleaned = value.replace(/,/g, '').replace(/[^\d.]/g, '');
  if (!cleaned) return '';

  const dotIndex = cleaned.indexOf('.');
  const hasDecimal = dotIndex !== -1;
  let intPart = hasDecimal ? cleaned.slice(0, dotIndex) : cleaned;
  const decPart = hasDecimal ? cleaned.slice(dotIndex + 1) : undefined;

  if (intPart.length > 0) {
    intPart = intPart.replace(/^0+(?=\d)/, '');
  }

  if (!intPart && !hasDecimal) return '';

  if (hasDecimal) {
    if (!intPart) intPart = '0';
    return decPart === undefined || decPart === ''
      ? `${intPart}.`
      : `${intPart}.${decPart}`;
  }

  return intPart;
}

function countDigitsBefore(value: string, cursor: number): number {
  let count = 0;
  for (let i = 0; i < Math.min(cursor, value.length); i++) {
    if (/\d/.test(value[i])) count++;
  }
  return count;
}

function cursorAfterDigits(formatted: string, digitCount: number): number {
  if (digitCount <= 0) return 0;
  let seen = 0;
  for (let i = 0; i < formatted.length; i++) {
    if (/\d/.test(formatted[i])) {
      seen++;
      if (seen >= digitCount) return i + 1;
    }
  }
  return formatted.length;
}

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
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [countries, setCountries] = useState<string[]>([]);
  const salaryInputRef = useRef<HTMLInputElement>(null);
  const salarySelectionRef = useRef<number | null>(null);

  useEffect(() => {
    async function loadOptions() {
      try {
        const [depts, countryList] = await Promise.all([
          getDepartments(),
          getCountries(),
        ]);
        setDepartments(depts);
        setCountries(countryList);
      } catch {
        // Form still works if options fail to load
      }
    }
    loadOptions();
  }, []);

  useEffect(() => {
    const input = salaryInputRef.current;
    const pos = salarySelectionRef.current;
    if (input && pos !== null) {
      input.setSelectionRange(pos, pos);
      salarySelectionRef.current = null;
    }
  }, [form.salary]);

  const jobTitles =
    departments.find((d) => d.name === form.department)?.job_titles ?? [];
  const jobTitleOptions =
    form.job_title && !jobTitles.includes(form.job_title)
      ? [form.job_title, ...jobTitles]
      : jobTitles;

  function updateDepartment(department: string) {
    const titles =
      departments.find((d) => d.name === department)?.job_titles ?? [];
    setForm((prev) => ({
      ...prev,
      department,
      job_title: titles.includes(prev.job_title) ? prev.job_title : '',
    }));
  }

  function update<K extends keyof EmployeePayload>(
    key: K,
    value: EmployeePayload[K],
  ) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function handleSalaryChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { value, selectionStart } = e.target;
    const cursor = selectionStart ?? value.length;
    const digitsBefore = countDigitsBefore(value, cursor);
    const parsed = parseSalaryInput(value);

    salarySelectionRef.current = cursorAfterDigits(
      formatSalaryInput(parsed),
      digitsBefore,
    );
    update('salary', parsed);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const payload: EmployeePayload = {
        ...form,
        salary: parseSalaryInput(form.salary),
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
          ID
          <input type="text" value={String(initial.id)} readOnly disabled />
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
        <select
          value={form.department}
          onChange={(e) => updateDepartment(e.target.value)}
          required
        >
          <option value="">Select a department…</option>
          {departments.map((d) => (
            <option key={d.name} value={d.name}>
              {d.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Job title
        <select
          value={form.job_title}
          onChange={(e) => update('job_title', e.target.value)}
          required
          disabled={!form.department}
        >
          <option value="">
            {form.department ? 'Select a job title…' : 'Choose a department first'}
          </option>
          {jobTitleOptions.map((title) => (
            <option key={title} value={title}>
              {title}
            </option>
          ))}
        </select>
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
        <select
          value={form.country}
          onChange={(e) => update('country', e.target.value)}
          required
        >
          <option value="">Select a country…</option>
          {countries.map((c) => {
            const flagUrl = getCountryFlagUrl(c);
            return (
              <option key={c} value={c}>
                {flagUrl ? '' : ''}{c}
              </option>
            );
          })}
        </select>
      </label>
      <label>
        Salary (USD)
        <input
          ref={salaryInputRef}
          type="text"
          inputMode="decimal"
          value={formatSalaryInput(form.salary)}
          onChange={handleSalaryChange}
          required
        />
      </label>
      <label>
        Date of joining
        <input
          type="date"
          value={form.date_joining}
          onChange={(e) => update('date_joining', e.target.value)}
          required
        />
      </label>
      <label>
        Date of relieving
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
