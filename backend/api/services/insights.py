from collections import defaultdict
import statistics
from decimal import Decimal

from django.db.models import Avg, Count, Max, Min, Sum

from api.models import Employee, EmployeeStatus, Gender


def active_employees():
    return Employee.objects.filter(status=EmployeeStatus.ACTIVE)


def _decimal(value) -> float:
    return float(value) if value is not None else 0.0


def _median(values: list) -> float:
    return float(statistics.median(values)) if values else 0.0


GENDER_ORDER = (
    Gender.MALE,
    Gender.FEMALE,
    Gender.NON_BINARY,
    Gender.PREFER_NOT_TO_SAY,
)


def _empty_gender_distribution() -> dict[str, int]:
    return {gender: 0 for gender in GENDER_ORDER}


def get_overview() -> dict:
    qs = active_employees()
    total = qs.count()
    if total == 0:
        return {
            'total_employees': 0,
            'avg_salary': 0,
            'highest_paid_country': None,
            'gender_distribution': _empty_gender_distribution(),
        }

    # Single query for avg + gender breakdown
    agg = qs.aggregate(avg=Avg('salary'))
    avg_salary = _decimal(agg['avg'])

    # Single query for highest paid country
    highest = (
        qs.values('country')
        .annotate(avg_salary=Avg('salary'))
        .order_by('-avg_salary')
        .first()
    )
    highest_paid_country = highest['country'] if highest else None

    # Single query for gender distribution
    gender_counts = _empty_gender_distribution()
    for row in qs.values('gender').annotate(c=Count('id')):
        if row['gender'] in gender_counts:
            gender_counts[row['gender']] += row['c']

    gender_distribution = {
        gender: round(gender_counts[gender] / total * 100)
        for gender in GENDER_ORDER
    }
    remainder = 100 - sum(gender_distribution.values())
    if remainder:
        top_key = max(gender_distribution, key=gender_distribution.get)
        gender_distribution[top_key] += remainder

    return {
        'total_employees': total,
        'avg_salary': round(avg_salary, 2),
        'highest_paid_country': highest_paid_country,
        'gender_distribution': gender_distribution,
    }


def get_by_country() -> list[dict]:
    qs = active_employees()

    # Single GROUP BY query for all aggregates
    agg_rows = (
        qs.values('country')
        .annotate(
            headcount=Count('id'),
            min_salary=Min('salary'),
            max_salary=Max('salary'),
            avg_salary=Avg('salary'),
        )
        .order_by('country')
    )
    agg_by_country = {row['country']: row for row in agg_rows}

    # Single query for all salaries (for median), grouped in Python
    country_salaries = defaultdict(list)
    for row in qs.values('country', 'salary').order_by('country', 'salary'):
        country_salaries[row['country']].append(float(row['salary']))

    return [
        {
            'country': country,
            'headcount': agg['headcount'],
            'min_salary': round(_decimal(agg['min_salary']), 2),
            'max_salary': round(_decimal(agg['max_salary']), 2),
            'avg_salary': round(_decimal(agg['avg_salary']), 2),
            'median_salary': round(_median(country_salaries[country]), 2),
        }
        for country, agg in agg_by_country.items()
    ]


def get_by_department() -> list[dict]:
    rows = (
        active_employees()
        .values('department')
        .annotate(
            headcount=Count('id'),
            avg_salary=Avg('salary'),
            total_payroll=Sum('salary'),
        )
        .order_by('department')
    )
    return [
        {
            'department': row['department'],
            'headcount': row['headcount'],
            'avg_salary': round(_decimal(row['avg_salary']), 2),
            'total_payroll': round(_decimal(row['total_payroll']), 2),
        }
        for row in rows
    ]


def get_by_job_title(
    countries: list[str] | None = None,
    departments: list[str] | None = None,
    job_titles: list[str] | None = None,
) -> list[dict]:
    qs = active_employees()
    if countries:
        qs = qs.filter(country__in=countries)
    if departments:
        qs = qs.filter(department__in=departments)
    if job_titles:
        qs = qs.filter(job_title__in=job_titles)

    # Single query: group by job_title + seniority_level together
    rows = (
        qs.values('job_title', 'seniority_level')
        .annotate(
            avg_salary=Avg('salary'),
            headcount=Count('id'),
        )
        .order_by('job_title', 'seniority_level')
    )

    # Collapse into per-job-title structure in Python
    job_title_map = defaultdict(lambda: {'headcount': 0, 'salaries_sum': 0.0, 'seniority_breakdown': {}})
    for row in rows:
        jt = row['job_title']
        job_title_map[jt]['headcount'] += row['headcount']
        job_title_map[jt]['salaries_sum'] += _decimal(row['avg_salary']) * row['headcount']
        job_title_map[jt]['seniority_breakdown'][row['seniority_level']] = round(
            _decimal(row['avg_salary']), 2
        )

    return sorted(
        [
            {
                'job_title': jt,
                'avg_salary': round(data['salaries_sum'] / data['headcount'], 2) if data['headcount'] else 0,
                'headcount': data['headcount'],
                'seniority_breakdown': data['seniority_breakdown'],
            }
            for jt, data in job_title_map.items()
        ],
        key=lambda r: r['job_title'],
    )


def _empty_gender_averages() -> dict[str, float]:
    return {gender: 0.0 for gender in GENDER_ORDER}


def get_pay_equity() -> list[dict]:
    # Single query: group by department + gender together
    rows = (
        active_employees()
        .values('department', 'gender')
        .annotate(avg_salary=Avg('salary'))
        .order_by('department')
    )

    # Collapse in Python
    dept_map = defaultdict(_empty_gender_averages)

    for row in rows:
        dept = row['department']
        gender = row['gender']
        if gender in GENDER_ORDER:
            dept_map[dept][gender] = _decimal(row['avg_salary'])

    results = []
    for dept, vals in sorted(dept_map.items()):
        male_val, female_val = vals[Gender.MALE], vals[Gender.FEMALE]
        gap = round((male_val - female_val) / male_val * 100, 1) if male_val > 0 else 0.0
        results.append({
            'department': dept,
            'male_avg': round(vals[Gender.MALE], 2),
            'female_avg': round(vals[Gender.FEMALE], 2),
            'non_binary_avg': round(vals[Gender.NON_BINARY], 2),
            'prefer_not_to_say_avg': round(vals[Gender.PREFER_NOT_TO_SAY], 2),
            'gap_percent': gap,
        })
    return results
