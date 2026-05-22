from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Employee, HRUser


class EmployeeSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['employee_id', 'job_title', 'department', 'country']


class HRUserSerializer(serializers.ModelSerializer):
    employee = EmployeeSummarySerializer(read_only=True)

    class Meta:
        model = HRUser
        fields = ['id', 'email', 'first_name', 'last_name', 'employee']


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = HRUser.USERNAME_FIELD
