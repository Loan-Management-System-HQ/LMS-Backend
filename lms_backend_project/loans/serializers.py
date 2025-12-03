from decimal import Decimal

from documents.serializers import DocumentSerializer
from rest_framework import serializers
from users.serializers import CustomerSerializer, UserSerializer

from .models import CustomerLoan, Installment, Loan, LoanApplication, LoanApplicationDocument, UserLoanApplication


class LoanApplicationSerializer(serializers.ModelSerializer):
    """Serializer for LoanApplication"""

    customer = UserSerializer(source="customer", read_only=True)
    customer_name = serializers.CharField(source="customer_name", read_only=True)
    emi = serializers.SerializerMethodField()
    total_payable = serializers.SerializerMethodField()
    total_interest = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = LoanApplication
        fields = [
            "id",
            "simulation",
            "is_approved",
            "amount",
            "duration",
            "interest_rate",
            "status",
            "created_at",
            "updated_at",
            "customer",
            "customer_name",
            "emi",
            "total_payable",
            "total_interest",
            "status_display",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_approved"]

    def get_emi(self, obj):
        return obj.calculate_emi()

    def get_total_payable(self, obj):
        return obj.get_total_payable()

    def get_total_interest(self, obj):
        return obj.get_total_interest()

    def validate(self, data):
        """Validate loan application data"""
        # Ensure amount is positive
        if "amount" in data and data["amount"] <= 0:
            raise serializers.ValidationError({"amount": "Loan amount must be greater than zero."})

        # Ensure duration is reasonable
        if "duration" in data:
            if data["duration"] < 1:
                raise serializers.ValidationError({"duration": "Loan duration must be at least 1 month."})
            if data["duration"] > 360:  # 30 years max
                raise serializers.ValidationError({"duration": "Loan duration cannot exceed 360 months."})

        # Ensure interest rate is reasonable
        if "interest_rate" in data:
            if data["interest_rate"] <= 0:
                raise serializers.ValidationError({"interest_rate": "Interest rate must be greater than zero."})
            if data["interest_rate"] > 100:  # 100% max
                raise serializers.ValidationError({"interest_rate": "Interest rate cannot exceed 100%."})

        return data


class UserLoanApplicationSerializer(serializers.ModelSerializer):
    """Serializer for User-LoanApplication relationship"""

    user = UserSerializer(read_only=True)
    loan_application = LoanApplicationSerializer(read_only=True)

    class Meta:
        model = UserLoanApplication
        fields = ["id", "user", "loan_application", "created_at"]


class LoanApplicationDocumentSerializer(serializers.ModelSerializer):
    """Serializer for LoanApplication-Document relationship"""

    document = DocumentSerializer(read_only=True)
    loan_application = LoanApplicationSerializer(read_only=True)

    class Meta:
        model = LoanApplicationDocument
        fields = ["id", "loan_application", "document", "created_at"]


class LoanSerializer(serializers.ModelSerializer):
    """Serializer for Loan"""

    loan_application = LoanApplicationSerializer(read_only=True)
    staff = serializers.StringRelatedField()
    primary_customer = CustomerSerializer(source="primary_customer", read_only=True)
    outstanding_balance = serializers.SerializerMethodField()
    next_due_date = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Loan
        fields = [
            "id",
            "loan_application",
            "staff",
            "amount",
            "duration",
            "interest_rate",
            "payment",
            "status",
            "disbursement_date",
            "commencing_date",
            "created_at",
            "updated_at",
            "primary_customer",
            "outstanding_balance",
            "next_due_date",
            "status_display",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_outstanding_balance(self, obj):
        return obj.calculate_outstanding_balance()

    def get_next_due_date(self, obj):
        next_due = obj.get_next_due_date()
        return next_due.isoformat() if next_due else None


class CustomerLoanSerializer(serializers.ModelSerializer):
    """Serializer for Customer-Loan relationship"""

    customer = CustomerSerializer(read_only=True)
    loan = LoanSerializer(read_only=True)

    class Meta:
        model = CustomerLoan
        fields = ["id", "customer", "loan", "created_at"]


class InstallmentSerializer(serializers.ModelSerializer):
    """Serializer for Installment"""

    loan = serializers.StringRelatedField()
    is_overdue = serializers.BooleanField(read_only=True)
    balance_due = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Installment
        fields = [
            "id",
            "loan",
            "installment_number",
            "due_amount",
            "due_date",
            "status",
            "payment_amount",
            "payment_date",
            "late_fee",
            "created_at",
            "updated_at",
            "is_overdue",
            "balance_due",
            "status_display",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_overdue", "balance_due"]


class PaymentSerializer(serializers.Serializer):
    """Serializer for making payments"""

    installment_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01)
    payment_date = serializers.DateTimeField(required=False)

    def validate(self, data):
        """Validate payment data"""
        try:
            installment = Installment.objects.get(id=data["installment_id"])
        except Installment.DoesNotExist:
            raise serializers.ValidationError({"installment_id": "Installment not found."})

        # Check if installment is already paid
        if installment.status == "PAID":
            raise serializers.ValidationError({"installment_id": "This installment is already paid."})

        # Store installment in validated data for use in save
        data["installment"] = installment
        return data


class LoanCalculatorSerializer(serializers.Serializer):
    """Serializer for loan calculation"""

    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=1000)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0.1, max_value=100)
    duration = serializers.IntegerField(min_value=3, max_value=360)

    def calculate(self):
        """Calculate loan details"""

        amount = self.validated_data["amount"]
        interest_rate = self.validated_data["interest_rate"]
        duration = self.validated_data["duration"]

        # Monthly interest rate
        r = interest_rate / 12 / 100

        # Calculate EMI
        if r == 0:
            emi = amount / duration
        else:
            emi = amount * r * ((1 + r) ** duration) / (((1 + r) ** duration) - 1)

        emi = Decimal(round(emi, 2))
        total_payable = emi * duration
        total_interest = total_payable - amount

        return {
            "emi": emi,
            "total_payable": Decimal(round(total_payable, 2)),
            "total_interest": Decimal(round(total_interest, 2)),
            "amount": amount,
            "interest_rate": interest_rate,
            "duration": duration,
        }
