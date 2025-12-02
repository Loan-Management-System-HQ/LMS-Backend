from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view

from .serializers import (
    SimulationCreateSerializer,
    SimulationHeaderSerializer,
)
from .views import SimulationViewSet

# Define common examples
SIMULATION_CREATE_EXAMPLE = {"amount": 10000.00, "duration": 12, "interest_rate": 5.0}

SIMULATION_RESPONSE_EXAMPLE = {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "user": 1,
    "user_email": "user@example.com",
    "amount": "10000.00",
    "duration": 12,
    "interest_rate": "5.00",
    "monthly_payment": "856.07",
    "total_interest": "272.84",
    "total_payment": "10272.84",
    "simulation_date": "2025-11-07T10:30:00Z",
    "details": [
        {
            "installment_number": 1,
            "beginning_balance": "10000.00",
            "installment": "856.07",
            "interest_payment": "41.67",
            "principal_payment": "814.40",
            "ending_balance": "9185.60",
            "custom_payment": None,
            "is_prepayment": False,
            "is_delayed": False,
        },
        {
            "installment_number": 2,
            "beginning_balance": "9185.60",
            "installment": "856.07",
            "interest_payment": "38.27",
            "principal_payment": "817.80",
            "ending_balance": "8367.80",
            "custom_payment": None,
            "is_prepayment": False,
            "is_delayed": False,
        },
    ],
}

CALCULATION_RESPONSE_EXAMPLE = {
    "monthly_payment": "856.07",
    "total_interest": "272.84",
    "total_payment": "10272.84",
    "amortization_table": [
        {
            "installment_number": 1,
            "beginning_balance": "10000.00",
            "installment": "856.07",
            "interest_payment": "41.67",
            "principal_payment": "814.40",
            "ending_balance": "9185.60",
            "custom_payment": None,
            "is_prepayment": False,
            "is_delayed": False,
        },
        {
            "installment_number": 2,
            "beginning_balance": "9185.60",
            "installment": "856.07",
            "interest_payment": "38.27",
            "principal_payment": "817.80",
            "ending_balance": "8367.80",
            "custom_payment": None,
            "is_prepayment": False,
            "is_delayed": False,
        },
    ],
}

ANONYMOUS_SIMULATION_RESPONSE = {
    "simulation_id": "123e4567-e89b-12d3-a456-426614174000",
    "amount": "10000.00",
    "duration": 12,
    "interest_rate": "5.00",
    "monthly_payment": "856.07",
    "total_interest": "272.84",
    "total_payment": "10272.84",
    "amortization_table": [
        {
            "installment_number": 1,
            "beginning_balance": "10000.00",
            "installment": "856.07",
            "interest_payment": "41.67",
            "principal_payment": "814.40",
            "ending_balance": "9185.60",
        }
    ],
}

ERROR_RESPONSE_EXAMPLE = {
    "amount": ["This field is required."],
    "duration": ["Ensure this value is greater than or equal to 1."],
    "interest_rate": ["Ensure this value is greater than or equal to 0.01."],
}

USE_FOR_APPLICATION_RESPONSE = {
    "status": "success",
    "message": "Simulation can be used for loan application",
    "simulation_data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "amount": "10000.00",
        "duration": 12,
        "interest_rate": "5.00",
        "monthly_payment": "856.07",
        "total_interest": "272.84",
        "total_payment": "10272.84",
    },
}


# Schema definitions for SimulationViewSet
simulation_schema = {
    "list": extend_schema(
        summary="List user's saved simulations",
        description="""Retrieve all saved simulations for the authenticated user.

        **Authentication Required**: Yes
        **Permissions**: User can only see their own simulations""",
        responses={
            200: SimulationHeaderSerializer(many=True),
            401: OpenApiResponse(
                description="Unauthorized - User not authenticated",
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="Unauthorized", value={"detail": "Authentication credentials were not provided."}
                    )
                ],
            ),
        },
        parameters=[
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Limit number of results (default: 20, max: 100)",
                examples=[OpenApiExample(name="Default", value=20)],
            ),
            OpenApiParameter(
                name="offset",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Offset for pagination (default: 0)",
                examples=[OpenApiExample(name="Default", value=0)],
            ),
            OpenApiParameter(
                name="order_by",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Order by field (amount, duration, simulation_date)",
                examples=[OpenApiExample(name="Recent first", value="-simulation_date")],
            ),
        ],
        examples=[
            OpenApiExample(
                name="Success Response", description="List of user's simulations", value=[SIMULATION_RESPONSE_EXAMPLE]
            )
        ],
        auth=True,
    ),
    "create": extend_schema(
        summary="Create/Calculate loan simulation",
        description="""Create a new loan simulation with full amortization table.

        **For Authenticated Users**: Simulation is saved to user's history
        **For Anonymous Users**: Calculation is performed but not saved

        The system calculates:
        - Monthly payment amount
        - Total interest over loan term
        - Total payment (principal + interest)
        - Complete amortization schedule""",
        request=SimulationCreateSerializer,
        responses={
            201: OpenApiResponse(
                description="Simulation created successfully (authenticated user)",
                response=SimulationHeaderSerializer,
                examples=[OpenApiExample(name="Authenticated User Response", value=SIMULATION_RESPONSE_EXAMPLE)],
            ),
            200: OpenApiResponse(
                description="Calculation successful (anonymous user)",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(name="Anonymous User Response", value=ANONYMOUS_SIMULATION_RESPONSE)],
            ),
            400: OpenApiResponse(
                description="Validation Error",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(name="Validation Error", value=ERROR_RESPONSE_EXAMPLE)],
            ),
        },
        examples=[
            OpenApiExample(
                name="Example Request",
                description="Standard loan simulation parameters",
                value=SIMULATION_CREATE_EXAMPLE,
                request_only=True,
            )
        ],
    ),
    "retrieve": extend_schema(
        summary="Retrieve specific simulation",
        description="""Get detailed information about a specific simulation including complete amortization table.

        **Authentication Required**: Yes (users can only retrieve their own simulations)
        **Returns**: Simulation header with all installment details""",
        responses={
            200: SimulationHeaderSerializer,
            404: OpenApiResponse(
                description="Simulation not found",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(name="Not Found", value={"detail": "Not found."})],
            ),
            403: OpenApiResponse(
                description="Forbidden - User doesn't own this simulation",
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="Forbidden", value={"error": "You do not have permission to access this simulation."}
                    )
                ],
            ),
        },
        examples=[
            OpenApiExample(
                name="Success Response", description="Complete simulation details", value=SIMULATION_RESPONSE_EXAMPLE
            )
        ],
        auth=True,
    ),
    "destroy": extend_schema(
        summary="Delete a simulation",
        description="""Delete a specific simulation from user's history.

        **Authentication Required**: Yes
        **Note**: This action cannot be undone""",
        responses={
            204: OpenApiResponse(description="Simulation deleted successfully"),
            404: OpenApiResponse(
                description="Simulation not found",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(name="Not Found", value={"detail": "Not found."})],
            ),
        },
        auth=True,
    ),
    "calculate": extend_schema(
        summary="Calculate loan simulation without saving",
        description="""Perform loan calculation without saving to database.

        **Authentication**: Not required (works for both anonymous and authenticated users)
        **Use Case**: Quick "what-if" calculations without cluttering history

        Returns the same calculation results as create endpoint but without saving.""",
        request=SimulationCreateSerializer,
        responses={
            200: OpenApiResponse(
                description="Calculation successful",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(name="Calculation Results", value=CALCULATION_RESPONSE_EXAMPLE)],
            ),
            400: OpenApiResponse(
                description="Validation Error",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(name="Validation Error", value=ERROR_RESPONSE_EXAMPLE)],
            ),
        },
        examples=[
            OpenApiExample(
                name="Example Request",
                description="Input parameters for calculation",
                value=SIMULATION_CREATE_EXAMPLE,
                request_only=True,
            )
        ],
    ),
    "history": extend_schema(
        summary="Get user's simulation history",
        description="""Retrieve all simulations saved by the authenticated user.

        **Authentication Required**: Yes
        **Returns**: List of simulations ordered by creation date (newest first)

        This is an alias for the list endpoint with default ordering.""",
        responses={
            200: SimulationHeaderSerializer(many=True),
            401: OpenApiResponse(
                description="Unauthorized",
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="Unauthorized", value={"detail": "Authentication credentials were not provided."}
                    )
                ],
            ),
        },
        parameters=[
            OpenApiParameter(
                name="recent_only",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Return only recent simulations (last 30 days)",
                examples=[OpenApiExample(name="False", value=False)],
            )
        ],
        examples=[
            OpenApiExample(
                name="Success Response", description="User's simulation history", value=[SIMULATION_RESPONSE_EXAMPLE]
            )
        ],
        auth=True,
    ),
    "use_for_application": extend_schema(
        summary="Mark simulation for loan application",
        description="""Prepare a simulation to be used for a loan application.

        **Authentication Required**: Yes
        **Permissions**: User must own the simulation

        This endpoint marks a simulation as "ready for application" and returns
        the simulation data in a format suitable for loan application forms.""",
        responses={
            200: OpenApiResponse(
                description="Simulation marked for application",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(name="Success Response", value=USE_FOR_APPLICATION_RESPONSE)],
            ),
            403: OpenApiResponse(
                description="Forbidden - User doesn't own this simulation",
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        name="Forbidden", value={"error": "You do not have permission to use this simulation."}
                    )
                ],
            ),
            404: OpenApiResponse(
                description="Simulation not found",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(name="Not Found", value={"detail": "Not found."})],
            ),
        },
        examples=[
            OpenApiExample(name="Request Example", description="No request body required", value={}, request_only=True)
        ],
        auth=True,
    ),
    "partial_update": extend_schema(
        exclude=True,  # We don't allow partial updates for simulations
        description="Partial updates not supported for simulations",
    ),
    "update": extend_schema(
        exclude=True,  # We don't allow updates for simulations
        description="Updates not supported for simulations (immutable once created)",
    ),
}


# Custom schemas for additional endpoints if needed
class SimulationSchemaMixin:
    """Mixin to apply simulation schemas to views (placeholder).

    Note: avoid decorating plain mixin classes with `@extend_schema` because
    drf-spectacular expects view classes (which define `http_method_names`).
    Use `extend_schema` or `extend_schema_view` on actual view/viewset objects.
    """

    pass


# Apply schema to the viewset
# Create a decorated version of the viewset
DecoratedSimulationViewSet = extend_schema_view(**simulation_schema)(SimulationViewSet)


# Export for use in urls.py
__all__ = ["DecoratedSimulationViewSet", "simulation_schema"]
