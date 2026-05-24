from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Employee, HRUser


class EmployeeSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'job_title', 'department', 'country']


class EmployeeSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id',
            'first_name',
            'last_name',
            'personal_email',
            'company_email',
            'gender',
            'date_of_birth',
            'department',
            'job_title',
            'seniority_level',
            'employment_type',
            'country',
            'salary',
            'currency',
            'date_joining',
            'date_relieving',
            'status',
            'created_at',
            'updated_at',
        ]

    def create(self, validated_data):
        employee = Employee(**validated_data)
        employee.save()
        return employee

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class HRUserSerializer(serializers.ModelSerializer):
    employee = EmployeeSummarySerializer(read_only=True)

    class Meta:
        model = HRUser
        fields = ['id', 'email', 'first_name', 'last_name', 'employee']


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = HRUser.USERNAME_FIELD
