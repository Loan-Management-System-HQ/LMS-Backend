import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone


# LoanApplication model
class LoanApplication(models.Model):
    APPLICATION_STATUS = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("UNDER_REVIEW", "Under Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    # Django PK convention, maps to 'loanApplicationID' in DB
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column="loanApplicationID",
    )

    # Optional simulation reference
    simulation = models.ForeignKey(
        "simulations.SimulationHeader",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loan_applications",
        db_column="simID",
    )

    # Application details
    is_approved = models.BooleanField(default=False, db_column="isApproved")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    duration = models.IntegerField()  # In months
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, db_column="interestRate")

    # Status tracking
    status = models.CharField(max_length=50, choices=APPLICATION_STATUS, default="DRAFT")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Many-to-Many with User through junction table
    users = models.ManyToManyField("users.User", through="UserLoanApplication")

    # Many-to-Many with Document through junction table
    documents = models.ManyToManyField("documents.Document", through="LoanApplicationDocument")

    class Meta:
        db_table = "loan_application"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Loan Application {self.id.hex[:8]}"

    def calculate_emi(self):
        """
        Calculate Equated Monthly Installment (EMI) using the formula:
        EMI = [P x R x (1+R)^N]/[(1+R)^N-1]
        where:
        P = principal loan amount
        R = monthly interest rate
        N = number of monthly installments
        """
        P = float(self.amount)
        R = float(self.interest_rate) / (12 * 100)  # Convert annual rate to monthly and decimal
        N = int(self.duration)

        if R == 0:  # If interest rate is 0%
            emi = P / N
        else:
            emi = (P * R * (1 + R) ** N) / (((1 + R) ** N) - 1)

        return Decimal(round(emi, 2))

        return emi * self.duration

    def get_total_payable(self):
        """Calculate total payable amount"""
        emi = self.calculate_emi()
        return emi * self.duration

    def get_total_interest(self):
        """Calculate total interest payable"""
        return self.get_total_payable() - self.amount

    @property
    def customer(self):
        """Get the primary customer for this application"""
        user_loan_app = self.userloanapplication_set.first()
        if user_loan_app:
            return user_loan_app.user
        return None

    @property
    def customer_name(self):
        """Get customer name"""
        customer = self.customer
        if customer:
            return customer.get_full_name()
        return "Unknown"


# Many-to-Many User <-> LoanApplication junction table
class UserLoanApplication(models.Model):
    # Django automatically creates 'id' field for junction tables
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, db_column="userID")
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, db_column="loanApplicationID")

    class Meta:
        db_table = "user_loan_application"
        unique_together = ["user", "loan_application"]

    def __str__(self):
        return f"{self.user.name} - Loan Application {self.loan_application.id.hex[:8]}"


# Many-to-Many LoanApplication <-> Document junction table
class LoanApplicationDocument(models.Model):
    # Django automatically creates 'id' field
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, db_column="loanApplicationID")
    document = models.ForeignKey("documents.Document", on_delete=models.CASCADE, db_column="documentID")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "loan_application_document"
        unique_together = ["loan_application", "document"]

    def __str__(self):
        return f"Loan Application {self.loan_application.id.hex[:8]} - Document {self.document.id.hex[:8]}"


# Loan model
class Loan(models.Model):
    LOAN_STATUS = [
        ("ACTIVE", "Active"),
        ("PAID_OFF", "Paid Off"),
        ("DELINQUENT", "Delinquent"),
        ("DEFAULTED", "Defaulted"),
    ]

    # Django PK convention, maps to 'loanID' in DB
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column="loanID")

    # Relationships
    loan_application = models.OneToOneField(
        LoanApplication,
        on_delete=models.PROTECT,
        related_name="loan",
        db_column="loanApplicationID",
    )
    staff = models.ForeignKey(
        "users.Staff",
        on_delete=models.PROTECT,
        related_name="approved_loans",
        db_column="staffID",
    )

    # Loan details
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    duration = models.IntegerField()  # In months
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, db_column="interestRate")
    payment = models.DecimalField(max_digits=15, decimal_places=2)  # Monthly payment
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default="ACTIVE")

    # Dates
    disbursement_date = models.DateTimeField(db_column="disbursementDate")
    commencing_date = models.DateTimeField(db_column="commencingDate")

    # Many-to-Many with Customer through junction table
    customers = models.ManyToManyField("users.Customer", through="CustomerLoan")

    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "loan"
        ordering = ["-disbursement_date"]

    def __str__(self):
        return f"Loan {self.id.hex[:8]} - ${self.amount}"

    def calculate_outstanding_balance(self):
        """Calculate outstanding principal balance"""
        from decimal import Decimal

        # Sum of all principal payments made
        total_principal_paid = self.installments.aggregate(total=models.Sum("payment_amount"))["total"] or Decimal(
            "0.00"
        )

        # For simplicity, assuming payment_amount goes toward principal first
        # In a real system, you'd need to track principal vs interest separately
        return self.amount - total_principal_paid

    def get_next_due_date(self):
        """Get the next due installment date"""
        next_installment = self.installments.filter(status="PENDING").order_by("due_date").first()

        if next_installment:
            return next_installment.due_date
        return None

    @property
    def primary_customer(self):
        """Get primary customer for this loan"""
        customer_loan = self.customerloan_set.first()
        if customer_loan:
            return customer_loan.customer
        return None


# Many-to-Many Customer <-> Loan junction table
class CustomerLoan(models.Model):
    customer = models.ForeignKey("users.Customer", on_delete=models.CASCADE, db_column="customerID")  # UPDATED
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, db_column="loanID")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "customer_loan"
        unique_together = ["customer", "loan"]

    def __str__(self):
        return f"Customer {self.customer.user.name} - Loan {self.loan.id.hex[:8]}"


# Installment model
class Installment(models.Model):
    INSTALLMENT_STATUS = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("OVERDUE", "Overdue"),
        ("PARTIAL", "Partially Paid"),
    ]

    # Django PK convention
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ForeignKey with Django convention, maps to 'loanID' in DB
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="installments", db_column="loanID")

    installment_number = models.IntegerField(db_column="installmentID")  # Sequential number of the installment
    due_amount = models.DecimalField(max_digits=15, decimal_places=2, db_column="amount")
    due_date = models.DateTimeField(db_column="dueDate")
    status = models.CharField(max_length=20, choices=INSTALLMENT_STATUS, default="PENDING")

    # Payment info
    payment_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, db_column="paymentAmount")
    payment_date = models.DateTimeField(null=True, blank=True, db_column="paymentDate")

    # ADD THESE MISSING FIELDS: [ERD doesn't have it]
    late_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "installment"
        ordering = ["loan", "due_date"]

    def __str__(self):
        return f"Installment {self.id.hex[:8]} - Loan {self.loan.id.hex[:8]}"

    @property
    def is_overdue(self):
        """Check if installment is overdue"""
        return self.status == "PENDING" and self.due_date < timezone.now()

    @property
    def balance_due(self):
        """Calculate remaining balance"""
        return self.due_amount - self.payment_amount

    def mark_as_paid(self, amount_paid, payment_date=None):
        """Mark installment as paid (fully or partially)"""
        self.payment_amount = amount_paid
        self.payment_date = payment_date or timezone.now()

        if amount_paid >= self.due_amount:
            self.status = "PAID"
        elif amount_paid > 0:
            self.status = "PARTIAL"

        self.save()
