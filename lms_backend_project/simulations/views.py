import uuid
from decimal import Decimal

from django.db import transaction
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .api_schema import calculate_schema, create_schema
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
        return SimulationHeader.objects.none()

    def _parse_request_data(self, data):
        """Helper to parse and clean request data"""
        parsed = {}

        # Handle amount
        if "amount" in data:
            try:
                parsed["amount"] = Decimal(str(data["amount"]))
            except (ValueError, TypeError):
                raise serializers.ValidationError({"amount": "Must be a valid number (e.g., 10000.00)"})

        # Handle duration
        if "duration" in data:
            try:
                parsed["duration"] = int(float(data["duration"]))
            except (ValueError, TypeError):
                raise serializers.ValidationError({"duration": "Must be a valid integer (e.g., 12)"})

        # Handle interest_rate
        if "interest_rate" in data:
            try:
                parsed["interest_rate"] = Decimal(str(data["interest_rate"]))
            except (ValueError, TypeError):
                raise serializers.ValidationError({"interest_rate": "Must be a valid percentage (e.g., 5.00 for 5%)"})

        return parsed

    @create_schema
    def create(self, request, *args, **kwargs):
        """
        Create a new simulation.
        Works for both anonymous and authenticated users.
        """
        try:
            # Parse and validate input data
            parsed_data = self._parse_request_data(request.data)

            if request.user.is_authenticated:
                serializer = SimulationCreateSerializer(data=parsed_data)
            else:
                serializer = AnonymousSimulationCreateSerializer(data=parsed_data)

            if serializer.is_valid():
                data = serializer.validated_data

                if request.user.is_authenticated:
                    # Create and save simulation for authenticated user
                    with transaction.atomic():
                        simulation = SimulationHeader.objects.create(
                            user=request.user,
                            amount=data["amount"],
                            duration=data["duration"],
                            interest_rate=data["interest_rate"],
                        )
                        self._create_simulation_details(simulation)

                        return Response(SimulationHeaderSerializer(simulation).data, status=status.HTTP_201_CREATED)
                else:
                    # Anonymous user - just calculate without saving
                    simulation_id = uuid.uuid4()
                    result = self._calculate_simulation(data["amount"], data["duration"], data["interest_rate"])

                    return Response(
                        {
                            "simulation_id": str(simulation_id),
                            "amount": float(data["amount"]),
                            "duration": data["duration"],
                            "interest_rate": float(data["interest_rate"]),
                            "monthly_payment": float(result["monthly_payment"]),
                            "total_interest": float(result["total_interest"]),
                            "total_payment": float(result["total_payment"]),
                            "amortization_table": result["amortization_table"],
                        },
                        status=status.HTTP_200_OK,
                    )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Invalid input data", "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @calculate_schema
    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def calculate(self, request):
        """
        Calculate simulation without saving
        Works for both anonymous and authenticated users.
        """
        try:
            # Parse and validate input data
            parsed_data = self._parse_request_data(request.data)
            serializer = SimulationCreateSerializer(data=parsed_data)

            if serializer.is_valid():
                data = serializer.validated_data
                result = self._calculate_simulation(data["amount"], data["duration"], data["interest_rate"])

                return Response(
                    {
                        "monthly_payment": float(result["monthly_payment"]),
                        "total_interest": float(result["total_interest"]),
                        "total_payment": float(result["total_payment"]),
                        "amortization_table": result["amortization_table"],
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Invalid input data", "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def history(self, request):
        """
        Get simulation history for authenticated user
        """
        # Short-circuit during schema generation / fake view
        if getattr(self, "swagger_fake_view", False):
            return Response([])

        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return Response([], status=status.HTTP_401_UNAUTHORIZED)

        simulations = SimulationHeader.objects.filter(user=user).order_by("-simulation_date")
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

        # Return simulation data that can be used for loan application
        return Response(
            {
                "status": "success",
                "message": f"Simulation {pk} can be used for application",
                "simulation_data": self.get_serializer(simulation).data,
            }
        )

    @action(detail=False, methods=["delete"], permission_classes=[permissions.IsAuthenticated])
    def clear_history(self, request):
        """
        Clear all simulations for the authenticated user.
        """
        # Short-circuit for fake views
        if getattr(self, "swagger_fake_view", False):
            return Response({"status": "success", "message": "Deleted 0 simulations from history"})

        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        deleted_count, _ = SimulationHeader.objects.filter(user=user).delete()
        return Response({"status": "success", "message": f"Deleted {deleted_count} simulations from history"})

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
                beginning_balance=Decimal(str(row["beginning_balance"])),
                installment=Decimal(str(row["installment"])),
                interest_payment=Decimal(str(row["interest_payment"])),
                principal_payment=Decimal(str(row["principal_payment"])),
                ending_balance=Decimal(str(row["ending_balance"])),
            )
            details.append(detail)

        SimulationDetail.objects.bulk_create(details)

    def _calculate_simulation(self, amount, duration, interest_rate):
        """Calculate amortization without saving to database"""
        # Ensure we have proper numeric types
        monthly_rate = float(Decimal(str(interest_rate))) / 100 / 12
        periods = int(duration)
        loan_amount = float(Decimal(str(amount)))

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
            if balance < 0.01:  # Tolerance for floating point
                principal += balance
                monthly_payment += balance
                balance = 0

            amortization_table.append(
                {
                    "installment_number": month,
                    "beginning_balance": round(balance + principal, 2),
                    "installment": round(monthly_payment, 2),
                    "interest_payment": round(interest, 2),
                    "principal_payment": round(principal, 2),
                    "ending_balance": round(balance, 2),
                    "custom_payment": None,
                    "is_prepayment": False,
                    "is_delayed": False,
                }
            )

        return {
            "monthly_payment": Decimal(round(monthly_payment, 2)),
            "total_interest": Decimal(round(sum(row["interest_payment"] for row in amortization_table), 2)),
            "total_payment": Decimal(round(monthly_payment * periods, 2)),
            "amortization_table": amortization_table,
        }

    def perform_create(self, serializer):
        """Override to handle creation properly"""
        pass  # We override create() method directly

    def perform_update(self, serializer):
        """Simulations are immutable once created"""
        raise serializers.ValidationError("Simulations cannot be updated once created.")
