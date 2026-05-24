from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from api.constants import COUNTRY_NAMES, DEPARTMENTS, JOB_TITLES_BY_DEPARTMENT
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
    http_method_names = ['get', 'post', 'head', 'options', 'patch', 'delete']

    def get_queryset(self):
        queryset = Employee.objects.all().order_by('id')
        departments = self.request.query_params.getlist('departments')
        countries = self.request.query_params.getlist('countries')
        status_param = self.request.query_params.get('status')
        if departments:
            queryset = queryset.filter(department__in=departments)
        if countries:
            queryset = queryset.filter(country__in=countries)
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    @action(detail=False, methods=['get'], url_path='departments')
    def departments(self, request):
        """Return departments with their allowed job titles."""
        return Response(
            [
                {
                    'name': department,
                    'job_titles': JOB_TITLES_BY_DEPARTMENT[department],
                }
                for department in DEPARTMENTS
            ]
        )

    @action(detail=False, methods=['get'], url_path='countries')
    def countries(self, request):
        """Return the canonical list of allowed countries."""
        return Response(COUNTRY_NAMES)
