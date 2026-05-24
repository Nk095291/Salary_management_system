from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.auth import MeView, TokenObtainPairView, TokenRefreshView
from .views.employees import EmployeeViewSet
from .views.health import health
from .views.insights import (
    InsightsByCountryView,
    InsightsByDepartmentView,
    InsightsByJobTitleView,
    InsightsOverviewView,
    InsightsPayEquityView,
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')

urlpatterns = [
    path('health/', health, name='health'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', MeView.as_view(), name='auth_me'),
    path('insights/overview/', InsightsOverviewView.as_view(), name='insights-overview'),
    path('insights/by-country/', InsightsByCountryView.as_view(), name='insights-by-country'),
    path(
        'insights/by-department/',
        InsightsByDepartmentView.as_view(),
        name='insights-by-department',
    ),
    path(
        'insights/by-job-title/',
        InsightsByJobTitleView.as_view(),
        name='insights-by-job-title',
    ),
    path(
        'insights/pay-equity/',
        InsightsPayEquityView.as_view(),
        name='insights-pay-equity',
    ),
    path('', include(router.urls)),
]
