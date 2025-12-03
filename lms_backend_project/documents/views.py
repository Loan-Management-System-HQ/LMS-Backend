from django.conf import settings
from django.core.mail import send_mail
from django.http import FileResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .api_schema import approve_schema, list_schema, reject_schema, upload_schema
from .models import Document

# Import all serializers
from .serializers import (
    DocumentApproveSerializer,
    DocumentRejectSerializer,
    DocumentRequestSerializer,
    DocumentResetSerializer,
    DocumentReviewSerializer,
    DocumentSerializer,
    DocumentStatsSerializer,
    DocumentUploadSerializer,
    StaffDocumentDashboardSerializer,
)


class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for Document model"""

    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["document_type", "status", "uploaded_by"]
    search_fields = ["original_filename", "display_filename", "link"]
    ordering_fields = ["uploaded_at", "updated_at", "file_name", "file_size"]

    @list_schema
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """Return documents based on user role"""
        # During schema generation (e.g. DRF/Swagger) a fake view instance may call
        # get_queryset without a real request/user. Short-circuit in that case to
        # avoid accessing request.user which can be an AnonymousUser and lead to
        # UUID validation errors when compared to UUID PKs.
        if getattr(self, "swagger_fake_view", False):
            return Document.objects.none()

        user = getattr(self.request, "user", None)

        # If no authenticated user, return empty queryset instead of attempting
        # to filter by AnonymousUser (which would trigger UUID coercion errors).
        if user is None or not getattr(user, "is_authenticated", False):
            return Document.objects.none()

        # Staff can see all documents
        if getattr(user, "is_staff", False):
            return Document.objects.all()

        # Regular users can only see their own documents
        return Document.objects.filter(uploaded_by=user)

    def get_serializer_context(self):
        """Add request context to serializer"""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        """Set uploaded_by to current user"""
        serializer.save(uploaded_by=self.request.user)

    # ==== User Actions ====#
    @upload_schema
    @action(detail=False, methods=["post"])
    def upload(self, request):
        """Upload a new document (file or link)"""
        # Strictly enforce authentication to prevent AnonymousUser errors with UUID fields
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = DocumentUploadSerializer(data=request.data)

        if serializer.is_valid():
            # Prepare document data
            document_data = {
                "uploaded_by": request.user,
                "document_type": serializer.validated_data["document_type"],
            }

            # Handle file upload
            if "file" in serializer.validated_data and serializer.validated_data["file"]:
                document_data["file"] = serializer.validated_data["file"]

            # Handle external link
            elif "link" in serializer.validated_data and serializer.validated_data["link"]:
                document_data["link"] = serializer.validated_data["link"]

            # Handle loan application linking
            loan_app = None
            if "loan_application_id" in serializer.validated_data and serializer.validated_data["loan_application_id"]:
                try:
                    from loans.models import LoanApplication

                    loan_app_id = serializer.validated_data["loan_application_id"]
                    loan_app = LoanApplication.objects.get(id=loan_app_id)
                    document_data["loan_application"] = loan_app
                except LoanApplication.DoesNotExist:
                    return Response(
                        {"error": f"Loan application with ID {loan_app_id} not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            # Set display filename if provided
            if "display_filename" in serializer.validated_data:
                document_data["display_filename"] = serializer.validated_data["display_filename"]

            # Create document
            document = Document.objects.create(**document_data)

            # Auto-link to loan application documents if loan_app exists
            if loan_app:
                try:
                    from loans.models import LoanApplicationDocument

                    LoanApplicationDocument.objects.create(loan_application=loan_app, document=document)
                except Exception as e:
                    # Document created but linking failed - log but don't fail
                    print(f"Failed to link document to application: {str(e)}")

            # Return created document
            doc_serializer = DocumentSerializer(document, context={"request": request})

            return Response(doc_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """Download document file (user and staff)"""
        document = self.get_object()

        # Check permissions
        if not request.user.is_staff and document.uploaded_by != request.user:
            return Response(
                {"error": "You do not have permission to download this document"}, status=status.HTTP_403_FORBIDDEN
            )

        # Handle file download
        if document.file:
            try:
                response = FileResponse(document.file.open(), as_attachment=True)
                response["Content-Disposition"] = f'attachment; filename="{document.original_filename}"'
                response["Content-Type"] = document.mime_type
                response["Content-Length"] = document.file_size
                return response
            except Exception as e:
                return Response({"error": f"Cannot open file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Handle external link
        elif document.link:
            return Response(
                {
                    "url": document.link,
                    "filename": document.original_filename,
                    "message": "Document is available at the external link above",
                }
            )

        return Response({"error": "No file or link available for this document"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        """Preview document (inline view)"""
        document = self.get_object()

        # Check permissions
        if not request.user.is_staff and document.uploaded_by != request.user:
            return Response(
                {"error": "You do not have permission to view this document"}, status=status.HTTP_403_FORBIDDEN
            )

        if document.file:
            try:
                # For PDFs and images, serve inline
                if document.mime_type in ["application/pdf", "image/jpeg", "image/png"]:
                    response = FileResponse(document.file.open())
                    response["Content-Type"] = document.mime_type
                    response["Content-Disposition"] = f'inline; filename="{document.original_filename}"'
                    return response
                else:
                    # For other types, force download
                    response = FileResponse(document.file.open(), as_attachment=True)
                    response["Content-Disposition"] = f'attachment; filename="{document.original_filename}"'
                    response["Content-Type"] = document.mime_type
                    return response
            except Exception as e:
                return Response({"error": f"Cannot open file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif document.link:
            return Response({"url": document.link, "message": "Document is available at the external link above"})

        return Response({"error": "No file or link available for preview"}, status=status.HTTP_404_NOT_FOUND)

    # ==== Staff Actions ====# [approve, reject, reset, review, request_new]
    @approve_schema
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a document (staff only) - uses detailed DocumentApproveSerializer"""
        document = self.get_object()
        serializer = DocumentApproveSerializer(data=request.data, context={"request": request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if document.status == "APPROVED":
            return Response({"error": "Document is already approved"}, status=status.HTTP_400_BAD_REQUEST)

        # Update document with approval data
        document.status = "APPROVED"

        # maybe in the future we want to add these fields to Document model:
        # document.approval_notes = serializer.validated_data.get('notes', '')
        # document.verification_method = serializer.validated_data.get('verification_method', 'MANUAL_REVIEW')
        # document.next_review_date = serializer.validated_data.get('next_review_date')
        # document.tags = ','.join(serializer.validated_data.get('tags', []))

        if hasattr(request.user, "staff"):
            document.requested_by = request.user.staff

        document.save()

        # Document approval no longer auto-submits loan applications in the new flow.
        # Keep the approve action focused on marking the document as APPROVED.

        # Return detailed response
        response_data = {
            "status": "Document approved successfully",
            "document_id": str(document.id),
            "new_status": document.status,
            "approved_by": request.user.username if request.user else "Unknown",
            "approved_at": document.updated_at.isoformat(),
            "approval_details": serializer.validated_data,
            "message": f'Document "{document.original_filename}" has been approved.',
        }

        return Response(response_data, status=status.HTTP_200_OK)

    # reject
    @reject_schema
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        """Reject a document (staff only) - stores note and sends email"""
        document = self.get_object()
        serializer = DocumentRejectSerializer(data=request.data, context={"request": request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if document.status == "REJECTED":
            return Response({"error": "Document is already rejected"}, status=status.HTTP_400_BAD_REQUEST)

        # Update document status and store rejection note
        document.status = "REJECTED"
        document.rejection_note = serializer.validated_data["reason"]

        if hasattr(request.user, "staff"):
            document.requested_by = request.user.staff

        document.save()

        # Send email to user if requested
        if serializer.validated_data.get("notify_user", True) and document.uploaded_by:
            try:
                user = document.uploaded_by
                loan_app_info = ""
                if document.loan_application:
                    loan_app_info = f"\n\nRelated Loan Application ID: {document.loan_application.id}"

                subject = "Document Rejected - Action Required"
                message = (
                    f"Hello {user.name},\n\n"
                    f"Your {document.get_document_type_display()} was rejected by our staff.\n\n"
                    f"Staff Note: {document.rejection_note}\n"
                    f"{loan_app_info}\n\n"
                    "Please log in to your account and re-upload a corrected version of this document.\n\n"
                    "Regards,\n"
                    "Fast Funding LMS Team"
                )
                from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@fastfunding-lms.com")

                send_mail(subject, message, from_email, [user.email], fail_silently=True)
            except Exception as e:
                # Don't let email failures block the rejection
                print(f"Failed to send rejection email: {str(e)}")

        response_data = {
            "status": "Document rejected",
            "document_id": str(document.id),
            "new_status": document.status,
            "rejected_by": request.user.username if request.user else "Unknown",
            "rejected_at": document.updated_at.isoformat(),
            "rejection_note": document.rejection_note,
            "user_notified": serializer.validated_data.get("notify_user", True),
            "message": f'Document "{document.original_filename}" has been rejected.',
        }

        return Response(response_data, status=status.HTTP_200_OK)

    # reset
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def reset(self, request, pk=None):
        """Reset document to pending (staff only) - uses DocumentResetSerializer"""
        document = self.get_object()
        serializer = DocumentResetSerializer(data=request.data, context={"request": request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        document.status = "PENDING"

        # Store reset details
        # document.reset_reason = serializer.validated_data.get('reason', '')
        # document.reset_category = serializer.validated_data.get('category', 'OTHER')

        document.save()

        return Response(
            {
                "status": "Document reset to pending",
                "document_id": str(document.id),
                "new_status": document.status,
                "reset_details": serializer.validated_data,
                "message": f'Document "{document.original_filename}" has been reset to pending status.',
            }
        )

    # review
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def review(self, request, pk=None):
        """Generic document review (staff only) - uses DocumentReviewSerializer"""
        document = self.get_object()
        serializer = DocumentReviewSerializer(data=request.data, context={"request": request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action = serializer.validated_data["action"]
        notes = serializer.validated_data.get("notes", "")

        if action == "approve":
            # Use the detailed approve serializer for additional data if provided
            approve_data = {"notes": notes}
            if "verification_method" in request.data:
                approve_data["verification_method"] = request.data["verification_method"]

            approve_serializer = DocumentApproveSerializer(data=approve_data, context={"request": request})
            if approve_serializer.is_valid():
                document.status = "APPROVED"
                # document.approval_notes = notes
        else:  # reject
            # Use the detailed reject serializer for additional data if provided
            reject_data = {"reason": notes}
            if "category" in request.data:
                reject_data["category"] = request.data["category"]

            reject_serializer = DocumentRejectSerializer(data=reject_data, context={"request": request})
            if reject_serializer.is_valid():
                document.status = "REJECTED"
                # document.rejection_reason = notes

        if hasattr(request.user, "staff"):
            document.requested_by = request.user.staff

        document.save()

        return Response(
            {
                "action": action,
                "status": "Document {}d successfully".format(action),
                "document_id": str(document.id),
                "new_status": document.status,
                "notes": notes,
                "reviewed_by": request.user.username if request.user else "Unknown",
                "reviewed_at": document.updated_at.isoformat(),
                "message": f'Document "{document.original_filename}" has been {action}d.',
            }
        )

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def request_new(self, request):
        """Request a new document from user (staff only)"""
        serializer = DocumentRequestSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]

            # Create document request
            document = Document.objects.create(
                uploaded_by=user,
                requested_by=request.user.staff if hasattr(request.user, "staff") else None,
                document_type=serializer.validated_data["document_type"],
                file_name=f"Requested {serializer.validated_data['document_type']}",
                original_filename=f"Requested {serializer.validated_data['document_type']}",
                display_filename=f"Requested {serializer.validated_data['document_type']}",
                link="",
                status="PENDING",
            )

            return Response(
                {
                    "status": "Document request created",
                    "document_id": str(document.id),
                    "user_id": str(user.id),
                    "document_type": document.document_type,
                    "priority": serializer.validated_data.get("priority", "MEDIUM"),
                    "deadline": serializer.validated_data.get("deadline"),
                    "message": f"Document request created for user {user.username}",
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ==== Additional Utility Actions ====#
    @action(detail=False, methods=["get"])
    def my_documents(self, request):
        """Get current user's documents"""
        # During schema generation or when unauthenticated, avoid filtering by
        # AnonymousUser which will trigger UUID validation errors on FK fields.
        if getattr(self, "swagger_fake_view", False):
            return Response([])

        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return Response([])

        documents = Document.objects.filter(uploaded_by=user)
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        """Get pending documents (staff sees all, users see their own)"""
        if getattr(self, "swagger_fake_view", False):
            return Response([])

        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return Response([])

        if getattr(user, "is_staff", False):
            documents = Document.objects.filter(status="PENDING")
        else:
            documents = Document.objects.filter(uploaded_by=user, status="PENDING")

        serializer = self.get_serializer(documents.order_by("-uploaded_at"), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def approved(self, request):
        """Get approved documents"""
        if getattr(self, "swagger_fake_view", False):
            return Response([])

        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return Response([])

        if getattr(user, "is_staff", False):
            documents = Document.objects.filter(status="APPROVED")
        else:
            documents = Document.objects.filter(uploaded_by=user, status="APPROVED")

        serializer = self.get_serializer(documents.order_by("-updated_at"), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_type(self, request):
        """Get documents grouped by type"""
        document_type = request.query_params.get("type", None)
        if getattr(self, "swagger_fake_view", False):
            return Response([])

        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return Response([])

        if document_type:
            if getattr(user, "is_staff", False):
                documents = Document.objects.filter(document_type=document_type)
            else:
                documents = Document.objects.filter(uploaded_by=user, document_type=document_type)
        else:
            # Return all documents grouped by type
            if getattr(user, "is_staff", False):
                documents = Document.objects.all()
            else:
                documents = Document.objects.filter(uploaded_by=user)

        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)


class DocumentStatsView(generics.GenericAPIView):
    """View for document statistics"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DocumentStatsSerializer

    def get(self, request):
        # Protect stats view from schema generation or AnonymousUser during
        # documentation builds which may call this without a real user.
        if getattr(self, "swagger_fake_view", False):
            return Response({})

        user = getattr(request, "user", None)

        if user is None or not getattr(user, "is_authenticated", False):
            return Response({})

        if getattr(user, "is_staff", False):
            # Admin stats
            total_docs = Document.objects.count()
            pending_docs = Document.objects.filter(status="PENDING").count()
            approved_docs = Document.objects.filter(status="APPROVED").count()
            rejected_docs = Document.objects.filter(status="REJECTED").count()

            # Group by document type
            by_type = {}
            for doc_type, display_name in Document.DOCUMENT_TYPES:
                count = Document.objects.filter(document_type=doc_type).count()
                by_type[doc_type] = {
                    "name": display_name,
                    "count": count,
                    "pending": Document.objects.filter(document_type=doc_type, status="PENDING").count(),
                    "approved": Document.objects.filter(document_type=doc_type, status="APPROVED").count(),
                }

            stats = {
                "total_documents": total_docs,
                "pending": pending_docs,
                "approved": approved_docs,
                "rejected": rejected_docs,
                "by_document_type": by_type,
                "user_type": "staff",
            }
        else:
            # User stats
            user_docs = Document.objects.filter(uploaded_by=user)

            stats = {
                "total_documents": user_docs.count(),
                "pending": user_docs.filter(status="PENDING").count(),
                "approved": user_docs.filter(status="APPROVED").count(),
                "rejected": user_docs.filter(status="REJECTED").count(),
                "user_type": "user",
            }

        return Response(stats)


# Staff-specific views
class StaffDocumentDashboardView(generics.GenericAPIView):
    """Staff dashboard for document management"""

    permission_classes = [permissions.IsAdminUser]
    serializer_class = StaffDocumentDashboardSerializer

    def get(self, request):
        """Get comprehensive dashboard data for staff"""

        # Recent activity
        recent_documents = Document.objects.order_by("-uploaded_at")[:10]
        recent_serializer = DocumentSerializer(recent_documents, many=True, context={"request": request})

        # Urgent pending (more than 7 days old)
        week_ago = timezone.now() - timezone.timedelta(days=7)
        urgent_pending = Document.objects.filter(status="PENDING", uploaded_at__lt=week_ago).count()

        return Response(
            {
                "recent_activity": recent_serializer.data,
                "urgent_pending": urgent_pending,
                "dashboard_actions": {
                    "approve": "/api/documents/{id}/approve/",
                    "reject": "/api/documents/{id}/reject/",
                    "review": "/api/documents/{id}/review/",
                    "reset": "/api/documents/{id}/reset/",
                    "request_new": "/api/documents/request_new/",
                    "pending_documents": "/api/documents/pending/",
                },
            }
        )
