"""
API Schema Documentation for Documents App
===========================================

This module defines the API endpoints, request/response schemas,
and integration points for the Documents application.

Version: 1.0.0
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DocumentType(str, Enum):
    """Document type enumeration"""

    GOVT_ID = "GOVT_ID"
    PAYROLL = "PAYROLL"
    CREDIT_HISTORY = "CREDIT_HISTORY"
    ADDRESS_PROOF = "ADDRESS_PROOF"
    OTHER = "OTHER"


class DocumentStatus(str, Enum):
    """Document status enumeration"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class StorageMode(str, Enum):
    """Storage mode enumeration"""

    FILE_UPLOAD = "FILE_UPLOAD"
    EXTERNAL_LINK = "EXTERNAL_LINK"
    UNKNOWN = "UNKNOWN"


class VerificationMethod(str, Enum):
    """Verification method enumeration"""

    MANUAL_REVIEW = "MANUAL_REVIEW"
    AUTO_VERIFIED = "AUTO_VERIFIED"
    THIRD_PARTY = "THIRD_PARTY"
    OTHER = "OTHER"


class RejectionCategory(str, Enum):
    """Rejection category enumeration"""

    POOR_QUALITY = "POOR_QUALITY"
    INCOMPLETE = "INCOMPLETE"
    EXPIRED = "EXPIRED"
    WRONG_TYPE = "WRONG_TYPE"
    SUSPICIOUS = "SUSPICIOUS"
    NOT_VERIFIABLE = "NOT_VERIFIABLE"
    DUPLICATE = "DUPLICATE"
    OTHER = "OTHER"


class PriorityLevel(str, Enum):
    """Priority level enumeration"""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================


class DocumentSchema:
    """Base document schema for request/response"""

    class Request:
        """Document creation/update request schema"""

        id: Optional[uuid.UUID] = None
        document_type: DocumentType
        file: Optional[Any] = None  # File object
        link: Optional[str] = None
        display_filename: Optional[str] = None

        class Config:
            schema_extra = {
                "example": {
                    "document_type": "GOVT_ID",
                    "file": "file_object",  # For file uploads
                    "link": "https://example.com/document.pdf",  # For external links
                    "display_filename": "My Passport 2024.pdf",
                }
            }

    class Response:
        """Document response schema"""

        id: uuid.UUID
        requested_by: Optional[Dict]  # Staff object
        uploaded_by: Dict  # User object
        status: DocumentStatus
        status_display: str
        document_type: DocumentType
        document_type_display: str
        file_url: Optional[str]
        download_url: Optional[str]
        original_filename: str
        display_filename: str
        stored_filename: Optional[str]
        file_size: int
        file_extension: Optional[str]
        mime_type: str
        storage_mode: StorageMode
        is_file_upload: bool
        is_external_link: bool
        is_approved: bool
        is_rejected: bool
        is_pending: bool
        uploaded_at: datetime
        updated_at: datetime

        class Config:
            schema_extra = {
                "example": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "uploaded_by": {"id": "user-uuid", "username": "john_doe", "email": "john@example.com"},
                    "status": "PENDING",
                    "status_display": "Pending",
                    "document_type": "GOVT_ID",
                    "document_type_display": "Government Photo ID",
                    "file_url": "http://localhost:8000/media/documents/user_1/abc123_passport.pdf",
                    "original_filename": "passport.pdf",
                    "display_filename": "My Passport",
                    "file_size": 2048576,
                    "file_extension": ".pdf",
                    "mime_type": "application/pdf",
                    "storage_mode": "FILE_UPLOAD",
                    "is_file_upload": True,
                    "is_external_link": False,
                    "is_approved": False,
                    "is_rejected": False,
                    "is_pending": True,
                    "uploaded_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                }
            }


class DocumentUploadSchema:
    """Document upload request schema"""

    class Request:
        document_type: DocumentType
        file: Optional[Any] = None
        link: Optional[str] = None
        display_filename: Optional[str] = None

        class Config:
            schema_extra = {
                "example": {
                    "document_type": "GOVT_ID",
                    "file": "file_object",
                    "display_filename": "My Identity Document",
                }
            }


class DocumentApproveSchema:
    """Document approval request schema"""

    class Request:
        notes: Optional[str] = None
        verification_method: Optional[VerificationMethod] = VerificationMethod.MANUAL_REVIEW
        next_review_date: Optional[str] = None  # YYYY-MM-DD
        tags: Optional[List[str]] = None
        is_conditional: bool = False
        conditions: Optional[str] = None

        class Config:
            schema_extra = {
                "example": {
                    "notes": "Document verified manually",
                    "verification_method": "MANUAL_REVIEW",
                    "next_review_date": "2024-12-31",
                    "tags": ["verified", "high_priority"],
                    "is_conditional": False,
                }
            }


class DocumentRejectSchema:
    """Document rejection request schema"""

    class Request:
        reason: str
        category: Optional[RejectionCategory] = RejectionCategory.OTHER
        severity: Optional[str] = "MEDIUM"
        allow_resubmission: bool = True
        resubmission_deadline: Optional[str] = None  # YYYY-MM-DD
        suggested_corrections: Optional[List[str]] = None
        internal_notes: Optional[str] = None
        notify_user: bool = True
        escalation_required: bool = False
        escalation_reason: Optional[str] = None

        class Config:
            schema_extra = {
                "example": {
                    "reason": "Document is blurry and unreadable",
                    "category": "POOR_QUALITY",
                    "severity": "MEDIUM",
                    "allow_resubmission": True,
                    "resubmission_deadline": "2024-06-30",
                    "suggested_corrections": ["Upload clearer scan", "Ensure all edges visible"],
                    "notify_user": True,
                }
            }


class DocumentReviewSchema:
    """Generic document review request schema"""

    class Request:
        action: str  # "approve" or "reject"
        notes: Optional[str] = None

        class Config:
            schema_extra = {"example": {"action": "approve", "notes": "Document meets all requirements"}}


class DocumentRequestSchema:
    """Document request (staff to user) schema"""

    class Request:
        user_id: uuid.UUID
        document_type: DocumentType
        description: Optional[str] = None
        priority: Optional[PriorityLevel] = PriorityLevel.MEDIUM
        deadline: Optional[str] = None  # YYYY-MM-DD
        instructions: Optional[str] = None
        notify_user: bool = True
        allow_multiple_uploads: bool = False
        required_fields: Optional[List[str]] = None

        class Config:
            schema_extra = {
                "example": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "document_type": "GOVT_ID",
                    "description": "Please upload a government-issued ID",
                    "priority": "HIGH",
                    "deadline": "2024-02-01",
                    "notify_user": True,
                }
            }


class DocumentResetSchema:
    """Document reset request schema"""

    class Request:
        reason: str
        category: Optional[str] = "OTHER"
        notify_user: bool = True
        new_deadline: Optional[str] = None
        internal_notes: Optional[str] = None

        class Config:
            schema_extra = {
                "example": {
                    "reason": "Document expired, needs updated version",
                    "category": "DOCUMENT_EXPIRED",
                    "notify_user": True,
                    "new_deadline": "2024-07-15",
                }
            }


# ============================================================================
# API ENDPOINTS DOCUMENTATION
# ============================================================================


class DocumentEndpoints:
    """Document API endpoints documentation"""

    BASE_PATH = "/api/documents"

    class Endpoint:
        """Individual endpoint definition"""

        def __init__(
            self,
            method: str,
            path: str,
            description: str,
            auth_required: bool = True,
            staff_only: bool = False,
            request_schema: Optional[Any] = None,
            response_schema: Optional[Any] = None,
        ):
            self.method = method
            self.path = path
            self.full_path = f"{DocumentEndpoints.BASE_PATH}{path}"
            self.description = description
            self.auth_required = auth_required
            self.staff_only = staff_only
            self.request_schema = request_schema
            self.response_schema = response_schema

        def to_dict(self):
            """Convert to dictionary for documentation"""
            return {
                "method": self.method,
                "path": self.path,
                "full_path": self.full_path,
                "description": self.description,
                "auth_required": self.auth_required,
                "staff_only": self.staff_only,
                "request_schema": self.request_schema.__name__ if self.request_schema else None,
                "response_schema": self.response_schema.__name__ if self.response_schema else None,
            }

    # Define all endpoints
    ENDPOINTS = [
        # ==== CRUD Operations ====
        Endpoint(
            method="GET",
            path="/",
            description="List all documents (staff sees all, users see their own)",
            request_schema=None,
            response_schema=DocumentSchema.Response,
        ),
        Endpoint(
            method="POST",
            path="/",
            description="Create a new document",
            request_schema=DocumentSchema.Request,
            response_schema=DocumentSchema.Response,
        ),
        Endpoint(
            method="GET",
            path="/{id}/",
            description="Get document details",
            request_schema=None,
            response_schema=DocumentSchema.Response,
        ),
        Endpoint(
            method="PUT",
            path="/{id}/",
            description="Update document",
            request_schema=DocumentSchema.Request,
            response_schema=DocumentSchema.Response,
        ),
        Endpoint(
            method="DELETE", path="/{id}/", description="Delete document", request_schema=None, response_schema=None
        ),
        # ==== User Actions ====
        Endpoint(
            method="POST",
            path="/upload/",
            description="Upload document (file or link)",
            request_schema=DocumentUploadSchema.Request,
            response_schema=DocumentSchema.Response,
        ),
        Endpoint(
            method="GET",
            path="/{id}/download/",
            description="Download document file",
            request_schema=None,
            response_schema=None,  # Returns file or redirect
        ),
        Endpoint(
            method="GET",
            path="/{id}/preview/",
            description="Preview document inline",
            request_schema=None,
            response_schema=None,  # Returns file
        ),
        Endpoint(
            method="GET",
            path="/my-documents/",
            description="Get current user's documents",
            request_schema=None,
            response_schema=DocumentSchema.Response,
        ),
        Endpoint(
            method="GET",
            path="/pending/",
            description="Get pending documents",
            request_schema=None,
            response_schema=DocumentSchema.Response,
        ),
        Endpoint(
            method="GET",
            path="/approved/",
            description="Get approved documents",
            request_schema=None,
            response_schema=DocumentSchema.Response,
        ),
        Endpoint(
            method="GET",
            path="/by-type/",
            description="Get documents by type",
            request_schema=None,
            response_schema=DocumentSchema.Response,
        ),
        # ==== Staff Actions ====
        Endpoint(
            method="POST",
            path="/{id}/approve/",
            description="Approve document (staff only)",
            staff_only=True,
            request_schema=DocumentApproveSchema.Request,
            response_schema=None,  # Returns success message
        ),
        Endpoint(
            method="POST",
            path="/{id}/reject/",
            description="Reject document (staff only)",
            staff_only=True,
            request_schema=DocumentRejectSchema.Request,
            response_schema=None,  # Returns success message
        ),
        Endpoint(
            method="POST",
            path="/{id}/reset/",
            description="Reset document to pending (staff only)",
            staff_only=True,
            request_schema=DocumentResetSchema.Request,
            response_schema=None,  # Returns success message
        ),
        Endpoint(
            method="POST",
            path="/{id}/review/",
            description="Generic document review (staff only)",
            staff_only=True,
            request_schema=DocumentReviewSchema.Request,
            response_schema=None,  # Returns success message
        ),
        Endpoint(
            method="POST",
            path="/request_new/",
            description="Request new document from user (staff only)",
            staff_only=True,
            request_schema=DocumentRequestSchema.Request,
            response_schema=None,  # Returns success message
        ),
        # ==== Statistics ====
        Endpoint(
            method="GET",
            path="/stats/",
            description="Get document statistics",
            request_schema=None,
            response_schema=None,  # Returns stats object
        ),
        Endpoint(
            method="GET",
            path="/staff/dashboard/",
            description="Staff dashboard (staff only)",
            staff_only=True,
            request_schema=None,
            response_schema=None,  # Returns dashboard data
        ),
    ]

    @classmethod
    def get_endpoints(cls, user_type: str = "all") -> List[Dict]:
        """Get endpoints filtered by user type"""
        if user_type == "user":
            return [e.to_dict() for e in cls.ENDPOINTS if not e.staff_only]
        elif user_type == "staff":
            return [e.to_dict() for e in cls.ENDPOINTS]
        else:
            return [e.to_dict() for e in cls.ENDPOINTS]

    @classmethod
    def get_endpoint_by_path(cls, path: str, method: str = None) -> Optional[Dict]:
        """Get specific endpoint by path and method"""
        for endpoint in cls.ENDPOINTS:
            if endpoint.path == path and (method is None or endpoint.method == method):
                return endpoint.to_dict()
        return None


# ============================================================================
# INTEGRATION SCHEMAS (For other apps)
# ============================================================================


class UserIntegrationSchema:
    """Integration schema for User app"""

    class UserDocumentSummary:
        """Summary of user's documents for User app"""

        user_id: uuid.UUID
        total_documents: int
        pending_documents: int
        approved_documents: int
        rejected_documents: int
        has_required_documents: bool
        missing_document_types: List[DocumentType]

        class Config:
            schema_extra = {
                "example": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "total_documents": 5,
                    "pending_documents": 2,
                    "approved_documents": 3,
                    "rejected_documents": 0,
                    "has_required_documents": True,
                    "missing_document_types": ["CREDIT_HISTORY"],
                }
            }


class LoanIntegrationSchema:
    """Integration schema for Loan app"""

    class LoanDocumentRequirements:
        """Document requirements for a loan application"""

        loan_application_id: uuid.UUID
        required_documents: List[Dict[str, Any]]  # List of required document types
        provided_documents: List[uuid.UUID]  # List of document IDs
        is_complete: bool
        missing_documents: List[str]

        class Config:
            schema_extra = {
                "example": {
                    "loan_application_id": "loan-uuid-123",
                    "required_documents": [
                        {"type": "GOVT_ID", "name": "Government ID", "required": True},
                        {"type": "ADDRESS_PROOF", "name": "Proof of Address", "required": True},
                    ],
                    "provided_documents": ["doc-uuid-1", "doc-uuid-2"],
                    "is_complete": True,
                    "missing_documents": [],
                }
            }


# ============================================================================
# INTEGRATION FUNCTIONS (For other apps to use)
# ============================================================================


class DocumentIntegration:
    """Integration functions for other apps"""

    @staticmethod
    def get_user_documents_summary(user_id: uuid.UUID) -> Dict:
        """
        Get summary of user's documents for User app

        Args:
            user_id: UUID of the user

        Returns:
            Dictionary with user's document summary
        """
        # This would typically make a database query
        # For now, returns a schema example
        return UserIntegrationSchema.UserDocumentSummary.Config.schema_extra["example"]

    @staticmethod
    def check_loan_document_completeness(loan_application_id: uuid.UUID, user_id: uuid.UUID) -> Dict:
        """
        Check if all required documents are provided for a loan application

        Args:
            loan_application_id: UUID of the loan application
            user_id: UUID of the user

        Returns:
            Dictionary with completeness status
        """
        # This would check loan requirements against user's documents
        return LoanIntegrationSchema.LoanDocumentRequirements.Config.schema_extra["example"]

    @staticmethod
    def link_document_to_loan_application(document_id: uuid.UUID, loan_application_id: uuid.UUID) -> Dict:
        """
        Link a document to a loan application

        Args:
            document_id: UUID of the document
            loan_application_id: UUID of the loan application

        Returns:
            Dictionary with linking status
        """
        return {
            "status": "success",
            "message": f"Document {document_id} linked to loan application {loan_application_id}",
            "document_id": str(document_id),
            "loan_application_id": str(loan_application_id),
        }

    @staticmethod
    def get_required_documents_for_user(user_id: uuid.UUID, context: str = "loan") -> List[Dict]:
        """
        Get required documents for a user based on context

        Args:
            user_id: UUID of the user
            context: Context for document requirements ("loan", "kyc", etc.)

        Returns:
            List of required document types with status
        """
        base_requirements = [
            {
                "type": "GOVT_ID",
                "name": "Government ID",
                "description": "Government issued photo ID",
                "required": True,
                "has_document": False,
                "document_id": None,
                "status": None,
            },
            {
                "type": "ADDRESS_PROOF",
                "name": "Proof of Address",
                "description": "Utility bill or official document",
                "required": True,
                "has_document": False,
                "document_id": None,
                "status": None,
            },
        ]

        if context == "loan":
            base_requirements.append(
                {
                    "type": "PAYROLL",
                    "name": "Income Proof",
                    "description": "Pay slips or income documents",
                    "required": True,
                    "has_document": False,
                    "document_id": None,
                    "status": None,
                }
            )

        return base_requirements


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def generate_openapi_schema() -> Dict:
    """Generate OpenAPI schema for the documents API"""

    schemas = {
        "DocumentType": {"type": "string", "enum": [dt.value for dt in DocumentType]},
        "DocumentStatus": {"type": "string", "enum": [ds.value for ds in DocumentStatus]},
        "StorageMode": {"type": "string", "enum": [sm.value for sm in StorageMode]},
    }

    paths = {}
    for endpoint in DocumentEndpoints.ENDPOINTS:
        path_key = endpoint.path.replace("{id}", "{document_id}")

        paths[path_key] = {
            endpoint.method.lower(): {
                "summary": endpoint.description,
                "security": [{"BearerAuth": []}] if endpoint.auth_required else [],
                "parameters": []
                if "{id}" not in endpoint.path
                else [
                    {
                        "name": "document_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "format": "uuid"},
                    }
                ],
                "responses": {
                    "200": {"description": "Success"},
                    "401": {"description": "Unauthorized"},
                    "403": {"description": "Forbidden (staff only endpoint)"},
                },
            }
        }

    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Documents API",
            "version": "1.0.0",
            "description": "API for managing documents in Loan Management System",
        },
        "paths": paths,
        "components": {
            "schemas": schemas,
            "securitySchemes": {"BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}},
        },
    }


def print_api_documentation():
    """Print API documentation to console"""
    print("=" * 80)
    print("DOCUMENTS API DOCUMENTATION")
    print("=" * 80)
    print(f"\nBase URL: {DocumentEndpoints.BASE_PATH}")
    print("\nAvailable Endpoints:\n")

    for endpoint in DocumentEndpoints.ENDPOINTS:
        print(f"{endpoint.method:6} {endpoint.full_path}")
        print(f"       {endpoint.description}")
        if endpoint.staff_only:
            print("       [STAFF ONLY]")
        if endpoint.request_schema:
            print(f"       Request: {endpoint.request_schema}")
        if endpoint.response_schema:
            print(f"       Response: {endpoint.response_schema}")
        print()

    print("\nIntegration Functions:")
    print("-" * 40)
    print("1. DocumentIntegration.get_user_documents_summary(user_id)")
    print("2. DocumentIntegration.check_loan_document_completeness(loan_id, user_id)")
    print("3. DocumentIntegration.link_document_to_loan_application(doc_id, loan_id)")
    print("4. DocumentIntegration.get_required_documents_for_user(user_id, context)")
    print("=" * 80)


# ============================================================================
# MAIN (for testing/documentation)
# ============================================================================

if __name__ == "__main__":
    # Print documentation when run directly
    print_api_documentation()

    # Example usage
    print("\nExample: Get endpoints for regular users")
    print("-" * 40)
    user_endpoints = DocumentEndpoints.get_endpoints("user")
    for ep in user_endpoints[:3]:  # Show first 3
        print(f"{ep['method']} {ep['full_path']}")
