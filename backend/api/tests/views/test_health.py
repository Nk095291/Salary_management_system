from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.tests.helpers import auth_as_hr


def expected_health_query_count(*, authenticated: bool = False) -> int:
    """
    Expected DB queries for GET /api/health/ on SQLite.

    Unauthenticated health checks are static and issue no DB queries.
    When a Bearer token is supplied, JWT authentication performs one lookup.
    """
    return 1 if authenticated else 0


class HealthViewTests(APITestCase):
    """
    Tests for GET /api/health/.

    Covered cases:
    - Unauthenticated request returns ok status and message.
    - Authenticated request also returns ok status (AllowAny permission).
    - Unsupported HTTP methods return 405 method not allowed.
    - GET issues predictable DB query counts for unauthenticated and
      authenticated callers.
    """

    TEST_CASES = [
        'Unauthenticated request returns ok status and message.',
        'Authenticated request also returns ok status (AllowAny permission).',
        'Unsupported HTTP methods return 405 method not allowed.',
        'GET issues predictable DB query counts for unauthenticated and '
        'authenticated callers.',
    ]

    def test_health__unauthenticated_get__returns_ok_status(self):
        """Unauthenticated request returns ok status and message."""
        # GIVEN
        url = reverse('health')

        # WHEN
        response = self.client.get(url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['message'], 'Django API is running')

    def test_health__authenticated_get__returns_ok_status(self):
        """Authenticated request also returns ok status (AllowAny permission)."""
        # GIVEN
        auth_as_hr(self.client)
        url = reverse('health')

        # WHEN
        response = self.client.get(url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['message'], 'Django API is running')

    def test_health__post__returns_method_not_allowed(self):
        """Unsupported HTTP methods return 405 method not allowed."""
        # GIVEN
        url = reverse('health')

        # WHEN
        response = self.client.post(url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_health__query_count__unauthenticated_get(self):
        """Unauthenticated GET issues no DB queries."""
        # GIVEN
        url = reverse('health')

        # WHEN / THEN
        with self.assertNumQueries(expected_health_query_count(authenticated=False)):
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health__query_count__authenticated_get(self):
        """Authenticated GET only performs JWT auth lookup."""
        # GIVEN
        auth_as_hr(self.client)
        url = reverse('health')

        # WHEN / THEN
        with self.assertNumQueries(expected_health_query_count(authenticated=True)):
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
