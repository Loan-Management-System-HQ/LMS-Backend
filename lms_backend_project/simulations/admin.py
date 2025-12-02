from django.contrib import admin

from .models import SimulationDetail, SimulationHeader


class SimulationDetailInline(admin.TabularInline):
    model = SimulationDetail
    extra = 0
    readonly_fields = [
        "installment_number",
        "beginning_balance",
        "installment",
        "interest_payment",
        "principal_payment",
        "ending_balance",
    ]
    can_delete = False


@admin.register(SimulationHeader)
class SimulationHeaderAdmin(admin.ModelAdmin):
    list_display = ("id_short", "user", "amount", "duration", "interest_rate", "simulation_date")
    list_filter = ("simulation_date", "user")
    search_fields = ("user__email", "amount")
    readonly_fields = ("id", "monthly_payment", "total_interest", "total_payment", "simulation_date")
    inlines = [SimulationDetailInline]

    def id_short(self, obj):
        return str(obj.id)[:8]

    id_short.short_description = "ID"


@admin.register(SimulationDetail)
class SimulationDetailAdmin(admin.ModelAdmin):
    list_display = (
        "simulation_short",
        "installment_number",
        "beginning_balance",
        "installment",
        "interest_payment",
        "principal_payment",
        "ending_balance",
    )
    list_filter = ("simulation",)
    search_fields = ("simulation__id",)

    def simulation_short(self, obj):
        return str(obj.simulation.id)[:8]

    simulation_short.short_description = "Simulation ID"
