import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings

from api.constants import COUNTRIES, DEPARTMENTS, JOB_TITLES_BY_DEPARTMENT
from api.models import (
    Currency,
    Employee,
    EmployeeStatus,
    EmploymentType,
    Gender,
    SeniorityLevel,
)

DATA_DIR = Path(settings.BASE_DIR) / 'data'


def load_names(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def slugify_email_part(value: str) -> str:
    return ''.join(ch.lower() if ch.isalnum() else '.' for ch in value).strip('.')


def build_employee(
    index: int,
    first_names: list[str],
    last_names: list[str],
    rng: random.Random,
    run_tag: str = '',
) -> Employee:
    first_name = rng.choice(first_names)
    last_name = rng.choice(last_names)
    slug_base = slugify_email_part(f'{first_name}.{last_name}.{index}')
    slug = f'{slug_base}.{run_tag}' if run_tag else slug_base
    department = rng.choice(DEPARTMENTS)
    country, salary_min, salary_max = rng.choice(COUNTRIES)
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
        currency=Currency.USD,
        date_joining=date_joining,
        date_relieving=date_relieving,
        status=status,
    )
