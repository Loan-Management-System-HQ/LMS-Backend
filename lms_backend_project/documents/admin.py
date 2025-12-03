from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["original_filename", "uploaded_by", "document_type", "status", "uploaded_at"]
    list_filter = ["document_type", "status", "uploaded_at"]
    search_fields = ["original_filename", "uploaded_by__username", "link"]
    readonly_fields = ["id", "uploaded_at", "updated_at", "rejection_note"]

    fieldsets = (
        ("Document Information", {"fields": ("uploaded_by", "requested_by", "document_type", "status")}),
        ("File Details", {"fields": ("original_filename", "link", "file", "file_size", "mime_type")}),
        ("Rejection", {"fields": ("rejection_note",)}),
        ("Loan Application", {"fields": ("loan_application",)}),
        ("Timestamps", {"fields": ("uploaded_at", "updated_at")}),
    )
