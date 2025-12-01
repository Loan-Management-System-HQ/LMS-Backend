# loans/admin.py - FIXED VERSION
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import LoanApplication, UserLoanApplication, LoanApplicationDocument, Loan, CustomerLoan, Installment


class UserLoanApplicationInline(admin.TabularInline):
    model = UserLoanApplication
    extra = 1
    autocomplete_fields = ["user"]


class LoanApplicationDocumentInline(admin.TabularInline):
    model = LoanApplicationDocument
    extra = 1
    autocomplete_fields = ["document"]


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "get_status_display", "amount", "duration", "interest_rate", "created_at")
    list_filter = ("status", "is_approved", "created_at")
    search_fields = ("id", "users__email", "users__name")
    readonly_fields = ("created_at", "updated_at")  # REMOVED credit_check_date

    fieldsets = (
        (None, {"fields": ("simulation", "status", "is_approved")}),
        (_("Loan Details"), {"fields": ("amount", "duration", "interest_rate", "purpose")}),
        (
            _("Credit Check"),
            {
                "fields": ("credit_score", "credit_check_notes"),  # REMOVED credit_check_date
                "classes": ("collapse",),
            },
        ),
        (_("Timestamps"), {"fields": ("submitted_at", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


class CustomerLoanInline(admin.TabularInline):
    model = CustomerLoan
    extra = 1
    autocomplete_fields = ["customer"]


class InstallmentInline(admin.TabularInline):
    model = Installment
    extra = 0
    readonly_fields = ("due_date", "due_amount", "status", "payment_amount", "payment_date")
    can_delete = False


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "loan_application",
        "amount",
        "get_status_display",
        "disbursement_date",
    )  # REMOVED current_balance
    list_filter = ("status", "disbursement_date")
    search_fields = ("id", "loan_application__id", "customers__user__email")
    readonly_fields = ()  # EMPTY for now - remove all readonly_fields

    fieldsets = (
        (None, {"fields": ("loan_application", "approved_by", "status")}),
        (
            _("Loan Terms"),
            {
                "fields": ("amount", "duration", "interest_rate", "payment")  # FIXED: payment not monthly_payment
            },
        ),
        (
            _("Dates"),
            {
                "fields": ("disbursement_date", "commencing_date")  # REMOVED maturity_date
            },
        ),
    )


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = (
        "loan",
        "installment_number",
        "due_date",
        "due_amount",
        "status",
        "payment_date",
    )  # FIXED: payment_date not paid_date
    list_filter = ("status", "due_date")
    search_fields = ("loan__id", "loan__loan_application__id")
    readonly_fields = ()  # EMPTY - remove principal_due, interest_due, late_fee

    fieldsets = (
        (None, {"fields": ("loan", "installment_number", "status")}),
        (
            _("Payment Details"),
            {
                "fields": ("due_date", "due_amount", "payment_amount", "payment_date")  # FIXED
            },
        ),
    )


# REMOVE CustomerLoanAdmin and LoanApplicationDocumentAdmin for now
# @admin.register(CustomerLoan)
# @admin.register(LoanApplicationDocument)
