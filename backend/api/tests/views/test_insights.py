from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import EmployeeStatus, Gender, SeniorityLevel
from api.services import insights
from api.tests.factory.models.employee import EmployeeFactory
from api.tests.helpers import auth_as_hr, auth_as_inactive_hr, auth_as_non_hr


def _insights_auth_query_count() -> int:
    """JWT authentication performs one HRUser lookup on SQLite."""
    return 1


def expected_insights_overview_view_query_count(*, has_active_employees: bool) -> int:
    service_queries = 1 if not has_active_employees else 2
    return _insights_auth_query_count() + service_queries


def expected_insights_by_country_view_query_count() -> int:
    return _insights_auth_query_count() + 2


def expected_insights_by_department_view_query_count() -> int:
    return _insights_auth_query_count() + 1


def expected_insights_by_job_title_view_query_count() -> int:
    return _insights_auth_query_count() + 1


def expected_insights_pay_equity_view_query_count() -> int:
    return _insights_auth_query_count() + 1


class InsightsOverviewViewTests(APITestCase):
    """
    Tests for GET /api/insights/overview/.

    Covered cases:
    - Authenticated HR request returns overview metrics.
    - Unauthenticated request returns 401 unauthorized.
    - Authenticated non-HR request returns 403 forbidden.
    - Deactivated HR user request returns 401 or 403.
    - Empty database returns 200 with zero-valued metrics.
    - POST requests return 405 method not allowed.
    - Predictable DB query counts for unauthenticated and authenticated callers.
    """

    TEST_CASES = [
        'Authenticated HR request returns overview metrics.',
        'Unauthenticated request returns 401 unauthorized.',
        'Authenticated non-HR request returns 403 forbidden.',
        'Deactivated HR user request returns 401 or 403.',
        'Empty database returns 200 with zero-valued metrics.',
        'POST requests return 405 method not allowed.',
        'Predictable DB query counts for unauthenticated and authenticated callers.',
    ]

    def test_InsightsOverviewView__authenticated__returns_overview(self):
        """Authenticated HR request returns overview metrics."""
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
            personal_email='india-overview.personal@example.com',
            company_email='india-overview@company.com',
        )
        auth_as_hr(self.client)

        response = self.client.get(reverse('insights-overview'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['total_employees'], 2)
        self.assertEqual(response.data['highest_paid_country'], 'United States')
        self.assertIn('avg_salary', response.data)
        self.assertIn('gender_distribution', response.data)

    def test_InsightsOverviewView__unauthenticated__returns_401(self):
        """Unauthenticated request returns 401 unauthorized."""
        response = self.client.get(reverse('insights-overview'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_InsightsOverviewView__non_hr__returns_403(self):
        """Authenticated non-HR request returns 403 forbidden."""
        auth_as_non_hr(self.client)

        response = self.client.get(reverse('insights-overview'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_InsightsOverviewView__deactivated_hr_user__returns_401_or_403(self):
        """An HR user who has been deactivated cannot access insights."""
        auth_as_inactive_hr(self.client)

        response = self.client.get(reverse('insights-overview'))

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_InsightsOverviewView__empty_database__returns_200_with_zero_metrics(self):
        """When no data exists, the endpoint returns 200 OK with zero-valued metrics."""
        auth_as_hr(self.client)

        response = self.client.get(reverse('insights-overview'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'total_employees': 0,
            'avg_salary': 0,
            'highest_paid_country': None,
            'gender_distribution': insights._empty_gender_distribution(),
        })

    def test_InsightsOverviewView__post_request__returns_405(self):
        """POST requests are not allowed on read-only endpoints."""
        auth_as_hr(self.client)

        response = self.client.post(reverse('insights-overview'), data={})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_InsightsOverviewView__query_count__unauthenticated_and_authenticated(self):
        """Predictable DB query counts for unauthenticated and authenticated callers."""
        url = reverse('insights-overview')

        with self.assertNumQueries(0):
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        auth_as_hr(self.client)
        with self.assertNumQueries(
            expected_insights_overview_view_query_count(has_active_employees=False),
        ):
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        EmployeeFactory.create(status=EmployeeStatus.ACTIVE)
        with self.assertNumQueries(
            expected_insights_overview_view_query_count(has_active_employees=True),
        ):
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class InsightsByCountryViewTests(APITestCase):
    """
    Tests for GET /api/insights/by-country/.

    Covered cases:
    - Authenticated HR request returns country breakdown.
    - Unauthenticated request returns 401 unauthorized.
    - Authenticated non-HR request returns 403 forbidden.
    - Empty database returns 200 with an empty array.
    - POST requests return 405 method not allowed.
    - Predictable DB query count for authenticated requests.
    """

    TEST_CASES = [
        'Authenticated HR request returns country breakdown.',
        'Unauthenticated request returns 401 unauthorized.',
        'Authenticated non-HR request returns 403 forbidden.',
        'Empty database returns 200 with an empty array.',
        'POST requests return 405 method not allowed.',
        'Predictable DB query count for authenticated requests.',
    ]

    def test_InsightsByCountryView__authenticated__returns_breakdown(self):
        """Authenticated HR request returns country breakdown."""
        EmployeeFactory.create(
            country='India',
            salary=Decimal('40000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        auth_as_hr(self.client)

        response = self.client.get(reverse('insights-by-country'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['country'], 'India')
        self.assertIn('median_salary', response.data[0])

    def test_InsightsByCountryView__unauthenticated__returns_401(self):
        """Unauthenticated request returns 401 unauthorized."""
        response = self.client.get(reverse('insights-by-country'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_InsightsByCountryView__non_hr__returns_403(self):
        """Authenticated non-HR request returns 403 forbidden."""
        auth_as_non_hr(self.client)

        response = self.client.get(reverse('insights-by-country'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_InsightsByCountryView__empty_database__returns_200_and_empty_list(self):
        """When no data exists, the endpoint returns a 200 OK with an empty array."""
        auth_as_hr(self.client)

        response = self.client.get(reverse('insights-by-country'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_InsightsByCountryView__post_request__returns_405(self):
        """POST requests are not allowed on read-only endpoints."""
        auth_as_hr(self.client)

        response = self.client.post(reverse('insights-by-country'), data={})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_InsightsByCountryView__query_count__authenticated_get(self):
        """Predictable DB query count for authenticated requests."""
        EmployeeFactory.create(status=EmployeeStatus.ACTIVE)
        auth_as_hr(self.client)

        with self.assertNumQueries(expected_insights_by_country_view_query_count()):
            response = self.client.get(reverse('insights-by-country'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class InsightsByDepartmentViewTests(APITestCase):
    """
    Tests for GET /api/insights/by-department/.

    Covered cases:
    - Authenticated HR request returns department breakdown.
    - Unauthenticated request returns 401 unauthorized.
    - Authenticated non-HR request returns 403 forbidden.
    - Empty database returns 200 with an empty array.
    - POST requests return 405 method not allowed.
    - Predictable DB query count for authenticated requests.
    """

    TEST_CASES = [
        'Authenticated HR request returns department breakdown.',
        'Unauthenticated request returns 401 unauthorized.',
        'Authenticated non-HR request returns 403 forbidden.',
        'Empty database returns 200 with an empty array.',
        'POST requests return 405 method not allowed.',
        'Predictable DB query count for authenticated requests.',
    ]

    def test_InsightsByDepartmentView__authenticated__returns_breakdown(self):
        """Authenticated HR request returns department breakdown."""
        EmployeeFactory.create(
            department='Engineering',
            salary=Decimal('80000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        auth_as_hr(self.client)

        response = self.client.get(reverse('insights-by-department'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['department'], 'Engineering')
        self.assertIn('total_payroll', response.data[0])

    def test_InsightsByDepartmentView__unauthenticated__returns_401(self):
        """Unauthenticated request returns 401 unauthorized."""
        response = self.client.get(reverse('insights-by-department'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_InsightsByDepartmentView__non_hr__returns_403(self):
        """Authenticated non-HR request returns 403 forbidden."""
        auth_as_non_hr(self.client)

        response = self.client.get(reverse('insights-by-department'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_InsightsByDepartmentView__empty_database__returns_200_and_empty_list(self):
        """When no data exists, the endpoint returns a 200 OK with an empty array."""
        auth_as_hr(self.client)

        response = self.client.get(reverse('insights-by-department'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_InsightsByDepartmentView__post_request__returns_405(self):
        """POST requests are not allowed on read-only endpoints."""
        auth_as_hr(self.client)

        response = self.client.post(reverse('insights-by-department'), data={})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_InsightsByDepartmentView__query_count__authenticated_get(self):
        """Predictable DB query count for authenticated requests."""
        EmployeeFactory.create(status=EmployeeStatus.ACTIVE)
        auth_as_hr(self.client)

        with self.assertNumQueries(expected_insights_by_department_view_query_count()):
            response = self.client.get(reverse('insights-by-department'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class InsightsByJobTitleViewTests(APITestCase):
    """
    Tests for GET /api/insights/by-job-title/.

    Covered cases:
    - No filters returns job title breakdown for all active employees.
    - Single country filter returns matching breakdown.
    - Multiple countries and departments filter the breakdown.
    - Job title filter and whitespace trimming on query params.
    - Blank query param values are ignored.
    - Comma-separated query params are treated as a single string.
    - Query parameters are case-sensitive.
    - Empty database returns 200 with an empty array.
    - Unauthenticated and non-HR access denied.
    - POST requests return 405 method not allowed.
    - Predictable DB query count for authenticated requests.
    """

    TEST_CASES = [
        'No filters returns job title breakdown for all active employees.',
        'Single country filter returns matching breakdown.',
        'Multiple countries and departments filter the breakdown.',
        'Job title filter and whitespace trimming on query params.',
        'Blank query param values are ignored.',
        'Comma-separated query params are treated as a single string.',
        'Query parameters are case-sensitive.',
        'Empty database returns 200 with an empty array.',
        'Unauthenticated and non-HR access denied.',
        'POST requests return 405 method not allowed.',
        'Predictable DB query count for authenticated requests.',
    ]

    def test_InsightsByJobTitleView__no_filters__returns_breakdown(self):
        """No filters returns job title breakdown for all active employees."""
        EmployeeFactory.create(
            country='India',
            job_title='Software Engineer',
            seniority_level=SeniorityLevel.JUNIOR,
            salary=Decimal('40000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        auth_as_hr(self.client)

        response = self.client.get(reverse('insights-by-job-title'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['job_title'], 'Software Engineer')

    def test_InsightsByJobTitleView__with_country__returns_breakdown(self):
        """Single country filter returns matching breakdown."""
        EmployeeFactory.create(
            country='India',
            job_title='Software Engineer',
            seniority_level=SeniorityLevel.JUNIOR,
            salary=Decimal('40000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            country='United States',
            job_title='Product Manager',
            seniority_level=SeniorityLevel.MID,
            salary=Decimal('90000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='pm-us.personal@example.com',
            company_email='pm-us@company.com',
        )
        auth_as_hr(self.client)

        response = self.client.get(
            reverse('insights-by-job-title'),
            {'countries': 'India'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = {row['job_title'] for row in response.data}
        self.assertIn('Software Engineer', titles)
        self.assertNotIn('Product Manager', titles)

    def test_InsightsByJobTitleView__with_multiple_filters__returns_filtered(self):
        """Multiple countries and departments filter the breakdown."""
        EmployeeFactory.create(
            country='India',
            department='Engineering',
            job_title='Software Engineer',
            seniority_level=SeniorityLevel.JUNIOR,
            salary=Decimal('40000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            country='United States',
            department='Engineering',
            job_title='Software Engineer',
            seniority_level=SeniorityLevel.SENIOR,
            salary=Decimal('120000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='se-us.personal@example.com',
            company_email='se-us@company.com',
        )
        EmployeeFactory.create(
            country='India',
            department='Sales',
            job_title='Account Executive',
            seniority_level=SeniorityLevel.MID,
            salary=Decimal('45000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='ae-in.personal@example.com',
            company_email='ae-in@company.com',
        )
        auth_as_hr(self.client)

        response = self.client.get(
            reverse('insights-by-job-title'),
            [
                ('countries', 'India'),
                ('countries', 'United States'),
                ('departments', 'Engineering'),
            ],
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['job_title'], 'Software Engineer')

    def test_InsightsByJobTitleView__with_job_title_and_whitespace__returns_filtered(self):
        """Job title filter and whitespace trimming on query params."""
        EmployeeFactory.create(
            country='India',
            department='Engineering',
            job_title='Software Engineer',
            seniority_level=SeniorityLevel.JUNIOR,
            salary=Decimal('40000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            country='India',
            department='Engineering',
            job_title='Product Manager',
            seniority_level=SeniorityLevel.MID,
            salary=Decimal('90000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='pm-in.personal@example.com',
            company_email='pm-in@company.com',
        )
        auth_as_hr(self.client)

        response = self.client.get(
            reverse('insights-by-job-title'),
            [
                ('countries', '  India  '),
                ('departments', ' Engineering '),
                ('job_titles', ' Software Engineer '),
            ],
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['job_title'], 'Software Engineer')

    def test_InsightsByJobTitleView__blank_query_params__ignored(self):
        """Blank query param values are ignored."""
        EmployeeFactory.create(
            job_title='Software Engineer',
            seniority_level=SeniorityLevel.JUNIOR,
            salary=Decimal('40000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        auth_as_hr(self.client)

        response = self.client.get(
            reverse('insights-by-job-title'),
            [
                ('countries', ''),
                ('countries', '   '),
                ('departments', ''),
                ('job_titles', ''),
            ],
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_InsightsByJobTitleView__comma_separated_params__treated_as_single_string(self):
        """
        getlist() does not auto-split commas. '?countries=A,B' searches for the literal string 'A,B'.
        This test documents the expected API contract.
        """
        EmployeeFactory.create(
            country='India',
            job_title='Engineer',
            status=EmployeeStatus.ACTIVE,
        )
        auth_as_hr(self.client)

        response = self.client.get(
            reverse('insights-by-job-title'),
            {'countries': 'India,United States'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_InsightsByJobTitleView__case_sensitive_params__require_exact_match(self):
        """Query parameters are case-sensitive."""
        EmployeeFactory.create(
            country='India',
            job_title='Engineer',
            status=EmployeeStatus.ACTIVE,
        )
        auth_as_hr(self.client)

        response = self.client.get(
            reverse('insights-by-job-title'),
            {'countries': 'india'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_InsightsByJobTitleView__empty_database__returns_200_and_empty_list(self):
        """When no data exists, the endpoint returns a 200 OK with an empty array."""
        auth_as_hr(self.client)

        response = self.client.get(reverse('insights-by-job-title'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_InsightsByJobTitleView__unauthenticated__returns_401(self):
        """Unauthenticated request returns 401 unauthorized."""
        response = self.client.get(reverse('insights-by-job-title'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_InsightsByJobTitleView__non_hr__returns_403(self):
        """Authenticated non-HR request returns 403 forbidden."""
        auth_as_non_hr(self.client)

        response = self.client.get(reverse('insights-by-job-title'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_InsightsByJobTitleView__post_request__returns_405(self):
        """POST requests are not allowed on read-only endpoints."""
        auth_as_hr(self.client)

        response = self.client.post(reverse('insights-by-job-title'), data={})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_InsightsByJobTitleView__query_count__authenticated_get(self):
        """Predictable DB query count for authenticated requests."""
        EmployeeFactory.create(status=EmployeeStatus.ACTIVE)
        auth_as_hr(self.client)

        with self.assertNumQueries(expected_insights_by_job_title_view_query_count()):
            response = self.client.get(reverse('insights-by-job-title'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class InsightsPayEquityViewTests(APITestCase):
    """
    Tests for GET /api/insights/pay-equity/.

    Covered cases:
    - Authenticated HR request returns pay equity breakdown.
    - Unauthenticated request returns 401 unauthorized.
    - Authenticated non-HR request returns 403 forbidden.
    - Empty database returns 200 with an empty array.
    - POST requests return 405 method not allowed.
    - Predictable DB query count for authenticated requests.
    """

    TEST_CASES = [
        'Authenticated HR request returns pay equity breakdown.',
        'Unauthenticated request returns 401 unauthorized.',
        'Authenticated non-HR request returns 403 forbidden.',
        'Empty database returns 200 with an empty array.',
        'POST requests return 405 method not allowed.',
        'Predictable DB query count for authenticated requests.',
    ]

    def test_InsightsPayEquityView__authenticated__returns_breakdown(self):
        """Authenticated HR request returns pay equity breakdown."""
        EmployeeFactory.create(
            department='Engineering',
            gender=Gender.MALE,
            salary=Decimal('100000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            department='Engineering',
            gender=Gender.FEMALE,
            salary=Decimal('80000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='eng-female-view.personal@example.com',
            company_email='eng-female-view@company.com',
        )
        auth_as_hr(self.client)

        response = self.client.get(reverse('insights-pay-equity'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['department'], 'Engineering')
        self.assertEqual(response.data[0]['gap_percent'], 20.0)

    def test_InsightsPayEquityView__unauthenticated__returns_401(self):
        """Unauthenticated request returns 401 unauthorized."""
        response = self.client.get(reverse('insights-pay-equity'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_InsightsPayEquityView__non_hr__returns_403(self):
        """Authenticated non-HR request returns 403 forbidden."""
        auth_as_non_hr(self.client)

        response = self.client.get(reverse('insights-pay-equity'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_InsightsPayEquityView__empty_database__returns_200_and_empty_list(self):
        """When no data exists, the endpoint returns a 200 OK with an empty array."""
        auth_as_hr(self.client)

        response = self.client.get(reverse('insights-pay-equity'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_InsightsPayEquityView__post_request__returns_405(self):
        """POST requests are not allowed on read-only endpoints."""
        auth_as_hr(self.client)

        response = self.client.post(reverse('insights-pay-equity'), data={})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_InsightsPayEquityView__query_count__authenticated_get(self):
        """Predictable DB query count for authenticated requests."""
        EmployeeFactory.create(
            gender=Gender.MALE,
            status=EmployeeStatus.ACTIVE,
        )
        auth_as_hr(self.client)

        with self.assertNumQueries(expected_insights_pay_equity_view_query_count()):
            response = self.client.get(reverse('insights-pay-equity'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
