import random
import secrets
from uuid import uuid4

from faker import Faker

from api.constants import COUNTRY_NAMES
from api.models import EmploymentType, Gender, SeniorityLevel, EmployeeStatus

fake = Faker()


def random_choice_value(choices):
    """Pick a random valid value from a Django TextChoices class."""
    return random.choice(choices.values)


def random_country() -> str:
    """Pick a random country from the allowed list."""
    return random.choice(COUNTRY_NAMES)


def unique_label(prefix):
    """Generate a unique string for unbounded CharField values (e.g. department)."""
    return f'{prefix}-{uuid4().hex[:12]}'


def distinct_choice_values(choices, count=2):
    """Pick `count` distinct valid values from a TextChoices class."""
    return random.sample(list(choices.values), count)


def distinct_countries(count: int) -> list[str]:
    """Pick `count` distinct countries from the allowed list."""
    return random.sample(COUNTRY_NAMES, count)


def invalid_choice_value(valid_values):
    """Return a value guaranteed not to be in `valid_values`."""
    valid = set(valid_values)
    while True:
        candidate = secrets.token_hex(8)
        if candidate not in valid:
            return candidate


def valid_employee_payload(**overrides):
    """Build a valid create payload using random valid field values."""
    suffix = uuid4().hex[:8]
    data = {
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'personal_email': f'personal.{suffix}@example.com',
        'company_email': f'company.{suffix}@example.com',
        'gender': random_choice_value(Gender),
        'department': 'Engineering',
        'job_title': fake.job(),
        'seniority_level': random_choice_value(SeniorityLevel),
        'employment_type': random_choice_value(EmploymentType),
        'country': random_country(),
        'salary': f'{random.randint(30_000, 200_000)}.00',
        'date_joining': fake.date_between(start_date='-10y', end_date='today').isoformat(),
        'status': random_choice_value(EmployeeStatus),
    }
    data.update(overrides)
    return data
