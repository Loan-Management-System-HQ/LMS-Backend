# loans/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import LoanApplication, UserLoanApplication, LoanApplicationDocument, Loan, CustomerLoan, Installment


# Inline admin for UserLoanApplication within LoanApplication
class UserLoanApplicationInline(admin.TabularInline):
    model = UserLoanApplication
    extra = 1
    autocomplete_fields = ["user"]


# Inline admin for LoanApplicationDocument within LoanApplication
class LoanApplicationDocumentInline(admin.TabularInline):
    model = LoanApplicationDocument
    extra = 1
    autocomplete_fields = ["document"]


# Register LoanApplication model with custom admin
@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "get_status_display", "amount", "duration", "interest_rate", "created_at")
    list_filter = ("status", "is_approved", "created_at")
    search_fields = ("id", "users__email", "users__name")
    readonly_fields = ("created_at", "updated_at", "credit_check_date")
    inlines = [UserLoanApplicationInline, LoanApplicationDocumentInline]

    fieldsets = (
        (None, {"fields": ("simulation", "status", "is_approved")}),
        (_("Loan Details"), {"fields": ("amount", "duration", "interest_rate", "purpose")}),
        (
            _("Credit Check"),
            {"fields": ("credit_score", "credit_check_notes", "credit_check_date"), "classes": ("collapse",)},
        ),
        (_("Timestamps"), {"fields": ("submitted_at", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


# Inline admin for CustomerLoan within Loan
class CustomerLoanInline(admin.TabularInline):
    model = CustomerLoan
    extra = 1
    autocomplete_fields = ["customer"]


# Inline admin for Installment within Loan
class InstallmentInline(admin.TabularInline):
    model = Installment
    extra = 0
    readonly_fields = ("due_date", "amount", "status", "payment_amount", "payment_date")
    can_delete = False


# Register Loan model with custom admin
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("id", "loan_application", "amount", "get_status_display", "disbursement_date", "current_balance")
    list_filter = ("status", "disbursement_date")
    search_fields = ("id", "loan_application__id", "customers__user__email")
    readonly_fields = ("created_at", "updated_at", "current_balance", "total_interest_paid", "total_principal_paid")
    inlines = [CustomerLoanInline, InstallmentInline]

    fieldsets = (
        (None, {"fields": ("loan_application", "approved_by", "status")}),
        (_("Loan Terms"), {"fields": ("amount", "duration", "interest_rate", "monthly_payment")}),
        (_("Dates"), {"fields": ("disbursement_date", "commencing_date", "maturity_date")}),
        (
            _("Current Status"),
            {"fields": ("current_balance", "total_interest_paid", "total_principal_paid"), "classes": ("collapse",)},
        ),
    )


# Inline admin for Installment within Loan
@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = ("loan", "installment_number", "due_date", "due_amount", "status", "paid_date")
    list_filter = ("status", "due_date")
    search_fields = ("loan__id", "loan__loan_application__id")
    readonly_fields = ("principal_due", "interest_due", "late_fee")

    fieldsets = (
        (None, {"fields": ("loan", "installment_number", "status")}),
        (_("Payment Details"), {"fields": ("due_date", "due_amount", "paid_amount", "paid_date")}),
        (
            _("Breakdown"),
            {
                "fields": (
                    "principal_due",
                    "interest_due",
                    "principal_paid",
                    "interest_paid",
                    "late_fee",
                    "late_fee_paid",
                ),
                "classes": ("collapse",),
            },
        ),
        (_("Notes"), {"fields": ("payment_notes",), "classes": ("collapse",)}),
    )


# Register junction tables if you want to manage them separately
@admin.register(CustomerLoan)
class CustomerLoanAdmin(admin.ModelAdmin):
    list_display = ("customer", "loan", "is_primary")
    list_filter = ("is_primary",)
    autocomplete_fields = ["customer", "loan"]


# Register LoanApplicationDocument model with custom admin
@admin.register(LoanApplicationDocument)
class LoanApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ("loan_application", "document", "is_required")
    autocomplete_fields = ["loan_application", "document"]
