# documents/models.py
import uuid
from django.db import models


class Document(models.Model):
    DOCUMENT_TYPES = [
        ("GOVT_ID", "Government Photo ID"),
        ("PAYROLL", "Pay Slip"),
        ("CREDIT_HISTORY", "Credit History"),
        ("ADDRESS_PROOF", "Proof of Address"),
        ("OTHER", "Other"),
    ]

    DOCUMENT_STATUS = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    # Django PK convention, maps to 'documentID' in DB
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column="documentID")

    # ForeignKey with Django convention
    requested_by = models.ForeignKey(
        "users.Staff",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_documents",
        db_column="requestedBy",
    )
    uploaded_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, related_name="uploaded_documents", db_column="uploadedBy"
    )

    status = models.CharField(max_length=32, choices=DOCUMENT_STATUS, default="PENDING")
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, db_column="type")
    link = models.CharField(max_length=500, db_column="link")  # URL or file path

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "document"

    def __str__(self):
        # for human readable representation
        return f"{self.get_document_type_display()} - {self.uploaded_by.name if self.uploaded_by else 'Unknown'}"
