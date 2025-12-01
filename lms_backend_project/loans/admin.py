# loans/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import CustomerLoan, Installment, Loan, LoanApplication, LoanApplicationDocument, UserLoanApplication


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
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("simulation", "status", "is_approved")}),
        (_("Loan Details"), {"fields": ("amount", "duration", "interest_rate", "purpose")}),
        (_("Credit Check"), {"fields": ("credit_score", "credit_check_notes"), "classes": ("collapse",)}),
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
    list_display = ("id", "loan_application", "amount", "get_status_display", "disbursement_date")
    list_filter = ("status", "disbursement_date")
    search_fields = ("id", "loan_application__id", "customers__user__email")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("loan_application", "approved_by", "status")}),
        (_("Loan Terms"), {"fields": ("amount", "duration", "interest_rate", "payment")}),
        (_("Dates"), {"fields": ("disbursement_date", "commencing_date")}),
    )


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = ("loan", "installment_number", "due_date", "due_amount", "status", "payment_date")
    list_filter = ("status", "due_date")
    search_fields = ("loan__id", "loan__loan_application__id")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("loan", "installment_number", "status")}),
        (_("Payment Details"), {"fields": ("due_date", "due_amount", "payment_amount", "payment_date")}),
        (_("Breakdown"), {"fields": ("principal_due", "interest_due", "late_fee"), "classes": ("collapse",)}),
    )


# Note: CustomerLoan and LoanApplicationDocument don't have is_primary/is_required fields
# So we use simple admin registration or skip them


@admin.register(CustomerLoan)
class CustomerLoanAdmin(admin.ModelAdmin):
    list_display = ("customer", "loan", "created_at")
    autocomplete_fields = ["customer", "loan"]


@admin.register(LoanApplicationDocument)
class LoanApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ("loan_application", "document", "created_at")
    autocomplete_fields = ["loan_application", "document"]
