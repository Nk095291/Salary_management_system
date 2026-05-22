from django.urls import reverse

from api.tests.factory.models.hr_user import HRUserFactory


def auth_as_hr(client, email='hr@company.com', password='testpass123'):
    HRUserFactory.create(email=email, password=password)
    response = client.post(
        reverse('token_obtain_pair'),
        {'email': email, 'password': password},
        format='json',
    )
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
