# simulations/api_schema.py
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .serializers import (
    SimulationCreateSerializer,
    SimulationHeaderSerializer,
)

# --- Schemas ---

# Create Simulation
create_schema = swagger_auto_schema(
    operation_description="Create a new simulation. Saves for authenticated users, returns result for anonymous.",
    request_body=SimulationCreateSerializer,
    responses={
        201: SimulationHeaderSerializer,
        200: openapi.Response(
            description="Simulation result (Anonymous)",
            examples={
                "application/json": {
                    "simulation_id": "uuid",
                    "monthly_payment": 500.00,
                    "total_interest": 1200.00,
                    "total_payment": 11200.00,
                    "amortization_table": [],
                }
            },
        ),
        400: "Bad Request",
    },
)

# Calculate Only
calculate_schema = swagger_auto_schema(
    operation_description="Calculate simulation without saving.",
    request_body=SimulationCreateSerializer,
    responses={
        200: openapi.Response(
            description="Calculation result",
            examples={
                "application/json": {
                    "monthly_payment": 500.00,
                    "total_interest": 1200.00,
                    "total_payment": 11200.00,
                    "amortization_table": [],
                }
            },
        ),
        400: "Bad Request",
    },
)
