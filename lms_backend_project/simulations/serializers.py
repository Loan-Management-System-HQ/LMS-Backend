from rest_framework import serializers

from .models import SimulationDetail, SimulationHeader


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


class SimulationCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01)
    duration = serializers.IntegerField(min_value=1)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0.01)


class AnonymousSimulationCreateSerializer(SimulationCreateSerializer):
    session_id = serializers.CharField(required=False, allow_blank=True)


class SimulationResultSerializer(serializers.Serializer):
    simulation_id = serializers.UUIDField()
    monthly_payment = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_interest = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_payment = serializers.DecimalField(max_digits=15, decimal_places=2)
    amortization_table = SimulationDetailSerializer(many=True)
