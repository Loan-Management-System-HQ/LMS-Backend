from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .api_schema import (
    dashboard_schema,
)
from .models import CustomerLoan, Installment, Loan, LoanApplication, LoanApplicationDocument, UserLoanApplication
from .serializers import (
    DashboardStatsSerializer,
    InstallmentSerializer,
    LoanApplicationSerializer,
    LoanCalculatorSerializer,
    LoanSerializer,
    PaymentSerializer,
)


class LoanApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for LoanApplication"""

    serializer_class = LoanApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "is_approved"]
    search_fields = ["id", "amount"]
    ordering_fields = ["created_at", "amount", "duration"]

    def get_queryset(self):
        """Return loan applications for the current user"""
        # Short-circuit during schema generation / swagger fake view
        if getattr(self, "swagger_fake_view", False):
            return LoanApplication.objects.none()

        user = getattr(self.request, "user", None)

        # If no authenticated user, return empty queryset to avoid filtering by AnonymousUser
        if user is None or not getattr(user, "is_authenticated", False):
            return LoanApplication.objects.none()

        # Staff can see all applications
        if getattr(user, "is_staff", False):
            return LoanApplication.objects.all()

        # Customers can only see their applications
        user_app_ids = UserLoanApplication.objects.filter(user=user).values_list("loan_application_id", flat=True)

        return LoanApplication.objects.filter(id__in=user_app_ids)

    def perform_create(self, serializer):
        """Create loan application and link it to the current user"""
        loan_application = serializer.save()

        # Link the current user to this application
        UserLoanApplication.objects.create(user=self.request.user, loan_application=loan_application)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Submit a draft loan application"""
        loan_application = self.get_object()

        if loan_application.status != "DRAFT":
            return Response({"error": "Application has already been submitted"}, status=status.HTTP_400_BAD_REQUEST)

        # Enforce mandatory documents before allowing submission
        required_types = {"GOVT_ID", "PAYROLL", "CREDIT_HISTORY"}
        # Only consider documents that have been APPROVED
        attached_types = set(
            LoanApplicationDocument.objects.filter(
                loan_application=loan_application, document__status="APPROVED"
            ).values_list("document__document_type", flat=True)
        )

        missing = required_types - attached_types
        if missing:
            return Response(
                {
                    "error": "Missing mandatory documents for submission",
                    "missing_document_types": list(missing),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        loan_application.status = "SUBMITTED"
        loan_application.save()

        return Response({"status": "Application submitted successfully", "application_id": str(loan_application.id)})

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a loan application (staff only)"""
        loan_application = self.get_object()

        if loan_application.status != "UNDER_REVIEW":
            return Response(
                {"error": "Application must be under review to approve"}, status=status.HTTP_400_BAD_REQUEST
            )

        loan_application.status = "APPROVED"
        loan_application.is_approved = True
        loan_application.save()

        # TODO: Create a Loan record from the approved application

        return Response({"status": "Application approved successfully", "application_id": str(loan_application.id)})

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        """Reject a loan application (staff only)"""
        loan_application = self.get_object()

        if loan_application.status != "UNDER_REVIEW":
            return Response({"error": "Application must be under review to reject"}, status=status.HTTP_400_BAD_REQUEST)

        loan_application.status = "REJECTED"
        loan_application.save()

        return Response({"status": "Application rejected", "application_id": str(loan_application.id)})

    @action(detail=True, methods=["post"])
    def add_document(self, request, pk=None):
        """Add a document to the loan application"""
        loan_application = self.get_object()
        document_id = request.data.get("document_id")

        if not document_id:
            return Response({"error": "document_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if document exists and belongs to user
        from documents.models import Document

        # Protect against AnonymousUser during schema generation or unauthenticated calls
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return Response(
                {"error": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Document model uses `uploaded_by` to reference the user
            document = Document.objects.get(id=document_id, uploaded_by=user)
        except Document.DoesNotExist:
            return Response(
                {
                    "error": "Document not found or does not belong to user",
                    "suggestion": "Upload the document first via the upload documents portal",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create relationship
        LoanApplicationDocument.objects.get_or_create(loan_application=loan_application, document=document)

        return Response(
            {
                "status": "Document added to application",
                "application_id": str(loan_application.id),
                "document_id": str(document.id),
            }
        )


class LoanViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Loan (read-only for customers)"""

    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["status"]
    search_fields = ["id", "amount"]

    def get_queryset(self):
        """Return loans for the current user"""
        # Short-circuit for schema generation / fake view
        if getattr(self, "swagger_fake_view", False):
            return Loan.objects.none()

        user = getattr(self.request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return Loan.objects.none()

        # Staff can see all loans
        if getattr(user, "is_staff", False):
            return Loan.objects.all()

        # Customers can only see their loans
        if hasattr(user, "customer"):
            customer_loan_ids = CustomerLoan.objects.filter(customer=user.customer).values_list("loan_id", flat=True)

            return Loan.objects.filter(id__in=customer_loan_ids)

        return Loan.objects.none()

    @action(detail=True, methods=["get"])
    def installments(self, request, pk=None):
        """Get installments for a specific loan"""
        loan = self.get_object()
        installments = loan.installments.all()
        serializer = InstallmentSerializer(installments, many=True)
        return Response(serializer.data)


class InstallmentViewSet(viewsets.ReadOnlyModelViewSet):
    """ReadOnly ViewSet for Installments"""

    queryset = Installment.objects.all()
    serializer_class = InstallmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Short-circuit for schema generation and unauthenticated users
        if getattr(self, "swagger_fake_view", False):
            return Installment.objects.none()

        user = getattr(self.request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return Installment.objects.none()

        if getattr(user, "is_staff", False):
            return Installment.objects.all()
        return Installment.objects.filter(loan__borrowers__user=user)


class PaymentView(generics.GenericAPIView):
    """Mock payment view"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def post(self, request, pk=None):
        return Response({"status": "Payment processed (mock)"})


class LoanCalculatorView(generics.GenericAPIView):
    """Loan calculator view"""

    permission_classes = [permissions.AllowAny]
    serializer_class = LoanCalculatorSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Implement calculation logic here
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DashboardView(generics.GenericAPIView):
    """
    Dashboard view for both staff and customers.
    Returns statistics and recent activity.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DashboardStatsSerializer

    @dashboard_schema
    def get(self, request, *args, **kwargs):
        user = request.user

        if user.is_staff:
            # Admin stats
            data = {
                "total_loans": Loan.objects.count(),
                "pending_loans": LoanApplication.objects.filter(status="SUBMITTED").count(),
                "approved_loans": Loan.objects.filter(status="ACTIVE").count(),
                "rejected_loans": LoanApplication.objects.filter(status="REJECTED").count(),
                "active_loans": Loan.objects.filter(status="ACTIVE").count(),
                "total_disbursed": Loan.objects.aggregate(total=Sum("amount"))["total"] or 0,
            }
        else:
            # Customer stats
            user_loans = Loan.objects.filter(borrowers__user=user)
            user_apps = LoanApplication.objects.filter(applicants__user=user)

            data = {
                "total_loans": user_loans.count(),
                "pending_loans": user_apps.filter(status="SUBMITTED").count(),
                "approved_loans": user_loans.filter(status="ACTIVE").count(),
                "rejected_loans": user_apps.filter(status="REJECTED").count(),
                "active_loans": user_loans.filter(status="ACTIVE").count(),
                "total_disbursed": user_loans.aggregate(total=Sum("amount"))["total"] or 0,
            }

        return Response(data)
