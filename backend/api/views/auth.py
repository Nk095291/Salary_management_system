from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView

from api.serializers import EmailTokenObtainPairSerializer, HRUserSerializer


class TokenObtainPairView(BaseTokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = EmailTokenObtainPairSerializer


class TokenRefreshView(BaseTokenRefreshView):
    permission_classes = [AllowAny]


class MeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HRUserSerializer

    def get_object(self):
        return self.request.user
