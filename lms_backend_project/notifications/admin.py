# notifications/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "get_notification_type_display", "to_user", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("to_user__email", "to_user__name", "message")
    readonly_fields = ("created_at", "read_at")

    fieldsets = (
        (None, {"fields": ("notification_type", "to_user", "from_user", "is_read")}),
        (_("Content"), {"fields": ("subject", "message", "link")}),
        (_("Related Items"), {"fields": ("loan_application", "loan", "document"), "classes": ("collapse",)}),
        (_("Timestamps"), {"fields": ("created_at", "read_at"), "classes": ("collapse",)}),
    )
