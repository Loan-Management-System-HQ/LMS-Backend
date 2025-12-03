from django.contrib import admin

from .models import CustomerLoan, Installment, Loan, LoanApplication, LoanApplicationDocument, UserLoanApplication


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ["id", "customer_name", "amount", "duration", "status", "created_at"]
    list_filter = ["status", "is_approved", "created_at"]
    search_fields = ["id", "amount"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(UserLoanApplication)
class UserLoanApplicationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "loan_application"]
    list_filter = ["loan_application__created_at"]
    search_fields = ["user__username", "loan_application__id"]


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ["id", "loan_application", "amount", "status", "disbursement_date"]
    list_filter = ["status", "disbursement_date"]
    search_fields = ["id", "amount"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = ["id", "loan", "installment_number", "due_amount", "due_date", "status"]
    list_filter = ["status", "due_date"]
    search_fields = ["loan__id", "installment_number"]
    readonly_fields = ["id", "created_at", "updated_at"]


# Register other models if needed
admin.site.register(LoanApplicationDocument)
admin.site.register(CustomerLoan)
