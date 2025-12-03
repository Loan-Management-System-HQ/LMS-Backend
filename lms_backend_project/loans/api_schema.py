# loans/api_schema.py
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .serializers import (
    DashboardStatsSerializer,
    LoanApplicationSerializer,
)

# --- Parameters ---

status_param = openapi.Parameter(
    "status",
    openapi.IN_QUERY,
    description="Filter by status (DRAFT, SUBMITTED, APPROVED, REJECTED)",
    type=openapi.TYPE_STRING,
)

# --- Schemas ---

# Application List/Create
application_list_schema = swagger_auto_schema(
    operation_description="List loan applications. Staff sees all, users see their own.",
    manual_parameters=[status_param],
    responses={200: LoanApplicationSerializer(many=True)},
)

application_create_schema = swagger_auto_schema(
    operation_description="Create a new loan application (DRAFT status).",
    request_body=LoanApplicationSerializer,
    responses={201: LoanApplicationSerializer},
)

# Submit Action
submit_schema = swagger_auto_schema(
    # otherwise draft if not all docs approved
    operation_description="Submit a loan application. Changes status to SUBMITTED if all docs approved",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={},  # No body required
    ),
    responses={
        200: openapi.Response(
            description="Application submitted or saved as draft",
            examples={
                "application/json": {
                    "status": "Application saved",
                    "message": "Your application is saved...",
                    "application_id": "uuid",
                    "new_status": "DRAFT",
                }
            },
        ),
        400: "Bad Request",
    },
)

# Approve Action
approve_schema = swagger_auto_schema(
    operation_description="Approve a loan application (Staff only). Creates a Loan record.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "notes": openapi.Schema(type=openapi.TYPE_STRING, description="Approval notes"),
        },
    ),
    responses={
        200: openapi.Response(
            description="Application approved",
            examples={
                "application/json": {
                    "status": "Application approved",
                    "loan_id": "uuid",
                }
            },
        ),
        403: "Permission Denied",
    },
)

# Reject Action
reject_schema = swagger_auto_schema(
    operation_description="Reject a loan application (Staff only).",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "reason": openapi.Schema(type=openapi.TYPE_STRING, description="Rejection reason"),
        },
        required=["reason"],
    ),
    responses={
        200: openapi.Response(
            description="Application rejected",
            examples={
                "application/json": {
                    "status": "Application rejected",
                    "new_status": "REJECTED",
                }
            },
        ),
        403: "Permission Denied",
    },
)

# Dashboard
dashboard_schema = swagger_auto_schema(
    operation_description="Get dashboard statistics and recent activity.",
    responses={200: DashboardStatsSerializer},
)
