import math
import random
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.test import TestCase

from api.models import Currency, Employee, EmployeeStatus, EmploymentType, Gender
from api.utils.management.commands.seed_employees import (
    COUNTRIES,
    DEPARTMENTS,
    JOB_TITLES_BY_DEPARTMENT,
    build_employee,
    load_names,
    slugify_email_part,
)


class SeedEmployeesUtilsTests(TestCase):
    """
    Tests for seed_employees utility helpers.

    Covered cases:
    - load_names strips lines and skips blank rows.
    - load_names on empty file returns an empty list.
    - slugify_email_part lowercases and replaces non-alphanumeric characters.
    - build_employee returns an unsaved Employee with names from input lists.
    - build_employee sets company and personal emails from slugified name parts.
    - build_employee picks department and job title from configured mappings.
    - build_employee sets salary within the selected country range.
    - build_employee sets date_relieving when status is terminated.
    """

    def test_load_names__file_with_blank_lines__returns_stripped_non_empty(self):
        """load_names strips lines and skips blank rows."""
        # GIVEN
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as handle:
            handle.write('  Alice  \n\nBob\n   \n')
            path = Path(handle.name)

        # WHEN
        names = load_names(path)

        # THEN
        self.assertEqual(names, ['Alice', 'Bob'])
        path.unlink(missing_ok=True)

    def test_load_names__empty_file__returns_empty_list(self):
        """load_names on empty file returns an empty list."""
        # GIVEN
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as handle:
            path = Path(handle.name)

        # WHEN
        names = load_names(path)

        # THEN
        self.assertEqual(names, [])
        path.unlink(missing_ok=True)

    def test_slugify_email_part__special_characters__lowercases_and_replaces(self):
        """slugify_email_part lowercases and replaces non-alphanumeric characters."""
        # GIVEN / WHEN
        slug = slugify_email_part('Jane O\'Connor-Smith')

        # THEN
        self.assertEqual(slug, 'jane.o.connorsmith')

    def test_build_employee__valid_inputs__returns_unsaved_employee(self):
        """build_employee returns an unsaved Employee with names from input lists."""
        # GIVEN
        first_names = ['Ada']
        last_names = ['Lovelace']
        rng = random.Random(1)

        # WHEN
        employee = build_employee(1, first_names, last_names, rng)

        # THEN
        self.assertIsInstance(employee, Employee)
        self.assertIsNone(employee.pk)
        self.assertIn(employee.first_name, first_names)
        self.assertIn(employee.last_name, last_names)

    def test_build_employee__index_in_slug__sets_unique_emails(self):
        """build_employee sets company and personal emails from slugified name parts."""
        # GIVEN
        rng = random.Random(42)

        # WHEN
        employee = build_employee(7, ['Ada'], ['Lovelace'], rng)

        # THEN
        self.assertTrue(employee.company_email.endswith('@company.com'))
        self.assertTrue(employee.personal_email.endswith('@personal.example.com'))
        self.assertIn('.7@', employee.company_email)

    def test_build_employee__department__uses_configured_job_titles(self):
        """build_employee picks department and job title from configured mappings."""
        # GIVEN
        rng = random.Random(99)

        # WHEN
        employee = build_employee(1, ['Test'], ['User'], rng)

        # THEN
        self.assertIn(employee.department, DEPARTMENTS)
        self.assertIn(employee.job_title, JOB_TITLES_BY_DEPARTMENT[employee.department])

    def test_build_employee__country__salary_within_configured_range(self):
        """build_employee sets salary within the selected country range."""
        # GIVEN
        rng = random.Random(5)
        country_ranges = {country: (minimum, maximum) for country, _, minimum, maximum in COUNTRIES}

        # WHEN
        employee = build_employee(1, ['Test'], ['User'], rng)

        # THEN
        minimum, maximum = country_ranges[employee.country]
        self.assertGreaterEqual(employee.salary, Decimal(minimum))
        self.assertLessEqual(employee.salary, Decimal(maximum))

    def test_build_employee__terminated_status__sets_date_relieving(self):
        """build_employee sets date_relieving when status is terminated."""
        # GIVEN
        rng = random.Random(0)
        for _ in range(200):
            employee = build_employee(1, ['Test'], ['User'], rng)
            if employee.status == EmployeeStatus.TERMINATED:
                break
        else:
            self.fail('Expected at least one terminated employee within 200 attempts.')

        # THEN
        self.assertIsNotNone(employee.date_relieving)
        self.assertGreaterEqual(employee.date_relieving, employee.date_joining)


class SeedEmployeesUtilsEdgeTests(TestCase):
    """
    Edge-case tests for seed_employees utility helpers.

    These document desired behavior for unusual inputs; some may fail until
    utilities add explicit validation.
    """

    def test_slugify_email_part__empty_string__returns_empty_slug(self):
        """Empty input slugifies to an empty string."""
        # GIVEN / WHEN
        slug = slugify_email_part('')

        # THEN
        self.assertEqual(slug, '')

    def test_build_employee__empty_first_names__raises_index_error(self):
        """build_employee with empty first_names should fail fast."""
        # GIVEN
        rng = random.Random(1)

        # WHEN / THEN
        with self.assertRaises(IndexError):
            build_employee(1, [], ['User'], rng)

    def test_build_employee__same_seed_and_index__reproducible_fields(self):
        """Same RNG seed and index produce identical employee field values."""
        # GIVEN
        first_names = ['Ada', 'Grace']
        last_names = ['Lovelace', 'Hopper']

        # WHEN
        first = build_employee(3, first_names, last_names, random.Random(77))
        second = build_employee(3, first_names, last_names, random.Random(77))

        # THEN
        self.assertEqual(first.first_name, second.first_name)
        self.assertEqual(first.company_email, second.company_email)
        self.assertEqual(first.salary, second.salary)

    def test_build_employee__date_of_birth_when_set__before_date_joining(self):
        """When date_of_birth is set it should not be after date_joining."""
        # GIVEN
        rng = random.Random(3)
        employees_with_dob = []
        for _ in range(100):
            employee = build_employee(1, ['Test'], ['User'], rng)
            if employee.date_of_birth is not None:
                employees_with_dob.append(employee)

        # THEN
        self.assertTrue(employees_with_dob, 'Expected at least one employee with date_of_birth.')
        for employee in employees_with_dob:
            self.assertLessEqual(employee.date_of_birth, employee.date_joining)

    def test_build_employee__gender_and_employment_type__valid_choices(self):
        """Generated choice fields use model TextChoices values."""
        # GIVEN
        rng = random.Random(11)

        # WHEN
        employee = build_employee(1, ['Test'], ['User'], rng)

        # THEN
        self.assertIn(employee.gender, Gender.values)
        self.assertIn(employee.employment_type, EmploymentType.values)
        self.assertIn(employee.currency, Currency.values)

    def test_build_employee__date_joining__not_in_future(self):
        """date_joining should never be in the future."""
        # GIVEN
        rng = random.Random(13)
        today = date.today()

        # WHEN
        employee = build_employee(1, ['Test'], ['User'], rng)

        # THEN
        self.assertLessEqual(employee.date_joining, today)
