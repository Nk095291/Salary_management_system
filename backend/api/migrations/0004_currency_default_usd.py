"""
Set currency default to USD and normalise all existing rows to USD.

Multi-currency is not supported in this phase of the product. A TODO comment
in api/models.py and api/serializers.py marks where to re-introduce currency
selection when salary normalisation for cross-country comparisons is added.
"""
from django.db import migrations, models


def set_all_currency_to_usd(apps, schema_editor):
    Employee = apps.get_model('api', 'Employee')
    Employee.objects.exclude(currency='USD').update(currency='USD')


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0003_remove_on_leave_status'),
    ]

    operations = [
        migrations.RunPython(set_all_currency_to_usd, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='employee',
            name='currency',
            field=models.CharField(
                choices=[
                    ('USD', 'USD'),
                    ('INR', 'INR'),
                    ('GBP', 'GBP'),
                    ('EUR', 'EUR'),
                    ('AUD', 'AUD'),
                    ('CAD', 'CAD'),
                ],
                default='USD',
                max_length=3,
            ),
        ),
    ]
