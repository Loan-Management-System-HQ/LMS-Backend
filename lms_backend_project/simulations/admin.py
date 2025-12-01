# simulations/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import SimulationHeader, SimulationDetail


# Inline admin for SimulationDetail within SimulationHeader
class SimulationDetailInline(admin.TabularInline):
    model = SimulationDetail
    extra = 0
    readonly_fields = ("beginning_balance", "installment", "interest_payment", "principal_payment", "ending_balance")
    can_delete = False


# register SimulationHeader model with custom admin
@admin.register(SimulationHeader)
class SimulationHeaderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "interest_rate", "duration", "simulation_date")
    list_filter = ("simulation_date", "interest_rate")
    search_fields = ("user__email", "user__name", "id")
    readonly_fields = ("simulation_date", "monthly_payment", "total_interest", "total_payment")
    inlines = [SimulationDetailInline]

    fieldsets = (
        (None, {"fields": ("user", "amount", "duration", "interest_rate")}),
        (
            _("Calculated Results"),
            {"fields": ("monthly_payment", "total_interest", "total_payment"), "classes": ("collapse",)},
        ),
    )


# register SimulationDetail model with custom admin
@admin.register(SimulationDetail)
class SimulationDetailAdmin(admin.ModelAdmin):
    list_display = ("simulation", "installment_number", "beginning_balance", "installment", "ending_balance")
    list_filter = ("simulation", "is_prepayment", "is_delayed")
    search_fields = ("simulation__id",)
    readonly_fields = ("beginning_balance", "installment", "interest_payment", "principal_payment", "ending_balance")
