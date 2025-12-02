import uuid
from decimal import Decimal

from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import SimulationDetail, SimulationHeader
from .serializers import (
    AnonymousSimulationCreateSerializer,
    SimulationCreateSerializer,
    SimulationHeaderSerializer,
)


class SimulationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for loan simulations.
    """

    serializer_class = SimulationHeaderSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return SimulationHeader.objects.filter(user=self.request.user)
        # Anonymous users - return empty queryset for safety
        return SimulationHeader.objects.none()

    def create(self, request, *args, **kwargs):
        """
        Create a new simulation.
        If user is authenticated: save to their account
        If anonymous: just calculate and return results without saving
        """
        if request.user.is_authenticated:
            serializer = SimulationCreateSerializer(data=request.data)
        else:
            serializer = AnonymousSimulationCreateSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            if request.user.is_authenticated:
                # Create and save simulation for authenticated user
                with transaction.atomic():
                    # Create simulation header
                    simulation = SimulationHeader.objects.create(
                        user=request.user,
                        amount=data["amount"],
                        duration=data["duration"],
                        interest_rate=data["interest_rate"],
                    )

                    # Calculate and create details
                    self._create_simulation_details(simulation)

                    return Response(self.get_serializer(simulation).data, status=status.HTTP_201_CREATED)
            else:
                # Anonymous user - just calculate and return results
                simulation_id = uuid.uuid4()
                result = self._calculate_simulation(data["amount"], data["duration"], data["interest_rate"])

                return Response(
                    {
                        "simulation_id": simulation_id,
                        "amount": data["amount"],
                        "duration": data["duration"],
                        "interest_rate": data["interest_rate"],
                        "monthly_payment": result["monthly_payment"],
                        "total_interest": result["total_interest"],
                        "total_payment": result["total_payment"],
                        "amortization_table": result["amortization_table"],
                    },
                    status=status.HTTP_200_OK,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def calculate(self, request):
        """
        Calculate simulation without saving (works for both anonymous and authenticated)
        """
        serializer = SimulationCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            result = self._calculate_simulation(data["amount"], data["duration"], data["interest_rate"])

            return Response(
                {
                    "monthly_payment": result["monthly_payment"],
                    "total_interest": result["total_interest"],
                    "total_payment": result["total_payment"],
                    "amortization_table": result["amortization_table"],
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def history(self, request):
        """
        Get simulation history for authenticated user
        """
        simulations = SimulationHeader.objects.filter(user=request.user).order_by("-simulation_date")
        serializer = self.get_serializer(simulations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def use_for_application(self, request, pk=None):
        """
        Mark simulation for loan application
        """
        simulation = self.get_object()
        if simulation.user != request.user:
            return Response(
                {"error": "You do not have permission to use this simulation."}, status=status.HTTP_403_FORBIDDEN
            )

        # Note: Since you don't have is_used_for_application field,
        # you might want to add this or handle differently
        return Response(
            {
                "status": "success",
                "message": f"Simulation {pk} can be used for application",
                "simulation_data": self.get_serializer(simulation).data,
            }
        )

    def _calculate_simulation(self, amount, duration, interest_rate):
        """Calculate amortization without saving to database"""
        monthly_rate = float(interest_rate) / 100 / 12
        periods = duration
        loan_amount = float(amount)

        # Calculate monthly payment
        if monthly_rate > 0:
            monthly_payment = (loan_amount * monthly_rate) / (1 - (1 + monthly_rate) ** -periods)
        else:
            monthly_payment = loan_amount / periods

        # Calculate amortization table
        balance = loan_amount
        amortization_table = []

        for month in range(1, periods + 1):
            interest = balance * monthly_rate
            principal = monthly_payment - interest
            balance -= principal

            # Handle last payment adjustment
            if balance < 0:
                principal += balance
                monthly_payment += balance
                balance = 0

            amortization_table.append(
                {
                    "installment_number": month,
                    "beginning_balance": Decimal(round(balance + principal, 2)),
                    "installment": Decimal(round(monthly_payment, 2)),
                    "interest_payment": Decimal(round(interest, 2)),
                    "principal_payment": Decimal(round(principal, 2)),
                    "ending_balance": Decimal(round(balance, 2)),
                }
            )

        return {
            "monthly_payment": Decimal(round(monthly_payment, 2)),
            "total_interest": Decimal(round(sum(row["interest_payment"] for row in amortization_table), 2)),
            "total_payment": Decimal(round(monthly_payment * periods, 2)),
            "amortization_table": amortization_table,
        }

    def _create_simulation_details(self, simulation):
        """Create simulation details based on calculated values"""
        result = self._calculate_simulation(simulation.amount, simulation.duration, simulation.interest_rate)

        # Update simulation header with calculated values
        simulation.monthly_payment = result["monthly_payment"]
        simulation.total_interest = result["total_interest"]
        simulation.total_payment = result["total_payment"]
        simulation.save()

        # Create simulation details
        details = []
        for row in result["amortization_table"]:
            detail = SimulationDetail(
                simulation=simulation,
                installment_number=row["installment_number"],
                beginning_balance=row["beginning_balance"],
                installment=row["installment"],
                interest_payment=row["interest_payment"],
                principal_payment=row["principal_payment"],
                ending_balance=row["ending_balance"],
            )
            details.append(detail)

        SimulationDetail.objects.bulk_create(details)
