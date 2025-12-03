import random
from decimal import Decimal

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed the database with mock users, staff, simulations, loans, and documents"

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        from documents.models import Document
        from loans.models import LoanApplication, LoanApplicationDocument, UserLoanApplication
        from simulations.models import SimulationDetail, SimulationHeader
        from users.models import Customer, Staff

        User = get_user_model()

        self.stdout.write("Seeding mock data...")

        # Create or ensure staff users
        staff_users = []
        for i, role in enumerate(["LOAN_OFFICER", "ADMIN"], start=1):
            email = f"staff{i}@example.com"
            user_defaults = {"name": f"Staff {i}", "password": "Password123!"}
            user, created = User.objects.get_or_create(email=email, defaults={"name": user_defaults["name"]})
            if created:
                # If created via get_or_create, set password properly
                user.set_password("Password123!")
                user.save()
            # Ensure Staff record exists for this user
            Staff.objects.get_or_create(user=user, defaults={"role": role})
            staff_users.append(user)
        self.stdout.write(f"Ensured {len(staff_users)} staff users (created if missing)")

        # Create or ensure customers / users
        customers = []
        for i in range(1, 6):
            email = f"user{i}@example.com"
            user, created = User.objects.get_or_create(email=email, defaults={"name": f"User {i}"})
            if created:
                user.set_password("Password123!")
                user.save()
            # Ensure Customer record exists for this user
            Customer.objects.get_or_create(user=user)
            customers.append(user)
        self.stdout.write(f"Ensured {len(customers)} customer users (created if missing)")

        # Create simulations for first 3 users if they don't already have any
        for user in customers[:3]:
            if SimulationHeader.objects.filter(user=user).exists():
                continue

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

        # Create loan applications for first 3 users and attach documents if not already present
        import datetime
        import os

        from django.conf import settings
        from django.core.files import File as DjangoFile

        for user in customers[:3]:
            # If user already has an application, skip to avoid duplicates
            if UserLoanApplication.objects.filter(user=user).exists():
                continue

            app = LoanApplication.objects.create(amount=Decimal(10000), duration=24, interest_rate=Decimal("7.5"))
            UserLoanApplication.objects.create(user=user, loan_application=app)

            # create and attach sample documents (create file under MEDIA_ROOT)
            for dtype in ["GOVT_ID", "PAYROLL", "CREDIT_HISTORY"]:
                # Ensure directory exists
                media_root = getattr(settings, "MEDIA_ROOT", None) or "."  # fallback to cwd if settings not configured
                user_dir = os.path.join(media_root, "documents", f"user_{str(user.id).replace('-', '')[:8]}")
                os.makedirs(user_dir, exist_ok=True)

                timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
                filename = f"seed_{dtype.lower()}_{timestamp}.txt"
                filepath = os.path.join(user_dir, filename)

                # Write a small dummy file
                with open(filepath, "wb") as f:
                    f.write(f"Seed file for {dtype} for user {user.email}\n".encode("utf-8"))

                # Create Document and attach file
                doc = Document.objects.create(
                    uploaded_by=user,
                    document_type=dtype,
                    original_filename=filename,
                    status="PENDING",
                )

                # Save file to Django FileField
                with open(filepath, "rb") as f:
                    django_file = DjangoFile(f)
                    doc.file.save(filename, django_file, save=True)

                LoanApplicationDocument.objects.create(loan_application=app, document=doc)

        self.stdout.write("Created sample loan applications with attached documents")

        self.stdout.write("Seeding complete.")
