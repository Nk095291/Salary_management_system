from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from api.models import (
    Currency,
    Employee,
    EmployeeStatus,
    EmploymentType,
    Gender,
    SeniorityLevel,
)


def _employee_kwargs(**overrides):
    data = {
        'first_name': 'Jane',
        'last_name': 'Doe',
        'personal_email': 'jane.personal@example.com',
        'company_email': 'jane@company.com',
        'gender': Gender.FEMALE,
        'department': 'Engineering',
        'job_title': 'Software Engineer',
        'seniority_level': SeniorityLevel.MID,
        'employment_type': EmploymentType.FULL_TIME,
        'country': 'United States',
        'salary': Decimal('75000.00'),
        'currency': Currency.USD,
        'date_joining': date(2020, 1, 15),
        'status': EmployeeStatus.ACTIVE,
    }
    data.update(overrides)
    return data


class EmployeeModelTests(TestCase):
    """
    Tests for Employee model save/validation.

    Covered cases:
    - Creating an employee assigns a database primary key.
    - Duplicate personal_email raises validation error.
    - date_relieving before date_joining fails validation.
    """

    TEST_CASES = [
        'Creating an employee assigns a database primary key.',
        'Duplicate personal_email raises validation error.',
        'date_relieving before date_joining fails validation.',
    ]

    def test_Employee__first_record__assigns_primary_key(self):
        """Creating an employee assigns a database primary key."""
        # GIVEN
        data = _employee_kwargs()

        # WHEN
        employee = Employee.objects.create(**data)

        # THEN
        self.assertIsNotNone(employee.pk)

    def test_Employee__duplicate_personal_email__raises_validation_error(self):
        """Duplicate personal_email raises validation error."""
        # GIVEN
        Employee.objects.create(**_employee_kwargs())
        duplicate = Employee(**_employee_kwargs(company_email='other@company.com'))

        # WHEN / THEN
        with self.assertRaises(ValidationError):
            duplicate.save()

    def test_Employee__relieving_before_joining__fails_validation(self):
        """date_relieving before date_joining fails validation."""
        # GIVEN
        employee = Employee(
            **_employee_kwargs(
                date_joining=date(2024, 6, 1),
                date_relieving=date(2024, 1, 1),
            )
        )

        # WHEN / THEN
        with self.assertRaises(ValidationError):
            employee.save()
