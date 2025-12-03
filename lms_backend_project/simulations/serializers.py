from decimal import Decimal

from rest_framework import serializers

from .models import SimulationDetail, SimulationHeader


class SimulationCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal("0.01"),
        error_messages={
            "required": "Loan amount is required.",
            "invalid": "Enter a valid number for amount.",
            "max_digits": "Amount cannot exceed 15 digits.",
            "max_decimal_places": "Amount cannot have more than 2 decimal places.",
            "min_value": "Amount must be greater than 0.",
        },
    )
    duration = serializers.IntegerField(
        min_value=1,
        max_value=360,
        error_messages={
            "required": "Loan duration is required.",
            "invalid": "Enter a valid integer for duration.",
            "min_value": "Duration must be at least 1 month.",
            "max_value": "Duration cannot exceed 360 months (30 years).",
        },
    )
    interest_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        # Allow 0% interest rate (zero is valid)
        min_value=Decimal("0.00"),
        max_value=Decimal("100.00"),
        error_messages={
            "required": "Interest rate is required.",
            "invalid": "Enter a valid number for interest rate.",
            "max_digits": "Interest rate cannot exceed 5 digits.",
            "max_decimal_places": "Interest rate cannot have more than 2 decimal places.",
            "min_value": "Interest rate must be greater than or equal to 0.",
            "max_value": "Interest rate cannot exceed 100%.",
        },
    )

    def validate(self, data):
        """Additional validation across multiple fields"""
        # Convert all values to proper types
        try:
            data["amount"] = Decimal(str(data["amount"]))
            data["duration"] = int(data["duration"])
            data["interest_rate"] = Decimal(str(data["interest_rate"]))
        except (ValueError, TypeError) as e:
            raise serializers.ValidationError(f"Invalid input data: {str(e)}")

        return data

    def to_internal_value(self, data):
        """Convert string inputs to proper types before validation"""
        # Handle potential string inputs from frontend
        internal_data = {}

        for field_name in ["amount", "duration", "interest_rate"]:
            if field_name in data:
                value = data[field_name]

                # Convert empty string to None
                if value == "":
                    internal_data[field_name] = None
                # Convert string to appropriate type
                elif isinstance(value, str):
                    try:
                        if field_name in ["amount", "interest_rate"]:
                            internal_data[field_name] = Decimal(value)
                        elif field_name == "duration":
                            internal_data[field_name] = int(float(value))
                    except (ValueError, TypeError):
                        internal_data[field_name] = value  # Let validation handle error
                else:
                    internal_data[field_name] = value

        return super().to_internal_value(internal_data)


class SimulationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationDetail
        fields = [
            "installment_number",
            "beginning_balance",
            "installment",
            "interest_payment",
            "principal_payment",
            "ending_balance",
            "custom_payment",
            "is_prepayment",
            "is_delayed",
        ]
        read_only_fields = fields


class SimulationHeaderSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    details = SimulationDetailSerializer(many=True, read_only=True)

    class Meta:
        model = SimulationHeader
        fields = [
            "id",
            "user",
            "user_email",
            "amount",
            "duration",
            "interest_rate",
            "simulation_date",
            "monthly_payment",
            "total_interest",
            "total_payment",
            "details",
        ]
        read_only_fields = [
            "id",
            "user",
            "simulation_date",
            "monthly_payment",
            "total_interest",
            "total_payment",
            "details",
        ]


class AnonymousSimulationCreateSerializer(SimulationCreateSerializer):
    session_id = serializers.CharField(required=False, allow_blank=True)


class SimulationResultSerializer(serializers.Serializer):
    simulation_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, coerce_to_string=False)
    duration = serializers.IntegerField()
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, coerce_to_string=False)
    monthly_payment = serializers.DecimalField(max_digits=15, decimal_places=2, coerce_to_string=False)
    total_interest = serializers.DecimalField(max_digits=15, decimal_places=2, coerce_to_string=False)
    total_payment = serializers.DecimalField(max_digits=15, decimal_places=2, coerce_to_string=False)
    amortization_table = SimulationDetailSerializer(many=True)


# Alternative: ModelSerializer approach with explicit field definitions
class SimulationCreateModelSerializer(serializers.ModelSerializer):
    """Alternative using ModelSerializer with explicit field definitions"""

    class Meta:
        model = SimulationHeader
        fields = ["amount", "duration", "interest_rate"]

    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal("0.01"),
        coerce_to_string=False,
        help_text="Loan amount in currency (e.g., 10000.00)",
    )

    duration = serializers.IntegerField(min_value=1, max_value=360, help_text="Loan duration in months (e.g., 12)")

    interest_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.00"),
        max_value=Decimal("100.00"),
        coerce_to_string=False,
        help_text="Annual interest rate in percentage (e.g., 5.00 for 5%)",
    )

    def to_internal_value(self, data):
        """Convert incoming data to proper Python types"""
        # Handle string inputs by converting them
        converted_data = {}

        for field_name, field_value in data.items():
            if field_name in ["amount", "interest_rate"]:
                try:
                    # Try to convert string to float/decimal
                    converted_data[field_name] = float(field_value) if field_value is not None else None
                except (ValueError, TypeError):
                    converted_data[field_name] = field_value  # Let validation handle it
            elif field_name == "duration":
                try:
                    converted_data[field_name] = int(field_value) if field_value is not None else None
                except (ValueError, TypeError):
                    converted_data[field_name] = field_value
            else:
                converted_data[field_name] = field_value

        return super().to_internal_value(converted_data)
