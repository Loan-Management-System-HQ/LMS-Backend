import uuid
from django.db import models


class SimulationHeader(models.Model):
    # Django PK convention, maps to 'simID' in DB
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column="simID")

    # ForeignKey with Django convention, maps to 'userID' in DB
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="simulations", db_column="userID")

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    duration = models.IntegerField()  # In months
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, db_column="interestRate")
    simulation_date = models.DateTimeField(auto_now_add=True)

    # Calculated fields
    monthly_payment = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_interest = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_payment = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "simulation_header"
        ordering = ["-simulation_date"]

    def __str__(self):
        return f"Simulation {self.id.hex[:8]} - ${self.amount}"


class SimulationDetail(models.Model):
    # Django uses single PK, we'll simulate composite PK with unique constraint
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ForeignKey with Django convention, maps to 'simID' in DB
    simulation = models.ForeignKey(
        SimulationHeader, on_delete=models.CASCADE, related_name="details", db_column="simID"
    )

    # Maps to 'installmentID' in DB
    installment_number = models.IntegerField(db_column="installmentID")

    # Amortization details
    beginning_balance = models.DecimalField(max_digits=15, decimal_places=2)
    installment = models.DecimalField(max_digits=15, decimal_places=2)
    interest_payment = models.DecimalField(max_digits=15, decimal_places=2)
    principal_payment = models.DecimalField(max_digits=15, decimal_places=2)
    ending_balance = models.DecimalField(max_digits=15, decimal_places=2)

    # Custom payment options
    custom_payment = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    is_prepayment = models.BooleanField(default=False)
    is_delayed = models.BooleanField(default=False)

    class Meta:
        db_table = "simulation_detail"
        ordering = ["simulation", "installment_number"]
        unique_together = ["simulation", "installment_number"]  # Simulates composite PK

    def __str__(self):
        return f"Installment {self.installment_number} - Sim {self.simulation.id.hex[:8]}"
