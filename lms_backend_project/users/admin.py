# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Staff, Customer


# register User model with custom admin
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ("email", "name", "phone", "is_active", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff", "date_joined")
    search_fields = ("email", "name", "phone")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal Info"), {"fields": ("name", "phone", "verification_link")}),
        (
            _("Permissions"),
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "phone", "password1", "password2"),
            },
        ),
    )


# register Staff model with custom admin
@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("user", "get_role_display", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("user__email", "user__name")
    readonly_fields = ("created_at", "updated_at")


# register Customer model with custom admin
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("user", "get_status_display", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__email", "user__name")
    readonly_fields = ("created_at", "updated_at")
