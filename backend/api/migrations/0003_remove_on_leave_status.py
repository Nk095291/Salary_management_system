from django.db import migrations, models


def migrate_on_leave_to_active(apps, schema_editor):
    Employee = apps.get_model('api', 'Employee')
    Employee.objects.filter(status='On Leave').update(status='Active')


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_remove_employee_employee_id'),
    ]

    operations = [
        migrations.RunPython(migrate_on_leave_to_active, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='employee',
            name='status',
            field=models.CharField(
                choices=[('Active', 'Active'), ('Terminated', 'Terminated')],
                default='Active',
                max_length=20,
            ),
        ),
    ]
