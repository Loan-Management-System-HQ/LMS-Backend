from decimal import Decimal
import random
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed the database with mock users, staff, simulations, loans, and documents"

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        from users.models import Staff, Customer
        from simulations.models import SimulationHeader, SimulationDetail
        from loans.models import LoanApplication, UserLoanApplication, LoanApplicationDocument
        from documents.models import Document

        User = get_user_model()

        self.stdout.write("Seeding mock data...")

        # Create staff users
        staff_users = []
        for i, role in enumerate(["LOAN_OFFICER", "ADMIN"], start=1):
            email = f"staff{i}@example.com"
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(email=email, password="Password123!", name=f"Staff {i}")
                staff = Staff.objects.create(user=user, role=role)
                staff_users.append(user)
        self.stdout.write(f"Created {len(staff_users)} staff users")

        # Create customers / users
        customers = []
        for i in range(1, 6):
            email = f"user{i}@example.com"
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(email=email, password="Password123!", name=f"User {i}")
                customer = Customer.objects.create(user=user)
                customers.append(user)
        self.stdout.write(f"Created {len(customers)} customer users")

        # Create simulations for first 3 users
        for user in customers[:3]:
            amount = Decimal(random.randint(5000, 50000))
            duration = random.choice([12, 24, 36, 48])
            interest = Decimal(random.choice([5.5, 7.0, 9.25]))

            sim = SimulationHeader.objects.create(user=user, amount=amount, duration=duration, interest_rate=interest)

            # Simple amortization to populate details
            monthly_rate = float(interest) / 100.0 / 12.0
            P = float(amount)
            N = duration
            if monthly_rate == 0:
                emi = P / N
            else:
                emi = (P * monthly_rate * (1 + monthly_rate) ** N) / (((1 + monthly_rate) ** N) - 1)

            remaining = P
            total_interest = 0
            for n in range(1, N + 1):
                interest_payment = remaining * monthly_rate
                principal_payment = emi - interest_payment
                ending = remaining - principal_payment
                SimulationDetail.objects.create(
                    simulation=sim,
                    installment_number=n,
                    beginning_balance=Decimal(round(remaining, 2)),
                    installment=Decimal(round(emi, 2)),
                    interest_payment=Decimal(round(interest_payment, 2)),
                    principal_payment=Decimal(round(principal_payment, 2)),
                    ending_balance=Decimal(round(max(ending, 0.0), 2)),
                )
                remaining = ending
                total_interest += interest_payment

            sim.monthly_payment = Decimal(round(emi, 2))
            sim.total_interest = Decimal(round(total_interest, 2))
            sim.total_payment = Decimal(round(P + total_interest, 2))
            sim.save()

        self.stdout.write("Created simulations for sample users")

        # Create loan applications for first 3 users and attach documents
        for user in customers[:3]:
            app = LoanApplication.objects.create(amount=Decimal(10000), duration=24, interest_rate=Decimal("7.5"))
            UserLoanApplication.objects.create(user=user, loan_application=app)

            # create and attach required documents
            for dtype in ["GOVT_ID", "PAYROLL", "CREDIT_HISTORY"]:
                doc = Document.objects.create(
                    uploaded_by=user,
                    document_type=dtype,
                    file_name=f"{dtype.lower()}_{user.id.hex[:6]}.pdf",
                    original_filename=f"{dtype.lower()}.pdf",
                    display_filename=f"{dtype.replace('_', ' ').title()}",
                    link="",
                    status="PENDING",
                )
                LoanApplicationDocument.objects.create(loan_application=app, document=doc)

        self.stdout.write("Created sample loan applications with attached documents")

        self.stdout.write("Seeding complete.")
