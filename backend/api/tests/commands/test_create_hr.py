from io import StringIO
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from api.models import (
    Currency,
    Employee,
    EmployeeStatus,
    EmploymentType,
    Gender,
    HRUser,
    SeniorityLevel,
)


def expected_create_hr_new_employee_query_count(*, personal_email_exists_checks: int = 1) -> int:
    """
    Expected DB queries when create_hr creates a new employee on SQLite.

    - 1 query to check for an existing HR user email
    - personal_email_exists_checks while-loop collision probes
    - 1 query to insert the employee
    - 1 query to insert the HR user
    """
    return 1 + personal_email_exists_checks + 1 + 1


def expected_create_hr_link_existing_query_count(*, create_user: bool = True) -> int:
    """
    Expected DB queries when create_hr links an existing employee on SQLite.

    - 1 query to check for an existing HR user email
    - 1 query to load the employee by primary key
    - 1 query to check whether the employee is already linked
    - optionally 1 query to insert the HR user
    """
    return 3 + (1 if create_user else 0)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEBUG=True,
)
class CreateHrCommandTests(TestCase):
    """
    Tests for create_hr management command.

    Covered cases:
    - New email creates HR user, employee link, and sends email.
    - Duplicate email raises command error.
    - Dev mode prints temporary password to stdout.
    - Missing email with --no-input or empty prompt raises errors.
    - Interactive prompt supplies email when omitted.
    - Linking to existing employee by --employee-pk.
    - Invalid or already-linked employee_pk raises errors.
    - Personal email suffix collision when generating employee.
    - Query counts match duplicate checks, employee creation, and linking paths.
    """

    def test_create_hr__new_email__creates_user_and_sends_mail(self):
        """New email creates HR user, employee link, and sends email."""
        # GIVEN
        email = 'newhr@company.com'

        # WHEN
        call_command('create_hr', email=email, no_input=True)

        # THEN
        user = HRUser.objects.get(email=email)
        self.assertIsNotNone(user.employee)
        self.assertEqual(user.employee.company_email, email)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(email, mail.outbox[0].to)
        self.assertIn('Temporary password', mail.outbox[0].body)

    def test_create_hr__duplicate_email__raises_command_error(self):
        """Duplicate email raises command error."""
        # GIVEN
        call_command('create_hr', email='dup@company.com', no_input=True)

        # WHEN / THEN
        with self.assertRaises(CommandError):
            call_command('create_hr', email='dup@company.com', no_input=True)

    def test_create_hr__debug_mode__prints_password_to_stdout(self):
        """Dev mode prints temporary password to stdout."""
        # GIVEN
        email = 'devhr@company.com'
        out = StringIO()

        # WHEN
        call_command('create_hr', email=email, no_input=True, stdout=out)

        # THEN
        output = out.getvalue()
        self.assertIn('[DEV] Temporary password', output)
        self.assertIn(email, output)

    def test_create_hr__no_email_with_no_input__raises_error(self):
        """Fails if no email is provided and --no-input is flagged."""
        with self.assertRaisesMessage(
            CommandError, '--email is required when using --no-input.'
        ):
            call_command('create_hr', no_input=True)

    @patch('builtins.input', return_value='prompted@company.com')
    def test_create_hr__no_email_prompts_user(self, mock_input):
        """Prompts for email if not provided and creates user."""
        call_command('create_hr')
        self.assertTrue(HRUser.objects.filter(email='prompted@company.com').exists())
        mock_input.assert_called_once_with('Email: ')

    @patch('builtins.input', return_value='   ')
    def test_create_hr__empty_prompt_raises_error(self, mock_input):
        """Fails if the user provides a blank email at the prompt."""
        with self.assertRaisesMessage(CommandError, 'Email is required.'):
            call_command('create_hr')

    def test_create_hr__with_existing_employee__links_successfully(self):
        """Links HR user to an existing employee via --employee-pk."""
        emp = Employee.objects.create(
            first_name='Existing',
            last_name='User',
            personal_email='existing.personal@company.com',
            company_email='existing@company.com',
            gender=Gender.PREFER_NOT_TO_SAY,
            department='HR',
            job_title='HR',
            seniority_level=SeniorityLevel.SENIOR,
            employment_type=EmploymentType.FULL_TIME,
            country='United States',
            salary=0,
            currency=Currency.USD,
            date_joining=timezone.localdate(),
            status=EmployeeStatus.ACTIVE,
        )

        call_command(
            'create_hr',
            email='hr.existing@company.com',
            employee_pk=emp.pk,
            no_input=True,
        )

        user = HRUser.objects.get(email='hr.existing@company.com')
        self.assertEqual(user.employee.pk, emp.pk)

    def test_create_hr__invalid_employee_pk__raises_error(self):
        """Fails if the provided employee_pk does not exist."""
        with self.assertRaisesMessage(CommandError, 'Employee 9999 not found.'):
            call_command(
                'create_hr',
                email='fail@company.com',
                employee_pk=9999,
                no_input=True,
            )

    def test_create_hr__employee_already_linked__raises_error(self):
        """Fails if the employee already has an HRUser attached."""
        call_command('create_hr', email='first@company.com', no_input=True)
        emp = HRUser.objects.get(email='first@company.com').employee

        with self.assertRaisesMessage(
            CommandError,
            f'Employee {emp.pk} is already linked to an HR user.',
        ):
            call_command(
                'create_hr',
                email='second@company.com',
                employee_pk=emp.pk,
                no_input=True,
            )

    def test_create_hr__personal_email_collision__uses_suffix(self):
        """Uses .1 suffix when generated personal_email already exists."""
        email = 'collision@company.com'
        base_personal = f'hr.{email.replace("@", "_")}@internal.local'
        Employee.objects.create(
            first_name='Blocker',
            last_name='User',
            personal_email=base_personal,
            company_email='blocker@company.com',
            gender=Gender.PREFER_NOT_TO_SAY,
            department='HR',
            job_title='HR',
            seniority_level=SeniorityLevel.SENIOR,
            employment_type=EmploymentType.FULL_TIME,
            country='United States',
            salary=0,
            currency=Currency.USD,
            date_joining=timezone.localdate(),
            status=EmployeeStatus.ACTIVE,
        )

        call_command('create_hr', email=email, no_input=True)

        user = HRUser.objects.get(email=email)
        expected = f'hr.{email.replace("@", "_")}.1@internal.local'
        self.assertEqual(user.employee.personal_email, expected)

    def test_create_hr__query_count__new_email_creates_employee(self):
        """Creating a new HR user issues one duplicate check plus employee/user inserts."""
        expected_queries = expected_create_hr_new_employee_query_count()

        with self.assertNumQueries(expected_queries):
            call_command('create_hr', email='query.new@company.com', no_input=True)

    def test_create_hr__query_count__existing_employee_link(self):
        """Linking an existing employee skips employee creation queries."""
        emp = Employee.objects.create(
            first_name='Existing',
            last_name='User',
            personal_email='query.existing.personal@company.com',
            company_email='query.existing@company.com',
            gender=Gender.PREFER_NOT_TO_SAY,
            department='HR',
            job_title='HR',
            seniority_level=SeniorityLevel.SENIOR,
            employment_type=EmploymentType.FULL_TIME,
            country='United States',
            salary=0,
            currency=Currency.USD,
            date_joining=timezone.localdate(),
            status=EmployeeStatus.ACTIVE,
        )
        expected_queries = expected_create_hr_link_existing_query_count()

        with self.assertNumQueries(expected_queries):
            call_command(
                'create_hr',
                email='query.link@company.com',
                employee_pk=emp.pk,
                no_input=True,
            )

    def test_create_hr__query_count__personal_email_collision(self):
        """Personal email collision adds one extra exists check before employee insert."""
        email = 'query.collision@company.com'
        base_personal = f'hr.{email.replace("@", "_")}@internal.local'
        Employee.objects.create(
            first_name='Blocker',
            last_name='User',
            personal_email=base_personal,
            company_email='query.blocker@company.com',
            gender=Gender.PREFER_NOT_TO_SAY,
            department='HR',
            job_title='HR',
            seniority_level=SeniorityLevel.SENIOR,
            employment_type=EmploymentType.FULL_TIME,
            country='United States',
            salary=0,
            currency=Currency.USD,
            date_joining=timezone.localdate(),
            status=EmployeeStatus.ACTIVE,
        )
        expected_queries = expected_create_hr_new_employee_query_count(
            personal_email_exists_checks=2,
        )

        with self.assertNumQueries(expected_queries):
            call_command('create_hr', email=email, no_input=True)


class CreateHrCommandEdgeTests(TestCase):
    """
    Edge-case tests for create_hr management command query behavior.

    These capture early-exit paths that should avoid unnecessary database work.
    """

    def test_create_hr__query_count__duplicate_email_only(self):
        """Duplicate email should stop after the HR user exists check."""
        call_command('create_hr', email='query.dup@company.com', no_input=True)

        with self.assertNumQueries(1):
            with self.assertRaises(CommandError):
                call_command('create_hr', email='query.dup@company.com', no_input=True)

    def test_create_hr__query_count__missing_email_no_input(self):
        """Missing email with --no-input should fail before touching the database."""
        with self.assertNumQueries(0):
            with self.assertRaisesMessage(
                CommandError, '--email is required when using --no-input.'
            ):
                call_command('create_hr', no_input=True)

    def test_create_hr__query_count__invalid_employee_pk(self):
        """Invalid employee_pk should issue only duplicate and lookup queries."""
        with self.assertNumQueries(2):
            with self.assertRaisesMessage(CommandError, 'Employee 9999 not found.'):
                call_command(
                    'create_hr',
                    email='query.invalid@company.com',
                    employee_pk=9999,
                    no_input=True,
                )

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEBUG=True,
    )
    def test_create_hr__query_count__employee_already_linked(self):
        """Already-linked employee should stop before creating a second HR user."""
        call_command('create_hr', email='query.first@company.com', no_input=True)
        emp = HRUser.objects.get(email='query.first@company.com').employee
        expected_queries = expected_create_hr_link_existing_query_count(create_user=False)

        with self.assertNumQueries(expected_queries):
            with self.assertRaisesMessage(
                CommandError,
                f'Employee {emp.pk} is already linked to an HR user.',
            ):
                call_command(
                    'create_hr',
                    email='query.second@company.com',
                    employee_pk=emp.pk,
                    no_input=True,
                )
