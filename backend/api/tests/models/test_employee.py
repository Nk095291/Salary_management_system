from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from api.models import (
    Currency,
    Employee,
    EmployeeStatus,
    EmploymentType,
    Gender,
    HRUser,
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
    - Duplicate personal_email raises integrity error on save.
    - date_relieving before date_joining fails the database check constraint.
    - __str__ includes primary key and full name.
    - clean() rejects unknown countries.
    - clean() rejects relieving date before joining date.
    """

    TEST_CASES = [
        'Creating an employee assigns a database primary key.',
        'Duplicate personal_email raises integrity error on save.',
        'date_relieving before date_joining fails the database check constraint.',
        '__str__ includes primary key and full name.',
        'clean() rejects unknown countries.',
        'clean() rejects relieving date before joining date.',
    ]

    def test_Employee__first_record__assigns_primary_key(self):
        """Creating an employee assigns a database primary key."""
        # GIVEN
        data = _employee_kwargs()

        # WHEN
        employee = Employee.objects.create(**data)

        # THEN
        self.assertIsNotNone(employee.pk)

    def test_Employee__duplicate_personal_email__raises_integrity_error(self):
        """Duplicate personal_email raises integrity error on save."""
        # GIVEN
        Employee.objects.create(**_employee_kwargs())
        duplicate = Employee(**_employee_kwargs(company_email='other@company.com'))

        # WHEN / THEN
        with self.assertRaises(IntegrityError):
            duplicate.save()

    def test_Employee__relieving_before_joining__fails_check_constraint(self):
        """date_relieving before date_joining fails the database check constraint."""
        # GIVEN
        employee = Employee(
            **_employee_kwargs(
                date_joining=date(2024, 6, 1),
                date_relieving=date(2024, 1, 1),
            )
        )

        # WHEN / THEN
        with self.assertRaises(IntegrityError):
            employee.save()

    def test_Employee__str__includes_pk_and_full_name(self):
        """__str__ includes primary key and full name."""
        # GIVEN
        employee = Employee.objects.create(**_employee_kwargs())

        # WHEN / THEN
        self.assertEqual(str(employee), f'{employee.pk} - Jane Doe')

    def test_Employee__invalid_country__clean_raises_validation_error(self):
        """clean() rejects unknown countries."""
        # GIVEN
        employee = Employee(**_employee_kwargs(country='Atlantis'))

        # WHEN / THEN
        with self.assertRaises(ValidationError) as context:
            employee.full_clean()
        self.assertIn('country', context.exception.message_dict)

    def test_Employee__relieving_before_joining__clean_raises_validation_error(self):
        """clean() rejects relieving date before joining date."""
        # GIVEN
        employee = Employee(
            **_employee_kwargs(
                date_joining=date(2024, 6, 1),
                date_relieving=date(2024, 1, 1),
            )
        )

        # WHEN / THEN
        with self.assertRaises(ValidationError) as context:
            employee.full_clean()
        self.assertIn('date_relieving', context.exception.message_dict)


class HRUserModelTests(TestCase):
    """
    Tests for HRUser model and manager.

    Covered cases:
    - __str__ returns the user email.
    - create_user without email raises ValueError.
    - create_superuser sets staff, superuser, and active flags.
    """

    TEST_CASES = [
        '__str__ returns the user email.',
        'create_user without email raises ValueError.',
        'create_superuser sets staff, superuser, and active flags.',
    ]

    def test_HRUser__str__returns_email(self):
        """__str__ returns the user email."""
        # GIVEN
        user = HRUser.objects.create_user(
            email='hr@company.com',
            password='secret123',
        )

        # WHEN / THEN
        self.assertEqual(str(user), 'hr@company.com')

    def test_HRUserManager__create_user_without_email__raises_value_error(self):
        """create_user without email raises ValueError."""
        # WHEN / THEN
        with self.assertRaises(ValueError):
            HRUser.objects.create_user(email='')

    def test_HRUserManager__create_superuser__sets_staff_flags(self):
        """create_superuser sets staff, superuser, and active flags."""
        # WHEN
        user = HRUser.objects.create_superuser(
            email='admin@company.com',
            password='secret123',
        )

        # THEN
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
