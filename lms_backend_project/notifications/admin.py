# notifications/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Notification


# register Notification model with custom admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "get_notification_type_display", "to_user", "is_read", "is_sent", "created_at")
    list_filter = ("notification_type", "is_read", "is_sent", "created_at")
    search_fields = ("to_user__email", "to_user__name", "message")
    readonly_fields = ("created_at", "read_at", "sent_at")
    list_select_related = ("to_user", "from_user")

    fieldsets = (
        (None, {"fields": ("notification_type", "to_user", "from_user", "is_read", "is_sent")}),
        (_("Content"), {"fields": ("subject", "message", "link")}),
        (_("Related Items"), {"fields": ("loan_application", "loan", "document"), "classes": ("collapse",)}),
        (_("Timestamps"), {"fields": ("created_at", "read_at", "sent_at"), "classes": ("collapse",)}),
    )
