import os
from datetime import timedelta

import django
from django.utils import timezone

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms_backend_project.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from loans.models import CustomerLoan, Installment, Loan, LoanApplication, UserLoanApplication  # noqa: E402
from users.models import Customer, Staff  # noqa: E402

User = get_user_model()


def create_dummy_data():
    print("Creating dummy data...")

    # 1. Create Staff User
    staff_email = "staff@example.com"
    staff_user, created = User.objects.get_or_create(
        email=staff_email,
        defaults={"name": "Staff User", "phone": "1234567890", "is_staff": True, "is_superuser": True},
    )
    if created:
        staff_user.set_password("staff@123")
        staff_user.save()
        print(f"Created staff user: {staff_email}")

    staff_profile, _ = Staff.objects.get_or_create(user=staff_user, defaults={"role": "LOAN_OFFICER"})

    # 2. Create Regular User & Customer Profile
    user_email = "user@example.com"
    user, created = User.objects.get_or_create(
        email=user_email, defaults={"name": "Regular User", "phone": "0987654321"}
    )
    if created:
        user.set_password("password@123")
        user.save()
        print(f"Created regular user: {user_email}")
    else:
        user.set_password("password@123")
        user.save()
        print(f"Updated regular user password: {user_email}")

    customer_profile, _ = Customer.objects.get_or_create(user=user)

    # 3. Create Loan Applications & Loans
    # First, find all loans for this user
    existing_loans = Loan.objects.filter(customers__user=user)
    for loan in existing_loans:
        # We must delete the loan first because on_delete=PROTECT on loan_application
        app = loan.loan_application
        loan.delete()
        if app:
            app.delete()

    # Now delete any remaining applications (those without loans, e.g. PENDING/REJECTED)
    LoanApplication.objects.filter(users=user).delete()

    loans_data = [
        # 1. Active Loan for Payment Demo (Partially Paid)
        {"amount": 20000, "term": 12, "rate": 5.0, "status": "APPROVED", "paid_installments": 3},
        # 2. Pending Application for Staff Approval Demo
        {"amount": 10000, "term": 24, "rate": 6.0, "status": "PENDING", "paid_installments": 0},
        # 3. Rejected Application (History)
        {"amount": 50000, "term": 36, "rate": 7.0, "status": "REJECTED", "paid_installments": 0},
    ]

    for i, data in enumerate(loans_data):
        app_status = data["status"] if data["status"] != "PAID_OFF" else "APPROVED"
        
        # Create Application
        loan_app = LoanApplication.objects.create(
            amount=data["amount"],
            duration=data["term"],
            interest_rate=data["rate"],
            status=app_status,
            is_approved=app_status == "APPROVED",
        )

        # Link Application to User
        UserLoanApplication.objects.create(user=user, loan_application=loan_app)

        if data["status"] == "PENDING" or data["status"] == "REJECTED":
            print(f"Created {data['status']} application: {loan_app.id}")
            continue

        # Create Loan for Approved
        loan_status = "ACTIVE"
        
        # Calculate monthly payment
        r = data["rate"] / 12 / 100
        if r == 0:
            monthly_payment = data["amount"] / data["term"]
        else:
            monthly_payment = data["amount"] * r * ((1 + r) ** data["term"]) / (((1 + r) ** data["term"]) - 1)

        loan = Loan.objects.create(
            loan_application=loan_app,
            staff=staff_profile,
            amount=data["amount"],
            duration=data["term"],
            interest_rate=data["rate"],
            payment=monthly_payment,
            status=loan_status,
            disbursement_date=timezone.now() - timedelta(days=30 * (data["paid_installments"] + 1)),
            commencing_date=timezone.now() - timedelta(days=30 * data["paid_installments"]),
        )

        # Link Loan to Customer
        CustomerLoan.objects.create(customer=customer_profile, loan=loan)
        print(f"Created loan: {loan.id} ({loan_status})")

        # Create Installments
        for j in range(1, data["term"] + 1):
            # Due date relative to commencing date
            due_date = loan.commencing_date + timedelta(days=30 * (j - 1))
            
            # Determine status based on how many we want paid
            if j <= data["paid_installments"]:
                status = "PAID"
                paid_date = due_date - timedelta(days=2) # Paid 2 days early
            elif j == data["paid_installments"] + 1:
                status = "PENDING" # Next due
                paid_date = None
            else:
                status = "PENDING" # Future
                paid_date = None

            Installment.objects.create(
                loan=loan,
                installment_number=j,
                due_date=due_date,
                due_amount=monthly_payment,
                payment_amount=monthly_payment if status == "PAID" else 0,
                status=status,
                payment_date=paid_date,
            )

    print("Dummy data creation complete!")


if __name__ == "__main__":
    create_dummy_data()
