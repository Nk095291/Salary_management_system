from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from api.models import Employee
from api.permissions import IsHRUser
from api.serializers import EmployeeSerializer


class EmployeePagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [IsHRUser]
    pagination_class = EmployeePagination
    lookup_field = 'pk'

    def get_queryset(self):
        queryset = Employee.objects.all().order_by('employee_id')
        department = self.request.query_params.get('department')
        country = self.request.query_params.get('country')
        status = self.request.query_params.get('status')
        if department:
            queryset = queryset.filter(department=department)
        if country:
            queryset = queryset.filter(country=country)
        if status:
            queryset = queryset.filter(status=status)
        return queryset
