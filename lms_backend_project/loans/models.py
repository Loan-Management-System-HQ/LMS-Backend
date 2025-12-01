import uuid

from django.db import models


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
    principal_due = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    interest_due = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    late_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "installment"
        ordering = ["loan", "due_date"]

    def __str__(self):
        return f"Installment {self.id.hex[:8]} - Loan {self.loan.id.hex[:8]}"
