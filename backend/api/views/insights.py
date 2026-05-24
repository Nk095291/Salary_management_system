from rest_framework import status
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
        country = request.query_params.get('country', '').strip()
        if not country:
            return Response(
                {'country': ['This query parameter is required.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(insights.get_by_job_title(country))


class InsightsPayEquityView(APIView):
    permission_classes = [IsHRUser]

    def get(self, request):
        return Response(insights.get_pay_equity())
