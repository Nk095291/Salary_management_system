from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import EmployeeStatus, Gender, SeniorityLevel
from api.tests.factory.models.employee import EmployeeFactory
from api.tests.helpers import auth_as_hr


class InsightsOverviewViewTests(APITestCase):
    """
    Tests for GET /api/insights/overview/.

    Covered cases:
    - Authenticated request returns overview metrics.
    - Unauthenticated request returns 401 unauthorized.
    """

    TEST_CASES = [
        'Authenticated request returns overview metrics.',
        'Unauthenticated request returns 401 unauthorized.',
    ]

    def test_InsightsOverviewView__authenticated__returns_overview(self):
        """Authenticated request returns overview metrics."""
        # GIVEN
        EmployeeFactory.create(
            country='United States',
            gender=Gender.MALE,
            salary=Decimal('100000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            country='India',
            gender=Gender.FEMALE,
            salary=Decimal('50000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        auth_as_hr(self.client)

        # WHEN
        response = self.client.get(reverse('insights-overview'))

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['total_employees'], 2)
        self.assertEqual(response.data['highest_paid_country'], 'United States')
        self.assertIn('avg_salary', response.data)
        self.assertIn('gender_distribution', response.data)

    def test_InsightsOverviewView__unauthenticated__returns_401(self):
        """Unauthenticated request returns 401 unauthorized."""
        # GIVEN
        url = reverse('insights-overview')

        # WHEN
        response = self.client.get(url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class InsightsByJobTitleViewTests(APITestCase):
    """
    Tests for GET /api/insights/by-job-title/.

    Covered cases:
    - Missing country parameter returns 400 bad request.
    - Valid country returns job title breakdown.
    """

    TEST_CASES = [
        'Missing country parameter returns 400 bad request.',
        'Valid country returns job title breakdown.',
    ]

    def test_InsightsByJobTitleView__missing_country__returns_400(self):
        """Missing country parameter returns 400 bad request."""
        # GIVEN
        auth_as_hr(self.client)

        # WHEN
        response = self.client.get(reverse('insights-by-job-title'))

        # THEN
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_InsightsByJobTitleView__with_country__returns_breakdown(self):
        """Valid country returns job title breakdown."""
        # GIVEN
        EmployeeFactory.create(
            country='India',
            job_title='Software Engineer',
            seniority_level=SeniorityLevel.JUNIOR,
            salary=Decimal('40000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        auth_as_hr(self.client)

        # WHEN
        response = self.client.get(
            reverse('insights-by-job-title'),
            {'country': 'India'},
        )

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['job_title'], 'Software Engineer')
