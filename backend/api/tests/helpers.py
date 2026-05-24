from django.urls import reverse

from api.models import HRUser


def auth_as_hr(client, email='hr@company.com', password='testpass123'):
    HRUser.objects.create_user(
        email=email,
        password=password,
        first_name='HR',
        last_name='User',
    )
    response = client.post(
        reverse('token_obtain_pair'),
        {'email': email, 'password': password},
        format='json',
    )
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')


class _AuthenticatedNonHRUser:
    """Minimal user object that passes authentication but fails IsHRUser."""

    is_authenticated = True
    is_active = True


def auth_as_non_hr(client):
    """Authenticate as a non-HR user (IsHRUser permission should deny access)."""
    client.force_authenticate(user=_AuthenticatedNonHRUser())


def auth_as_inactive_hr(client, email='inactive-hr@company.com', password='testpass123'):
    """Authenticate as a deactivated HR user (IsHRUser permission should deny access)."""
    user = HRUser.objects.create_user(
        email=email,
        password=password,
        first_name='Inactive',
        last_name='HR',
        is_active=False,
    )
    client.force_authenticate(user=user)
