from io import StringIO

from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from api.models import HRUser


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
    """

    TEST_CASES = [
        'New email creates HR user, employee link, and sends email.',
        'Duplicate email raises command error.',
        'Dev mode prints temporary password to stdout.',
    ]

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
