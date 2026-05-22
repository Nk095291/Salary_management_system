from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.auth import MeView, TokenObtainPairView, TokenRefreshView
from .views.employees import EmployeeViewSet
from .views.health import health

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')

urlpatterns = [
    path('health/', health, name='health'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', MeView.as_view(), name='auth_me'),
    path('', include(router.urls)),
]
