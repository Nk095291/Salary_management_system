from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Employee
from api.tests.factory.models.employee import EmployeeFactory
from api.tests.helpers import auth_as_hr


def _valid_employee_payload(**overrides):
    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'personal_email': 'john.personal@example.com',
        'company_email': 'john@company.com',
        'gender': 'Male',
        'department': 'Engineering',
        'job_title': 'Software Engineer',
        'seniority_level': 'Mid',
        'employment_type': 'Full-time',
        'country': 'United States',
        'salary': '80000.00',
        'currency': 'USD',
        'date_joining': '2021-05-01',
        'status': 'Active',
    }
    data.update(overrides)
    return data


class EmployeeViewSetTests(APITestCase):
    """
    Tests for EmployeeViewSet CRUD endpoints.

    Covered cases:
    - Unauthenticated list request returns 401 unauthorized.
    - Authenticated HR user list returns paginated employees.
    - Valid payload creates employee with employee_id.
    - Invalid payload returns 400 bad request.
    - Existing pk retrieve returns employee details.
    - Patch payload updates employee fields.
    - Delete existing employee removes record from database.
    """

    def test_EmployeeViewSet__unauthenticated_list__returns_401(self):
        """Unauthenticated list request returns 401 unauthorized."""
        # GIVEN
        EmployeeFactory.create()
        url = reverse('employee-list')

        # WHEN
        response = self.client.get(url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_EmployeeViewSet__authenticated_list__returns_paginated_employees(self):
        """Authenticated HR user list returns paginated employees."""
        # GIVEN
        EmployeeFactory.create()
        auth_as_hr(self.client)
        url = reverse('employee-list')

        # WHEN
        response = self.client.get(url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_EmployeeViewSet__valid_payload__creates_employee(self):
        """Valid payload creates employee with employee_id."""
        # GIVEN
        auth_as_hr(self.client)
        url = reverse('employee-list')
        payload = _valid_employee_payload()

        # WHEN
        response = self.client.post(url, payload, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['employee_id'].startswith('EMP-'))
        self.assertEqual(response.data['first_name'], 'John')
        self.assertTrue(Employee.objects.filter(company_email='john@company.com').exists())

    def test_EmployeeViewSet__invalid_payload__returns_400(self):
        """Invalid payload returns 400 bad request."""
        # GIVEN
        auth_as_hr(self.client)
        url = reverse('employee-list')
        payload = _valid_employee_payload()
        del payload['first_name']

        # WHEN
        response = self.client.post(url, payload, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_EmployeeViewSet__existing_pk__returns_employee(self):
        """Existing pk retrieve returns employee details."""
        # GIVEN
        employee = EmployeeFactory.create(first_name='Alice')
        auth_as_hr(self.client)
        url = reverse('employee-detail', kwargs={'pk': employee.pk})

        # WHEN
        response = self.client.get(url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Alice')
        self.assertEqual(response.data['employee_id'], employee.employee_id)

    def test_EmployeeViewSet__patch_payload__updates_employee(self):
        """Patch payload updates employee fields."""
        # GIVEN
        employee = EmployeeFactory.create(salary=Decimal('70000.00'))
        auth_as_hr(self.client)
        url = reverse('employee-detail', kwargs={'pk': employee.pk})

        # WHEN
        response = self.client.patch(
            url,
            {'salary': '95000.00', 'job_title': 'Senior Engineer'},
            format='json',
        )

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['job_title'], 'Senior Engineer')
        employee.refresh_from_db()
        self.assertEqual(employee.salary, Decimal('95000.00'))

    def test_EmployeeViewSet__delete_existing__removes_employee(self):
        """Delete existing employee removes record from database."""
        # GIVEN
        employee = EmployeeFactory.create()
        pk = employee.pk
        auth_as_hr(self.client)
        url = reverse('employee-detail', kwargs={'pk': pk})

        # WHEN
        response = self.client.delete(url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Employee.objects.filter(pk=pk).exists())
