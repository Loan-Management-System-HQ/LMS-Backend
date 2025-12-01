import uuid

from django.db import models


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("DOCUMENT_REQUEST", "Document Request"),
        ("LOAN_APPROVAL", "Loan Approval"),
        ("INSTALLMENT_DUE", "Installment Due"),
        ("PAYMENT_CONFIRMATION", "Payment Confirmation"),
        ("SYSTEM", "System Notification"),
    ]

    # Django PK convention, maps to 'notificationID' in DB
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column="notificationID")

    # Relationships
    from_user = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, related_name="sent_notifications", db_column="fromID"
    )
    to_user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="received_notifications", db_column="toID"
    )

    # Notification content
    message = models.CharField(max_length=256)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, db_column="type")
    # Prefer empty string defaults for text fields instead of NULL
    link = models.CharField(max_length=500, default="", db_column="link")

    # ADD THESE MISSING FIELDS: [ERD doesn't have it]
    subject = models.CharField(max_length=255, default="")
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    # Status
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notification"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification {self.get_notification_type_display()} to {self.to_user.name}"
