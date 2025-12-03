# documents/api_schema.py
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .serializers import (
    DocumentApproveSerializer,
    DocumentRejectSerializer,
    DocumentSerializer,
    DocumentUploadSerializer,
)

# --- Parameters ---

# Filter parameters for list view
document_type_param = openapi.Parameter(
    "document_type",
    openapi.IN_QUERY,
    description="Filter by document type (GOVT_ID, PAYROLL, CREDIT_HISTORY)",
    type=openapi.TYPE_STRING,
)

status_param = openapi.Parameter(
    "status",
    openapi.IN_QUERY,
    description="Filter by status (PENDING, APPROVED, REJECTED)",
    type=openapi.TYPE_STRING,
)

uploaded_by_param = openapi.Parameter(
    "uploaded_by",
    openapi.IN_QUERY,
    description="Filter by uploader ID (Staff only)",
    type=openapi.TYPE_STRING,
)

# --- Schemas ---

# Upload schema
upload_schema = swagger_auto_schema(
    operation_description="Upload a new document (file or link). Optionally link to a loan application.",
    request_body=DocumentUploadSerializer,
    responses={
        201: DocumentSerializer,
        400: "Bad Request",
        401: "Unauthorized",
        404: "Loan Application Not Found",
    },
)

# List schema
list_schema = swagger_auto_schema(
    operation_description="List documents. Staff sees all, users see their own.",
    manual_parameters=[document_type_param, status_param, uploaded_by_param],
    responses={200: DocumentSerializer(many=True)},
)

# Reject schema
reject_schema = swagger_auto_schema(
    operation_description="Reject a document (Staff only). Sends email notification.",
    request_body=DocumentRejectSerializer,
    responses={
        200: openapi.Response(
            description="Document rejected successfully",
            examples={
                "application/json": {
                    "status": "Document rejected",
                    "document_id": "uuid",
                    "new_status": "REJECTED",
                    "rejection_note": "Reason...",
                    "user_notified": True,
                }
            },
        ),
        400: "Bad Request",
        403: "Permission Denied",
    },
)

# Approve schema
approve_schema = swagger_auto_schema(
    operation_description="Approve a document (Staff only). May trigger auto-submission of loan application.",
    request_body=DocumentApproveSerializer,
    responses={
        200: openapi.Response(
            description="Document approved successfully",
            examples={
                "application/json": {
                    "status": "Document approved successfully",
                    "document_id": "uuid",
                    "new_status": "APPROVED",
                }
            },
        ),
        400: "Bad Request",
        403: "Permission Denied",
    },
)
