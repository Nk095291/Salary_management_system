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


def _gender_bucket(gender: str) -> str:
    return gender if gender in (Gender.MALE, Gender.FEMALE) else 'Other'


def get_overview() -> dict:
    qs = active_employees()
    total = qs.count()
    if total == 0:
        return {
            'total_employees': 0,
            'avg_salary': 0,
            'highest_paid_country': None,
            'gender_distribution': {'Male': 0, 'Female': 0, 'Other': 0},
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
    gender_counts = {'Male': 0, 'Female': 0, 'Other': 0}
    for row in qs.values('gender').annotate(c=Count('id')):
        bucket = _gender_bucket(row['gender'])
        gender_counts[bucket] += row['c']

    gender_distribution = {
        key: round(gender_counts[key] / total * 100)
        for key in ('Male', 'Female', 'Other')
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


def get_by_job_title(country: str) -> list[dict]:
    qs = active_employees().filter(country=country)

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


def get_pay_equity() -> list[dict]:
    # Single query: group by department + gender together
    rows = (
        active_employees()
        .values('department', 'gender')
        .annotate(avg_salary=Avg('salary'))
        .order_by('department')
    )

    # Collapse in Python
    dept_map = defaultdict(lambda: {'male_avg': 0.0, 'female_avg': 0.0})
    for row in rows:
        dept = row['department']
        avg = _decimal(row['avg_salary'])
        if row['gender'] == Gender.MALE:
            dept_map[dept]['male_avg'] = avg
        elif row['gender'] == Gender.FEMALE:
            dept_map[dept]['female_avg'] = avg

    results = []
    for dept, vals in sorted(dept_map.items()):
        male_val, female_val = vals['male_avg'], vals['female_avg']
        gap = round((male_val - female_val) / male_val * 100, 1) if male_val > 0 else 0.0
        results.append({
            'department': dept,
            'male_avg': round(male_val, 2),
            'female_avg': round(female_val, 2),
            'gap_percent': gap,
        })
    return results