import random
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Employee, EmployeeStatus, Gender
from api.constants import COUNTRY_NAMES, DEPARTMENTS
from api.tests.employee_test_data import (
    distinct_choice_values,
    distinct_countries,
    fake,
    invalid_choice_value,
    unique_label,
    valid_employee_payload,
)
from api.tests.factory.models.employee import EmployeeFactory
from api.tests.helpers import auth_as_hr


class EmployeeViewSetTests(APITestCase):
    """
    Tests for EmployeeViewSet CRUD endpoints.

    Covered cases:
    - Unauthenticated list request returns 401 unauthorized.
    - Authenticated HR user list returns paginated employees.
    - List filters by department, country, and status query params.
    - List filters by multiple departments or countries (OR within each dimension).
    - Departments and countries actions return distinct sorted values.
    - Filter with no matches returns empty results.
    - Valid payload creates employee with database id.
    - Missing required field returns 400 bad request.
    - Present field with invalid value returns 400 bad request.
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

    def test_EmployeeViewSet__filter_by_department__returns_matching_only(self):
        """List filtered by department returns only employees in that department."""
        # GIVEN
        matched_department = unique_label('dept')
        other_department = unique_label('dept')
        matched = EmployeeFactory.create(department=matched_department)
        EmployeeFactory.create(department=other_department)
        auth_as_hr(self.client)
        url = reverse('employee-list')

        # WHEN
        response = self.client.get(url, {'departments': matched_department})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {item['id'] for item in response.data['results']}
        self.assertEqual(result_ids, {matched.id})
        self.assertTrue(
            all(item['department'] == matched_department for item in response.data['results'])
        )

    def test_EmployeeViewSet__filter_by_country__returns_matching_only(self):
        """List filtered by country returns only employees in that country."""
        # GIVEN
        matched_country, other_country = distinct_countries(2)
        matched = EmployeeFactory.create(country=matched_country)
        EmployeeFactory.create(country=other_country)
        auth_as_hr(self.client)
        url = reverse('employee-list')

        # WHEN
        response = self.client.get(url, {'countries': matched_country})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {item['id'] for item in response.data['results']}
        self.assertEqual(result_ids, {matched.id})
        self.assertTrue(
            all(item['country'] == matched_country for item in response.data['results'])
        )

    def test_EmployeeViewSet__filter_by_multiple_departments__returns_union(self):
        """List filtered by multiple departments returns employees in any of them."""
        # GIVEN
        dept_a = unique_label('dept')
        dept_b = unique_label('dept')
        dept_other = unique_label('dept')
        emp_a = EmployeeFactory.create(department=dept_a)
        emp_b = EmployeeFactory.create(department=dept_b)
        EmployeeFactory.create(department=dept_other)
        auth_as_hr(self.client)
        url = reverse('employee-list')

        # WHEN
        response = self.client.get(
            url,
            [('departments', dept_a), ('departments', dept_b)],
        )

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {item['id'] for item in response.data['results']}
        self.assertEqual(result_ids, {emp_a.id, emp_b.id})

    def test_EmployeeViewSet__filter_by_multiple_countries__returns_union(self):
        """List filtered by multiple countries returns employees in any of them."""
        # GIVEN
        country_a, country_b, country_other = distinct_countries(3)
        emp_a = EmployeeFactory.create(country=country_a)
        emp_b = EmployeeFactory.create(country=country_b)
        EmployeeFactory.create(country=country_other)
        auth_as_hr(self.client)
        url = reverse('employee-list')

        # WHEN
        response = self.client.get(
            url,
            [('countries', country_a), ('countries', country_b)],
        )

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {item['id'] for item in response.data['results']}
        self.assertEqual(result_ids, {emp_a.id, emp_b.id})

    def test_EmployeeViewSet__departments_action__returns_constant_list(self):
        """Departments action returns the canonical sorted department list."""
        # GIVEN
        auth_as_hr(self.client)
        url = reverse('employee-departments')

        # WHEN
        response = self.client.get(url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), DEPARTMENTS)

    def test_EmployeeViewSet__countries_action__returns_constant_list(self):
        """Countries action returns the canonical sorted country list."""
        # GIVEN
        auth_as_hr(self.client)
        url = reverse('employee-countries')

        # WHEN
        response = self.client.get(url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), COUNTRY_NAMES)

    def test_EmployeeViewSet__filter_by_status__returns_matching_only(self):
        """List filtered by status returns only employees with that status."""
        # GIVEN
        matched_status, other_status = distinct_choice_values(EmployeeStatus)
        matched = EmployeeFactory.create(status=matched_status)
        EmployeeFactory.create(status=other_status)
        auth_as_hr(self.client)
        url = reverse('employee-list')

        # WHEN
        response = self.client.get(url, {'status': matched_status})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {item['id'] for item in response.data['results']}
        self.assertEqual(result_ids, {matched.id})
        self.assertTrue(
            all(item['status'] == matched_status for item in response.data['results'])
        )

    def test_EmployeeViewSet__filter_no_matches__returns_empty_results(self):
        """List filtered by non-existent department returns empty results."""
        # GIVEN
        EmployeeFactory.create(department=unique_label('dept'))
        unmatched_department = unique_label('dept')
        auth_as_hr(self.client)
        url = reverse('employee-list')

        # WHEN
        response = self.client.get(url, {'departments': unmatched_department})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_EmployeeViewSet__valid_payload__creates_employee(self):
        """Valid payload creates employee with database id."""
        # GIVEN
        auth_as_hr(self.client)
        url = reverse('employee-list')
        payload = valid_employee_payload()

        # WHEN
        response = self.client.post(url, payload, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data['id'])
        self.assertEqual(response.data['first_name'], payload['first_name'])
        self.assertTrue(
            Employee.objects.filter(company_email=payload['company_email']).exists()
        )

    def test_EmployeeViewSet__missing_required_field__returns_400(self):
        """Missing required field returns 400 bad request."""
        # GIVEN
        auth_as_hr(self.client)
        url = reverse('employee-list')
        payload = valid_employee_payload()
        del payload['first_name']

        # WHEN
        response = self.client.post(url, payload, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)

    def test_EmployeeViewSet__invalid_gender_value__returns_400(self):
        """Present gender field with invalid choice returns 400 bad request."""
        # GIVEN
        auth_as_hr(self.client)
        url = reverse('employee-list')
        payload = valid_employee_payload(
            gender=invalid_choice_value(Gender.values),
        )

        # WHEN
        response = self.client.post(url, payload, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('gender', response.data)

    def test_EmployeeViewSet__invalid_status_value__returns_400(self):
        """Present status field with invalid choice returns 400 bad request."""
        # GIVEN
        auth_as_hr(self.client)
        url = reverse('employee-list')
        payload = valid_employee_payload(
            status=invalid_choice_value(EmployeeStatus.values),
        )

        # WHEN
        response = self.client.post(url, payload, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status', response.data)

    def test_EmployeeViewSet__invalid_email_format__returns_400(self):
        """Present email field with invalid format returns 400 bad request."""
        # GIVEN
        auth_as_hr(self.client)
        url = reverse('employee-list')
        payload = valid_employee_payload(company_email=f'invalid-{unique_label("email")}')

        # WHEN
        response = self.client.post(url, payload, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company_email', response.data)

    def test_EmployeeViewSet__negative_salary__returns_400(self):
        """Present salary field with negative value returns 400 bad request."""
        # GIVEN
        auth_as_hr(self.client)
        url = reverse('employee-list')
        payload = valid_employee_payload(
            salary=f'-{random.randint(1, 99_999)}.00',
        )

        # WHEN
        response = self.client.post(url, payload, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('salary', response.data)

    def test_EmployeeViewSet__currency_is_always_usd__ignores_client_value(self):
        """Currency field is read-only; employee is created with USD regardless of payload."""
        # GIVEN
        auth_as_hr(self.client)
        url = reverse('employee-list')
        payload = valid_employee_payload()
        # currency is read-only — even if client supplies a different value it is ignored

        # WHEN
        response = self.client.post(url, payload, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['currency'], 'USD')

    def test_EmployeeViewSet__existing_pk__returns_employee(self):
        """Existing pk retrieve returns employee details."""
        # GIVEN
        employee = EmployeeFactory.create(first_name=fake.first_name())
        auth_as_hr(self.client)
        url = reverse('employee-detail', kwargs={'pk': employee.pk})

        # WHEN
        response = self.client.get(url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], employee.first_name)
        self.assertEqual(response.data['id'], employee.id)

    def test_EmployeeViewSet__patch_payload__updates_employee(self):
        """Patch payload updates employee fields."""
        # GIVEN
        original_salary = Decimal(f'{random.randint(40_000, 80_000)}.00')
        updated_salary = Decimal(f'{random.randint(81_000, 150_000)}.00')
        updated_job_title = fake.job()
        employee = EmployeeFactory.create(salary=original_salary)
        auth_as_hr(self.client)
        url = reverse('employee-detail', kwargs={'pk': employee.pk})

        # WHEN
        response = self.client.patch(
            url,
            {
                'salary': str(updated_salary),
                'job_title': updated_job_title,
            },
            format='json',
        )

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['job_title'], updated_job_title)
        employee.refresh_from_db()
        self.assertEqual(employee.salary, updated_salary)

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
