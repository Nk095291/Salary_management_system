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

        self.assertIn('Non-binary', response.data['gender_distribution'])

        self.assertIn('Prefer not to say', response.data['gender_distribution'])



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

    - No filters returns job title breakdown for all active employees.

    - Single country filter returns matching breakdown.

    - Multiple countries and departments filter the breakdown.

    """



    TEST_CASES = [

        'No filters returns job title breakdown for all active employees.',

        'Single country filter returns matching breakdown.',

        'Multiple countries and departments filter the breakdown.',

    ]



    def test_InsightsByJobTitleView__no_filters__returns_breakdown(self):

        """No filters returns job title breakdown for all active employees."""

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

        response = self.client.get(reverse('insights-by-job-title'))



        # THEN

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertGreaterEqual(len(response.data), 1)

        self.assertEqual(response.data[0]['job_title'], 'Software Engineer')



    def test_InsightsByJobTitleView__with_country__returns_breakdown(self):

        """Single country filter returns matching breakdown."""

        # GIVEN

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

        )

        auth_as_hr(self.client)



        # WHEN

        response = self.client.get(

            reverse('insights-by-job-title'),

            {'countries': 'India'},

        )



        # THEN

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        titles = {row['job_title'] for row in response.data}

        self.assertIn('Software Engineer', titles)

        self.assertNotIn('Product Manager', titles)



    def test_InsightsByJobTitleView__with_multiple_filters__returns_filtered(self):

        """Multiple countries and departments filter the breakdown."""

        # GIVEN

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

        )

        EmployeeFactory.create(

            country='India',

            department='Sales',

            job_title='Account Executive',

            seniority_level=SeniorityLevel.MID,

            salary=Decimal('45000.00'),

            status=EmployeeStatus.ACTIVE,

        )

        auth_as_hr(self.client)



        # WHEN

        response = self.client.get(

            reverse('insights-by-job-title'),

            [

                ('countries', 'India'),

                ('countries', 'United States'),

                ('departments', 'Engineering'),

            ],

        )



        # THEN

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 1)

        self.assertEqual(response.data[0]['job_title'], 'Software Engineer')

