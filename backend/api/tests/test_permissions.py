from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from rest_framework.views import APIView

from api.permissions import IsHRUser
from api.tests.factory.models.hr_user import HRUserFactory


class IsHRUserTests(TestCase):
    """
    Tests for IsHRUser permission.

    Covered cases:
    - Authenticated active HR user is granted permission.
    - Anonymous user is denied permission.
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsHRUser()
        self.view = APIView()

    def test_IsHRUser__authenticated_hr_user__returns_true(self):
        """Authenticated active HR user is granted permission."""
        # GIVEN
        user = HRUserFactory.create()
        request = self.factory.get('/')
        request.user = user

        # WHEN
        result = self.permission.has_permission(request, self.view)

        # THEN
        self.assertTrue(result)

    def test_IsHRUser__anonymous_user__returns_false(self):
        """Anonymous user is denied permission."""
        # GIVEN
        request = self.factory.get('/')
        request.user = AnonymousUser()

        # WHEN
        result = self.permission.has_permission(request, self.view)

        # THEN
        self.assertFalse(result)
