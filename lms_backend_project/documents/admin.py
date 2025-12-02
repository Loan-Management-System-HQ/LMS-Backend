from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["file_name", "uploaded_by", "document_type", "status", "uploaded_at"]
    list_filter = ["document_type", "status", "uploaded_at"]
    search_fields = ["file_name", "uploaded_by__username", "link"]
    readonly_fields = ["id", "uploaded_at", "updated_at"]

    fieldsets = (
        ("Document Information", {"fields": ("uploaded_by", "requested_by", "document_type", "status")}),
        ("File Details", {"fields": ("file_name", "link", "file_path", "file_size", "mime_type")}),
        ("Timestamps", {"fields": ("uploaded_at", "updated_at")}),
    )
