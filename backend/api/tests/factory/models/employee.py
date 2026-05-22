from datetime import date
from decimal import Decimal

import factory
from factory import Faker

from api.models import (
    Currency,
    Employee,
    EmployeeStatus,
    EmploymentType,
    Gender,
    SeniorityLevel,
)


class EmployeeFactory(factory.django.DjangoModelFactory):
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    personal_email = factory.Sequence(lambda n: f'employee{n}.personal@example.com')
    company_email = factory.Sequence(lambda n: f'employee{n}@company.com')
    gender = Gender.FEMALE
    department = 'Human Resources'
    job_title = 'HR Manager'
    seniority_level = SeniorityLevel.SENIOR
    employment_type = EmploymentType.FULL_TIME
    country = 'United States'
    salary = factory.LazyFunction(lambda: Decimal('90000.00'))
    currency = Currency.USD
    date_joining = factory.LazyFunction(lambda: date(2019, 3, 1))
    status = EmployeeStatus.ACTIVE

    class Meta:
        model = Employee
