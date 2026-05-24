"""
Centralised constants shared across the api app.

DEPARTMENTS and COUNTRIES are the single source of truth for allowed values.
The /employees/departments/ and /employees/countries/ endpoints return these values. 


TODO : Right now we are handling this using constants. In future we can use a DB table to store the values.
"""

DEPARTMENTS = [
    'Engineering',
    'Finance',
    'Human Resources',
    'Legal',
    'Marketing',
    'Operations',
    'Sales',
    'Support',
]

# Each entry: (country_name, salary_min_usd, salary_max_usd)
# Salary ranges are stored in USD for now since the system is single-currency.
# TODO: When multi-currency support is added, restore per-country currency
#       mappings here and update the insights aggregation to convert to a
#       base currency before comparison.
COUNTRIES = [
    ('Australia', 50_000, 130_000),
    ('Canada', 45_000, 120_000),
    ('Germany', 35_000, 110_000),
    ('India', 10_000, 60_000),
    ('United Kingdom', 28_000, 95_000),
    ('United States', 40_000, 180_000),
]

COUNTRY_NAMES: list[str] = [c[0] for c in COUNTRIES]

JOB_TITLES_BY_DEPARTMENT: dict[str, list[str]] = {
    'Engineering': [
        'Software Engineer',
        'Senior Software Engineer',
        'QA Engineer',
        'DevOps Engineer',
        'Engineering Manager',
    ],
    'Finance': ['Financial Analyst', 'Accountant', 'Finance Manager'],
    'Human Resources': ['HR Manager', 'HR Specialist', 'Recruiter'],
    'Legal': ['Legal Counsel', 'Compliance Officer'],
    'Marketing': ['Marketing Specialist', 'Content Strategist', 'Marketing Manager'],
    'Operations': ['Operations Analyst', 'Operations Manager', 'Project Coordinator'],
    'Sales': [
        'Account Executive',
        'Sales Representative',
        'Sales Manager',
        'Business Development Manager',
    ],
    'Support': ['Support Specialist', 'Customer Success Manager'],
}
