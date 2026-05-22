from django.urls import path

from .views.auth import MeView, TokenObtainPairView, TokenRefreshView
from .views.health import health

urlpatterns = [
    path('health/', health, name='health'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', MeView.as_view(), name='auth_me'),
]
