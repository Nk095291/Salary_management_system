from decimal import Decimal

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Gender(models.TextChoices):
    MALE = 'Male', 'Male'
    FEMALE = 'Female', 'Female'
    NON_BINARY = 'Non-binary', 'Non-binary'
    PREFER_NOT_TO_SAY = 'Prefer not to say', 'Prefer not to say'


class SeniorityLevel(models.TextChoices):
    JUNIOR = 'Junior', 'Junior'
    MID = 'Mid', 'Mid'
    SENIOR = 'Senior', 'Senior'
    LEAD = 'Lead', 'Lead'
    PRINCIPAL = 'Principal', 'Principal'


class EmploymentType(models.TextChoices):
    FULL_TIME = 'Full-time', 'Full-time'
    PART_TIME = 'Part-time', 'Part-time'
    CONTRACT = 'Contract', 'Contract'
    INTERNSHIP = 'Internship', 'Internship'


class EmployeeStatus(models.TextChoices):
    ACTIVE = 'Active', 'Active'
    ON_LEAVE = 'On Leave', 'On Leave'
    TERMINATED = 'Terminated', 'Terminated'


class Currency(models.TextChoices):
    USD = 'USD', 'USD'
    INR = 'INR', 'INR'
    GBP = 'GBP', 'GBP'
    EUR = 'EUR', 'EUR'
    AUD = 'AUD', 'AUD'
    CAD = 'CAD', 'CAD'


class Employee(models.Model):
    employee_id = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    personal_email = models.EmailField(unique=True)
    company_email = models.EmailField(unique=True)
    gender = models.CharField(max_length=20, choices=Gender.choices)
    date_of_birth = models.DateField(null=True, blank=True)
    department = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    seniority_level = models.CharField(max_length=20, choices=SeniorityLevel.choices)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    country = models.CharField(max_length=100, db_index=True)
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    currency = models.CharField(max_length=3, choices=Currency.choices)
    date_joining = models.DateField()
    date_relieving = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=EmployeeStatus.choices,
        default=EmployeeStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee_id']
        indexes = [
            models.Index(fields=['country', 'job_title']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(date_relieving__isnull=True)
                | models.Q(date_relieving__gte=models.F('date_joining')),
                name='employee_relieving_after_joining',
            ),
        ]
    def __str__(self):
        return f'{self.employee_id} - {self.first_name} {self.last_name}'

    def clean(self):
        super().clean()
        if (
            self.date_relieving
            and self.date_joining
            and self.date_relieving < self.date_joining
        ):
            raise ValidationError(
                {'date_relieving': 'Date of relieving must be on or after date of joining.'}
            )
    

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.full_clean()
        super().save(*args, **kwargs)
        if is_new and not self.employee_id:
            self.employee_id = f'EMP-{self.pk:05d}'
            super().save(update_fields=['employee_id'])


class HRUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class HRUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    employee = models.OneToOneField(
        Employee,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='hr_user',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = HRUserManager()

    def __str__(self):
        return self.email
