from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .models import CustomerLoan, Installment, Loan, LoanApplication, LoanApplicationDocument, UserLoanApplication
from .serializers import (
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
        user = self.request.user

        # Staff can see all applications
        if user.is_staff:
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

        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

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
        user = self.request.user

        # Staff can see all loans
        if user.is_staff:
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
    """ViewSet for Installment"""

    serializer_class = InstallmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "loan"]
    ordering_fields = ["due_date", "installment_number"]

    def get_queryset(self):
        """Return installments for the current user"""
        user = self.request.user

        # Staff can see all installments
        if user.is_staff:
            return Installment.objects.all()

        # Customers can only see their installments
        if hasattr(user, "customer"):
            customer_loan_ids = CustomerLoan.objects.filter(customer=user.customer).values_list("loan_id", flat=True)

            return Installment.objects.filter(loan_id__in=customer_loan_ids)

        return Installment.objects.none()

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        """Get overdue installments"""
        queryset = self.get_queryset().filter(status="PENDING", due_date__lt=timezone.now())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Get upcoming installments (due in next 30 days)"""
        thirty_days_from_now = timezone.now() + timedelta(days=30)
        queryset = self.get_queryset().filter(
            status="PENDING", due_date__gte=timezone.now(), due_date__lte=thirty_days_from_now
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PaymentView(generics.GenericAPIView):
    """View for making payments"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            installment = serializer.validated_data["installment"]
            amount = serializer.validated_data["amount"]
            payment_date = serializer.validated_data.get("payment_date", timezone.now())

            # Check if user owns this installment
            user = request.user
            if hasattr(user, "customer"):
                customer_loan_exists = CustomerLoan.objects.filter(
                    customer=user.customer, loan=installment.loan
                ).exists()

                if not customer_loan_exists and not user.is_staff:
                    return Response(
                        {"error": "You do not have permission to make this payment"}, status=status.HTTP_403_FORBIDDEN
                    )

            # Process payment
            installment.mark_as_paid(amount, payment_date)

            return Response(
                {
                    "status": "Payment processed successfully",
                    "installment_id": str(installment.id),
                    "amount_paid": amount,
                    "balance_due": installment.balance_due,
                    "new_status": installment.status,
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoanCalculatorView(generics.GenericAPIView):
    """View for loan calculations"""

    permission_classes = [permissions.AllowAny]  # Allow anyone to use calculator
    serializer_class = LoanCalculatorSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            calculation = serializer.calculate()
            return Response(calculation)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DashboardView(generics.GenericAPIView):
    """View for dashboard statistics"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.is_staff:
            # Admin dashboard
            stats = {
                "total_loan_applications": LoanApplication.objects.count(),
                "pending_applications": LoanApplication.objects.filter(status="SUBMITTED").count(),
                "approved_applications": LoanApplication.objects.filter(is_approved=True).count(),
                "total_loans": Loan.objects.count(),
                "active_loans": Loan.objects.filter(status="ACTIVE").count(),
                "total_disbursed": Loan.objects.aggregate(total=Sum("amount"))["total"] or 0,
                "overdue_installments": Installment.objects.filter(
                    status="PENDING", due_date__lt=timezone.now()
                ).count(),
            }
        else:
            # Customer dashboard
            # Get customer's loan applications
            user_app_ids = UserLoanApplication.objects.filter(user=user).values_list("loan_application_id", flat=True)

            loan_applications = LoanApplication.objects.filter(id__in=user_app_ids)

            # Get customer's loans (if they have a customer profile)
            if hasattr(user, "customer"):
                customer_loan_ids = CustomerLoan.objects.filter(customer=user.customer).values_list(
                    "loan_id", flat=True
                )

                loans = Loan.objects.filter(id__in=customer_loan_ids)

                overdue_installments = Installment.objects.filter(
                    loan_id__in=customer_loan_ids, status="PENDING", due_date__lt=timezone.now()
                ).count()

                total_outstanding = sum(loan.calculate_outstanding_balance() for loan in loans)
            else:
                loans = Loan.objects.none()
                overdue_installments = 0
                total_outstanding = 0

            stats = {
                "my_loan_applications": loan_applications.count(),
                "pending_applications": loan_applications.filter(status="SUBMITTED").count(),
                "approved_applications": loan_applications.filter(is_approved=True).count(),
                "my_loans": loans.count(),
                "active_loans": loans.filter(status="ACTIVE").count(),
                "total_outstanding": total_outstanding,
                "overdue_installments": overdue_installments,
                "next_payment_due": None,
            }

            # Find next payment due date
            if hasattr(user, "customer"):
                next_installment = (
                    Installment.objects.filter(
                        loan_id__in=customer_loan_ids, status="PENDING", due_date__gte=timezone.now()
                    )
                    .order_by("due_date")
                    .first()
                )

                if next_installment:
                    stats["next_payment_due"] = next_installment.due_date.isoformat()
                    stats["next_payment_amount"] = float(next_installment.balance_due)

        return Response(stats)
