# documents/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Document


# register Document model with custom admin
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "get_document_type_display", "uploaded_by", "status", "uploaded_at")
    list_filter = ("document_type", "status", "uploaded_at")
    search_fields = ("uploaded_by__email", "uploaded_by__name", "id")
    readonly_fields = ("uploaded_at", "updated_at", "file_size", "mime_type")

    fieldsets = (
        (None, {"fields": ("document_type", "status")}),
        (_("File Information"), {"fields": ("file_name", "file_path", "file_size", "mime_type", "link")}),
        (
            _("Upload Details"),
            {"fields": ("uploaded_by", "requested_by", "reviewed_by", "review_notes", "reviewed_at")},
        ),
        (_("Timestamps"), {"fields": ("uploaded_at", "updated_at"), "classes": ("collapse",)}),
    )
