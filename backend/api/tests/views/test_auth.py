from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.tests.factory.models.hr_user import HRUserFactory


class TokenObtainPairViewTests(APITestCase):
    """
    Tests for POST /api/auth/login/.

    Covered cases:
    - Valid credentials return access and refresh tokens.
    - Invalid password returns 401 unauthorized.
    """

    TEST_CASES = [
        'Valid credentials return access and refresh tokens.',
        'Invalid password returns 401 unauthorized.',
    ]

    def test_TokenObtainPairView__valid_credentials__returns_tokens(self):
        """Valid credentials return access and refresh tokens."""
        # GIVEN
        HRUserFactory.create(email='login@company.com', password='secret123')
        url = reverse('token_obtain_pair')

        # WHEN
        response = self.client.post(
            url,
            {'email': 'login@company.com', 'password': 'secret123'},
            format='json',
        )

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_TokenObtainPairView__invalid_password__returns_401(self):
        """Invalid password returns 401 unauthorized."""
        # GIVEN
        HRUserFactory.create(email='login@company.com', password='secret123')
        url = reverse('token_obtain_pair')

        # WHEN
        response = self.client.post(
            url,
            {'email': 'login@company.com', 'password': 'wrong'},
            format='json',
        )

        # THEN
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MeViewTests(APITestCase):
    """
    Tests for GET /api/auth/me/.

    Covered cases:
    - Authenticated request returns HR profile with nested employee.
    """

    TEST_CASES = [
        'Authenticated request returns HR profile with nested employee.',
    ]

    def test_MeView__authenticated_user__returns_profile_with_employee(self):
        """Authenticated request returns HR profile with nested employee."""
        # GIVEN
        user = HRUserFactory.create(email='me@company.com', password='secret123')
        login_response = self.client.post(
            reverse('token_obtain_pair'),
            {'email': 'me@company.com', 'password': 'secret123'},
            format='json',
        )
        access = login_response.data['access']

        # WHEN
        response = self.client.get(
            reverse('auth_me'),
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], user.email)
        self.assertIsNotNone(response.data['employee'])
        self.assertEqual(
            response.data['employee']['employee_id'],
            user.employee.employee_id,
        )
