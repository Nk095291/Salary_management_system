import secrets

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
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


class Command(BaseCommand):
    help = 'Create an HR user linked to an employee record and email login credentials.'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='HR login email (company email).')
        parser.add_argument(
            '--employee-pk',
            type=int,
            help='Link an existing employee by primary key instead of creating one.',
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Do not prompt for input (requires --email).',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        employee_pk = options.get('employee_pk')
        no_input = options.get('no_input')

        if not email:
            if no_input:
                raise CommandError('--email is required when using --no-input.')
            email = input('Email: ').strip()

        if not email:
            raise CommandError('Email is required.')

        if HRUser.objects.filter(email__iexact=email).exists():
            raise CommandError(f'HR user with email {email} already exists.')

        password = secrets.token_urlsafe(16)

        if employee_pk:
            try:
                employee = Employee.objects.get(pk=employee_pk)
            except Employee.DoesNotExist as exc:
                raise CommandError(f'Employee {employee_pk} not found.') from exc
            if hasattr(employee, 'hr_user') and employee.hr_user is not None:
                raise CommandError(
                    f'Employee {employee_pk} is already linked to an HR user.'
                )
        else:
            personal_email = f'hr.{email.replace("@", "_")}@internal.local'
            suffix = 1
            while Employee.objects.filter(personal_email=personal_email).exists():
                personal_email = (
                    f'hr.{email.replace("@", "_")}.{suffix}@internal.local'
                )
                suffix += 1

            employee = Employee(
                first_name='HR',
                last_name='Manager',
                personal_email=personal_email,
                company_email=email,
                gender=Gender.PREFER_NOT_TO_SAY,
                department='Human Resources',
                job_title='HR Manager',
                seniority_level=SeniorityLevel.SENIOR,
                employment_type=EmploymentType.FULL_TIME,
                country='United States',
                salary=0,
                currency=Currency.USD,
                date_joining=timezone.localdate(),
                status=EmployeeStatus.ACTIVE,
            )
            employee.save()

        user = HRUser.objects.create_user(
            email=email,
            password=password,
            first_name=employee.first_name,
            last_name=employee.last_name,
            is_staff=True,
            is_active=True,
            employee=employee,
        )

        login_url = settings.FRONTEND_LOGIN_URL
        subject = 'Your HR portal login credentials'
        message = (
            f'Hello {user.first_name},\n\n'
            f'An HR account has been created for you.\n\n'
            f'Login URL: {login_url}\n'
            f'Email: {email}\n'
            f'Temporary password: {password}\n\n'
            f'Please change your password after first login.\n'
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        self.stdout.write(
            self.style.SUCCESS(f'Created HR account for {email} (credentials emailed).')
        )

        if settings.DEBUG or 'console' in settings.EMAIL_BACKEND.lower():
            self.stdout.write(
                self.style.WARNING(
                    f'[DEV] Temporary password for {email}: {password}'
                )
            )
