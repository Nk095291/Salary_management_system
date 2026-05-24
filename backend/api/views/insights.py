from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsHRUser
from api.services import insights


class InsightsOverviewView(APIView):
    permission_classes = [IsHRUser]

    def get(self, request):
        return Response(insights.get_overview())


class InsightsByCountryView(APIView):
    permission_classes = [IsHRUser]

    def get(self, request):
        return Response(insights.get_by_country())


class InsightsByDepartmentView(APIView):
    permission_classes = [IsHRUser]

    def get(self, request):
        return Response(insights.get_by_department())


class InsightsByJobTitleView(APIView):
    permission_classes = [IsHRUser]

    def get(self, request):
        countries = [
            value.strip()
            for value in request.query_params.getlist('countries')
            if value.strip()
        ]
        departments = [
            value.strip()
            for value in request.query_params.getlist('departments')
            if value.strip()
        ]
        job_titles = [
            value.strip()
            for value in request.query_params.getlist('job_titles')
            if value.strip()
        ]
        return Response(
            insights.get_by_job_title(countries, departments, job_titles),
        )


class InsightsPayEquityView(APIView):
    permission_classes = [IsHRUser]

    def get(self, request):
        return Response(insights.get_pay_equity())
