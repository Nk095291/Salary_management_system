import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings

from api.models import (
    Currency,
    Employee,
    EmployeeStatus,
    EmploymentType,
    Gender,
    SeniorityLevel,
)

DATA_DIR = Path(settings.BASE_DIR) / 'data'

DEPARTMENTS = [
    'Engineering',
    'Sales',
    'Human Resources',
    'Finance',
    'Marketing',
    'Operations',
    'Legal',
    'Support',
]

JOB_TITLES_BY_DEPARTMENT = {
    'Engineering': [
        'Software Engineer',
        'Senior Software Engineer',
        'QA Engineer',
        'DevOps Engineer',
        'Engineering Manager',
    ],
    'Sales': [
        'Account Executive',
        'Sales Representative',
        'Sales Manager',
        'Business Development Manager',
    ],
    'Human Resources': ['HR Manager', 'HR Specialist', 'Recruiter'],
    'Finance': ['Financial Analyst', 'Accountant', 'Finance Manager'],
    'Marketing': ['Marketing Specialist', 'Content Strategist', 'Marketing Manager'],
    'Operations': ['Operations Analyst', 'Operations Manager', 'Project Coordinator'],
    'Legal': ['Legal Counsel', 'Compliance Officer'],
    'Support': ['Support Specialist', 'Customer Success Manager'],
}

COUNTRIES = [
    ('United States', Currency.USD, 40_000, 180_000),
    ('India', Currency.INR, 400_000, 2_500_000),
    ('United Kingdom', Currency.GBP, 28_000, 95_000),
    ('Germany', Currency.EUR, 35_000, 110_000),
    ('Canada', Currency.CAD, 45_000, 120_000),
    ('Australia', Currency.AUD, 50_000, 130_000),
]


def load_names(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def slugify_email_part(value: str) -> str:
    return ''.join(ch.lower() if ch.isalnum() else '.' for ch in value).strip('.')


def build_employee(
    index: int,
    first_names: list[str],
    last_names: list[str],
    rng: random.Random,
) -> Employee:
    first_name = rng.choice(first_names)
    last_name = rng.choice(last_names)
    slug = slugify_email_part(f'{first_name}.{last_name}.{index}')
    department = rng.choice(DEPARTMENTS)
    country, currency, salary_min, salary_max = rng.choice(COUNTRIES)
    status = rng.choices(
        list(EmployeeStatus.values),
        weights=[90, 10],
        k=1,
    )[0]
    date_joining = date.today() - timedelta(days=rng.randint(30, 3650))
    date_relieving = None
    if status == EmployeeStatus.TERMINATED:
        date_relieving = date_joining + timedelta(days=rng.randint(180, 2000))

    date_of_birth = None
    if rng.random() < 0.7:
        age_days = rng.randint(22 * 365, 60 * 365)
        date_of_birth = date_joining - timedelta(days=age_days)

    salary = Decimal(rng.randint(salary_min, salary_max))

    return Employee(
        first_name=first_name,
        last_name=last_name,
        personal_email=f'{slug}@personal.example.com',
        company_email=f'{slug}@company.com',
        gender=rng.choice(list(Gender.values)),
        date_of_birth=date_of_birth,
        department=department,
        job_title=rng.choice(JOB_TITLES_BY_DEPARTMENT[department]),
        seniority_level=rng.choice(list(SeniorityLevel.values)),
        employment_type=rng.choices(
            list(EmploymentType.values),
            weights=[80, 15, 4, 1],
            k=1,
        )[0],
        country=country,
        salary=salary,
        currency=currency,
        date_joining=date_joining,
        date_relieving=date_relieving,
        status=status,
    )
