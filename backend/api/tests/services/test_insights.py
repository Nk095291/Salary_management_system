from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase

from api.models import EmployeeStatus, Gender, SeniorityLevel
from api.services import insights
from api.tests.factory.models.employee import EmployeeFactory


def expected_overview_query_count(*, has_active_employees: bool) -> int:
    """COUNT only when empty; otherwise COUNT + AVG + country AVG + gender GROUP BY."""
    return 1 if not has_active_employees else 4


def expected_by_country_query_count() -> int:
    """One GROUP BY aggregates query and one salary scan for medians."""
    return 2


def expected_by_department_query_count() -> int:
    return 1


def expected_by_job_title_query_count() -> int:
    return 1


def expected_pay_equity_query_count() -> int:
    return 1


class InsightsHelperTests(TestCase):
    """
    Tests for private helpers in api.services.insights.

    Covered cases:
    - _decimal converts values and treats None as zero.
    - _median returns zero for an empty list and the statistical median otherwise.
    - _empty_gender_distribution and _empty_gender_averages seed all genders.
    - active_employees excludes terminated records.
    """

    TEST_CASES = [
        '_decimal converts values and treats None as zero.',
        '_median returns zero for an empty list and the statistical median otherwise.',
        '_empty_gender_distribution and _empty_gender_averages seed all genders.',
        'active_employees excludes terminated records.',
    ]

    def test_insightsHelpers__decimal__converts_and_handles_none(self):
        """_decimal converts values and treats None as zero."""
        self.assertEqual(insights._decimal(Decimal('123.45')), 123.45)
        self.assertEqual(insights._decimal(None), 0.0)

    def test_insightsHelpers__median__empty_and_non_empty(self):
        """_median returns zero for an empty list and the statistical median otherwise."""
        self.assertEqual(insights._median([]), 0.0)
        self.assertEqual(insights._median([10.0, 20.0, 30.0]), 20.0)
        self.assertEqual(insights._median([10.0, 30.0]), 20.0)

    def test_insightsHelpers__empty_gender_structures__include_all_genders(self):
        """_empty_gender_distribution and _empty_gender_averages seed all genders."""
        distribution = insights._empty_gender_distribution()
        averages = insights._empty_gender_averages()

        for gender in insights.GENDER_ORDER:
            self.assertEqual(distribution[gender], 0)
            self.assertEqual(averages[gender], 0.0)

    def test_insightsHelpers__active_employees__excludes_terminated(self):
        """active_employees excludes terminated records."""
        active = EmployeeFactory.create(status=EmployeeStatus.ACTIVE)
        EmployeeFactory.create(
            status=EmployeeStatus.TERMINATED,
            personal_email='terminated.personal@example.com',
            company_email='terminated@company.com',
        )

        ids = list(insights.active_employees().values_list('id', flat=True))

        self.assertEqual(ids, [active.id])


class GetOverviewTests(TestCase):
    """
    Tests for insights.get_overview().

    Covered cases:
    - No active employees returns zeros and empty gender distribution.
    - Active employees return aggregated metrics and highest-paid country.
    - Gender percentages are adjusted so they sum to 100.
    - Terminated employees are excluded from metrics.
    - Predictable DB query count for empty and populated datasets.
    """

    TEST_CASES = [
        'No active employees returns zeros and empty gender distribution.',
        'Active employees return aggregated metrics and highest-paid country.',
        'Gender percentages are adjusted so they sum to 100.',
        'Terminated employees are excluded from metrics.',
        'Predictable DB query count for empty and populated datasets.',
    ]

    def test_getOverview__no_active_employees__returns_empty_metrics(self):
        """No active employees returns zeros and empty gender distribution."""
        EmployeeFactory.create(
            status=EmployeeStatus.TERMINATED,
            personal_email='gone.personal@example.com',
            company_email='gone@company.com',
        )

        result = insights.get_overview()

        self.assertEqual(
            result,
            {
                'total_employees': 0,
                'avg_salary': 0,
                'highest_paid_country': None,
                'gender_distribution': insights._empty_gender_distribution(),
            },
        )

    def test_getOverview__with_active_employees__returns_metrics(self):
        """Active employees return aggregated metrics and highest-paid country."""
        EmployeeFactory.create(
            country='United States',
            gender=Gender.MALE,
            salary=Decimal('120000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            country='India',
            gender=Gender.FEMALE,
            salary=Decimal('40000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='india.personal@example.com',
            company_email='india@company.com',
        )

        result = insights.get_overview()

        self.assertEqual(result['total_employees'], 2)
        self.assertEqual(result['avg_salary'], 80000.0)
        self.assertEqual(result['highest_paid_country'], 'United States')
        self.assertEqual(sum(result['gender_distribution'].values()), 100)

    def test_getOverview__rounding_remainder__adjusts_largest_bucket(self):
        """Gender percentages are adjusted so they sum to 100."""
        for index, gender in enumerate(
            (Gender.MALE, Gender.FEMALE, Gender.NON_BINARY),
            start=1,
        ):
            EmployeeFactory.create(
                gender=gender,
                salary=Decimal('50000.00'),
                status=EmployeeStatus.ACTIVE,
                personal_email=f'remainder{index}.personal@example.com',
                company_email=f'remainder{index}@company.com',
            )

        result = insights.get_overview()

        self.assertEqual(result['total_employees'], 3)
        self.assertEqual(sum(result['gender_distribution'].values()), 100)

    def test_getOverview__terminated_employees__excluded_from_count(self):
        """Terminated employees are excluded from metrics."""
        EmployeeFactory.create(
            gender=Gender.MALE,
            salary=Decimal('100000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            gender=Gender.FEMALE,
            salary=Decimal('200000.00'),
            status=EmployeeStatus.TERMINATED,
            personal_email='terminated2.personal@example.com',
            company_email='terminated2@company.com',
        )

        result = insights.get_overview()

        self.assertEqual(result['total_employees'], 1)
        self.assertEqual(result['gender_distribution'][Gender.MALE], 100)

    def test_getOverview__query_count__empty_and_populated(self):
        """Predictable DB query count for empty and populated datasets."""
        with self.assertNumQueries(expected_overview_query_count(has_active_employees=False)):
            insights.get_overview()

        EmployeeFactory.create(status=EmployeeStatus.ACTIVE)

        with self.assertNumQueries(expected_overview_query_count(has_active_employees=True)):
            insights.get_overview()

    @patch.object(insights, 'active_employees')
    def test_getOverview__no_country_aggregate_row__highest_paid_country_none(
        self,
        mock_active_employees,
    ):
        """When country aggregation returns no row, highest_paid_country is None."""
        mock_qs = MagicMock()
        mock_qs.count.return_value = 2
        mock_qs.aggregate.return_value = {'avg': Decimal('50000.00')}

        country_chain = MagicMock()
        country_chain.annotate.return_value.order_by.return_value.first.return_value = None

        gender_chain = MagicMock()
        gender_chain.annotate.return_value = []

        def values_side_effect(*args, **_kwargs):
            if args and args[0] == 'country':
                return country_chain
            if args and args[0] == 'gender':
                return gender_chain
            return MagicMock()

        mock_qs.values.side_effect = values_side_effect
        mock_active_employees.return_value = mock_qs

        result = insights.get_overview()

        self.assertEqual(result['highest_paid_country'], None)


class GetByCountryTests(TestCase):
    """
    Tests for insights.get_by_country().

    Covered cases:
    - Empty dataset returns an empty list.
    - Country rows include min, max, average, and median salaries.
    - Terminated employees are excluded.
    - Predictable DB query count.
    """

    TEST_CASES = [
        'Empty dataset returns an empty list.',
        'Country rows include min, max, average, and median salaries.',
        'Terminated employees are excluded.',
        'Predictable DB query count.',
    ]

    def test_getByCountry__no_active_employees__returns_empty_list(self):
        """Empty dataset returns an empty list."""
        self.assertEqual(insights.get_by_country(), [])

    def test_getByCountry__with_employees__returns_country_aggregates(self):
        """Country rows include min, max, average, and median salaries."""
        EmployeeFactory.create(
            country='India',
            salary=Decimal('30000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            country='India',
            salary=Decimal('50000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='india2.personal@example.com',
            company_email='india2@company.com',
        )
        EmployeeFactory.create(
            country='United States',
            salary=Decimal('90000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='us.personal@example.com',
            company_email='us@company.com',
        )

        result = insights.get_by_country()
        by_country = {row['country']: row for row in result}

        india = by_country['India']
        self.assertEqual(india['headcount'], 2)
        self.assertEqual(india['min_salary'], 30000.0)
        self.assertEqual(india['max_salary'], 50000.0)
        self.assertEqual(india['avg_salary'], 40000.0)
        self.assertEqual(india['median_salary'], 40000.0)

        united_states = by_country['United States']
        self.assertEqual(united_states['headcount'], 1)
        self.assertEqual(united_states['median_salary'], 90000.0)

    def test_getByCountry__terminated_employees__excluded(self):
        """Terminated employees are excluded."""
        EmployeeFactory.create(
            country='India',
            salary=Decimal('40000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            country='India',
            salary=Decimal('99999.00'),
            status=EmployeeStatus.TERMINATED,
            personal_email='terminated-country.personal@example.com',
            company_email='terminated-country@company.com',
        )

        result = insights.get_by_country()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['headcount'], 1)

    def test_getByCountry__query_count__two_queries(self):
        """Predictable DB query count."""
        EmployeeFactory.create(status=EmployeeStatus.ACTIVE)

        with self.assertNumQueries(expected_by_country_query_count()):
            insights.get_by_country()


class GetByDepartmentTests(TestCase):
    """
    Tests for insights.get_by_department().

    Covered cases:
    - Departments return headcount, average salary, and total payroll.
    - Terminated employees are excluded.
    - Predictable DB query count.
    """

    TEST_CASES = [
        'Departments return headcount, average salary, and total payroll.',
        'Terminated employees are excluded.',
        'Predictable DB query count.',
    ]

    def test_getByDepartment__with_employees__returns_department_aggregates(self):
        """Departments return headcount, average salary, and total payroll."""
        EmployeeFactory.create(
            department='Engineering',
            salary=Decimal('80000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            department='Engineering',
            salary=Decimal('100000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='eng2.personal@example.com',
            company_email='eng2@company.com',
        )
        EmployeeFactory.create(
            department='Sales',
            salary=Decimal('60000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='sales.personal@example.com',
            company_email='sales@company.com',
        )

        result = insights.get_by_department()
        by_department = {row['department']: row for row in result}

        engineering = by_department['Engineering']
        self.assertEqual(engineering['headcount'], 2)
        self.assertEqual(engineering['avg_salary'], 90000.0)
        self.assertEqual(engineering['total_payroll'], 180000.0)

        sales = by_department['Sales']
        self.assertEqual(sales['headcount'], 1)
        self.assertEqual(sales['total_payroll'], 60000.0)

    def test_getByDepartment__terminated_employees__excluded(self):
        """Terminated employees are excluded."""
        EmployeeFactory.create(
            department='Engineering',
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            department='Engineering',
            status=EmployeeStatus.TERMINATED,
            personal_email='terminated-dept.personal@example.com',
            company_email='terminated-dept@company.com',
        )

        result = insights.get_by_department()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['headcount'], 1)

    def test_getByDepartment__query_count__single_group_by(self):
        """Predictable DB query count."""
        EmployeeFactory.create(status=EmployeeStatus.ACTIVE)

        with self.assertNumQueries(expected_by_department_query_count()):
            insights.get_by_department()


class GetByJobTitleTests(TestCase):
    """
    Tests for insights.get_by_job_title().

    Covered cases:
    - No filters returns sorted job title breakdown with seniority averages.
    - Country, department, and job title filters narrow results.
    - Weighted average salary is computed across seniority levels.
    - Predictable DB query count.
    """

    TEST_CASES = [
        'No filters returns sorted job title breakdown with seniority averages.',
        'Country, department, and job title filters narrow results.',
        'Weighted average salary is computed across seniority levels.',
        'Predictable DB query count.',
    ]

    def test_getByJobTitle__no_filters__returns_sorted_breakdown(self):
        """No filters returns sorted job title breakdown with seniority averages."""
        EmployeeFactory.create(
            job_title='Software Engineer',
            seniority_level=SeniorityLevel.JUNIOR,
            salary=Decimal('50000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            job_title='Product Manager',
            seniority_level=SeniorityLevel.MID,
            salary=Decimal('90000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='pm.personal@example.com',
            company_email='pm@company.com',
        )

        result = insights.get_by_job_title()

        self.assertEqual([row['job_title'] for row in result], ['Product Manager', 'Software Engineer'])
        engineer = next(row for row in result if row['job_title'] == 'Software Engineer')
        self.assertEqual(engineer['headcount'], 1)
        self.assertEqual(engineer['seniority_breakdown'][SeniorityLevel.JUNIOR], 50000.0)

    def test_getByJobTitle__filters__narrow_results(self):
        """Country, department, and job title filters narrow results."""
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
            department='Sales',
            job_title='Account Executive',
            seniority_level=SeniorityLevel.MID,
            salary=Decimal('70000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='ae.personal@example.com',
            company_email='ae@company.com',
        )

        result = insights.get_by_job_title(
            countries=['India'],
            departments=['Engineering'],
            job_titles=['Software Engineer'],
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['job_title'], 'Software Engineer')

    def test_getByJobTitle__multiple_seniority_levels__weighted_average(self):
        """Weighted average salary is computed across seniority levels."""
        EmployeeFactory.create(
            job_title='Software Engineer',
            seniority_level=SeniorityLevel.JUNIOR,
            salary=Decimal('40000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            job_title='Software Engineer',
            seniority_level=SeniorityLevel.JUNIOR,
            salary=Decimal('40000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='se2.personal@example.com',
            company_email='se2@company.com',
        )
        EmployeeFactory.create(
            job_title='Software Engineer',
            seniority_level=SeniorityLevel.SENIOR,
            salary=Decimal('100000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='se3.personal@example.com',
            company_email='se3@company.com',
        )

        result = insights.get_by_job_title(job_titles=['Software Engineer'])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['headcount'], 3)
        self.assertEqual(result[0]['avg_salary'], 60000.0)

    def test_getByJobTitle__query_count__single_group_by(self):
        """Predictable DB query count."""
        EmployeeFactory.create(status=EmployeeStatus.ACTIVE)

        with self.assertNumQueries(expected_by_job_title_query_count()):
            insights.get_by_job_title()

    def test_getByJobTitle__zero_headcount_row__avg_salary_zero(self):
        """When headcount is zero, avg_salary is zero."""
        with patch.object(insights, 'active_employees') as mock_active:
            mock_qs = MagicMock()
            mock_active.return_value = mock_qs
            mock_qs.filter.return_value = mock_qs
            mock_qs.values.return_value.annotate.return_value.order_by.return_value = []
            with patch(
                'api.services.insights.defaultdict',
                return_value={
                    'Ghost Role': {
                        'headcount': 0,
                        'salaries_sum': 0.0,
                        'seniority_breakdown': {},
                    },
                },
            ):
                result = insights.get_by_job_title()

        self.assertEqual(result[0]['avg_salary'], 0)
        self.assertEqual(result[0]['headcount'], 0)


class GetPayEquityTests(TestCase):
    """
    Tests for insights.get_pay_equity().

    Covered cases:
    - Departments return per-gender averages and pay gap percentage.
    - Gap is zero when male average salary is zero.
    - Terminated employees are excluded.
    - Predictable DB query count.
    """

    TEST_CASES = [
        'Departments return per-gender averages and pay gap percentage.',
        'Gap is zero when male average salary is zero.',
        'Terminated employees are excluded.',
        'Predictable DB query count.',
    ]

    def test_getPayEquity__with_male_and_female__computes_gap(self):
        """Departments return per-gender averages and pay gap percentage."""
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
            personal_email='eng-female.personal@example.com',
            company_email='eng-female@company.com',
        )
        EmployeeFactory.create(
            department='Engineering',
            gender=Gender.NON_BINARY,
            salary=Decimal('85000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='eng-nb.personal@example.com',
            company_email='eng-nb@company.com',
        )
        EmployeeFactory.create(
            department='Engineering',
            gender=Gender.PREFER_NOT_TO_SAY,
            salary=Decimal('90000.00'),
            status=EmployeeStatus.ACTIVE,
            personal_email='eng-pnts.personal@example.com',
            company_email='eng-pnts@company.com',
        )

        result = insights.get_pay_equity()

        self.assertEqual(len(result), 1)
        row = result[0]
        self.assertEqual(row['department'], 'Engineering')
        self.assertEqual(row['male_avg'], 100000.0)
        self.assertEqual(row['female_avg'], 80000.0)
        self.assertEqual(row['non_binary_avg'], 85000.0)
        self.assertEqual(row['prefer_not_to_say_avg'], 90000.0)
        self.assertEqual(row['gap_percent'], 20.0)

    def test_getPayEquity__no_male_in_department__gap_is_zero(self):
        """Gap is zero when male average salary is zero."""
        EmployeeFactory.create(
            department='People',
            gender=Gender.FEMALE,
            salary=Decimal('70000.00'),
            status=EmployeeStatus.ACTIVE,
        )

        result = insights.get_pay_equity()

        self.assertEqual(result[0]['gap_percent'], 0.0)
        self.assertEqual(result[0]['male_avg'], 0.0)

    def test_getPayEquity__terminated_employees__excluded(self):
        """Terminated employees are excluded."""
        EmployeeFactory.create(
            department='Engineering',
            gender=Gender.MALE,
            salary=Decimal('100000.00'),
            status=EmployeeStatus.ACTIVE,
        )
        EmployeeFactory.create(
            department='Engineering',
            gender=Gender.FEMALE,
            salary=Decimal('50000.00'),
            status=EmployeeStatus.TERMINATED,
            personal_email='terminated-equity.personal@example.com',
            company_email='terminated-equity@company.com',
        )

        result = insights.get_pay_equity()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['male_avg'], 100000.0)
        self.assertEqual(result[0]['female_avg'], 0.0)
        self.assertEqual(result[0]['gap_percent'], 100.0)

    def test_getPayEquity__query_count__single_group_by(self):
        """Predictable DB query count."""
        EmployeeFactory.create(status=EmployeeStatus.ACTIVE)

        with self.assertNumQueries(expected_pay_equity_query_count()):
            insights.get_pay_equity()
