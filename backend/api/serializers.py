from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from api.constants import COUNTRY_NAMES

from .models import Currency, Employee, HRUser


class EmployeeSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'job_title', 'department', 'country']


class EmployeeSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    # TODO: Multi-currency — when local-currency support is added, remove
    #       read_only and let the client supply a validated currency code.
    currency = serializers.CharField(read_only=True)

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

    def validate_country(self, value: str) -> str:
        if value not in COUNTRY_NAMES:
            raise serializers.ValidationError(
                f'"{value}" is not in the list of allowed countries. '
                f'Allowed: {", ".join(COUNTRY_NAMES)}'
            )
        return value

    def create(self, validated_data):
        validated_data.setdefault('currency', Currency.USD)
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
