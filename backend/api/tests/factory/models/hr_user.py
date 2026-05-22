import factory
from factory import SubFactory

from api.models import HRUser
from api.tests.factory.models.employee import EmployeeFactory


class HRUserFactory(factory.django.DjangoModelFactory):
    email = factory.Sequence(lambda n: f'hr{n}@company.com')
    first_name = factory.LazyAttribute(lambda obj: obj.employee.first_name)
    last_name = factory.LazyAttribute(lambda obj: obj.employee.last_name)
    employee = SubFactory(
        EmployeeFactory,
        company_email=factory.SelfAttribute('..email'),
        personal_email=factory.LazyAttribute(
            lambda obj: f'{obj.company_email.split("@")[0]}.personal@example.com'
        ),
    )

    class Meta:
        model = HRUser

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', 'testpass123')
        return model_class.objects.create_user(*args, password=password, **kwargs)
