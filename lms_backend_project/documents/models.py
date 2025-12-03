# documents/models.py
import os
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify

User = get_user_model()


def user_document_path(instance, filename):
    """
    Generate file path for uploaded document.
    Files will be uploaded to: MEDIA_ROOT/documents/user_<id>/<uuid_filename>
    """
    # Get file extension
    name, ext = os.path.splitext(filename)

    # Clean the original filename (remove special characters, keep it safe)
    safe_name = slugify(name)  # Converts "My Document.pdf" to "my-document"

    # Generate unique identifier
    unique_id = uuid.uuid4().hex[:8]  # First 8 chars of UUID

    # Return path: documents/user_<user_id>/<unique_filename>
    return f"documents/user_{instance.uploaded_by.id}/{unique_id}_{safe_name}{ext}"


class Document(models.Model):
    DOCUMENT_TYPES = [
        ("GOVT_ID", "Government Photo ID"),
        ("PAYROLL", "Pay Slip"),
        ("CREDIT_HISTORY", "Credit History"),
        ("BANK_STATEMENT", "Bank Statement"),
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
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_documents",
        db_column="uploadedBy",
    )

    status = models.CharField(max_length=32, choices=DOCUMENT_STATUS, default="PENDING")
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, db_column="type")

    # currently using file stored locally, later will use online storage bucket (link)
    link = models.CharField(max_length=500, db_column="link", default="")  # URL or file path prod only
    file = models.FileField(upload_to=user_document_path, max_length=500, db_column="file", default="")  # dev only

    # Store original filename exactly as uploaded
    original_filename = models.CharField(max_length=255, default="", db_column="originalFilename")

    # File metadata
    file_size = models.IntegerField(default=0, db_column="fileSize")  # in bytes
    mime_type = models.CharField(max_length=100, default="application/octet-stream")

    # Rejection note from staff
    rejection_note = models.TextField(blank=True, default="", db_column="rejectionNote")

    # Link to loan application (optional)
    loan_application = models.ForeignKey(
        "loans.LoanApplication",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_documents",
        db_column="loanApplicationID",
    )

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True, db_column="uploadedAt")
    updated_at = models.DateTimeField(auto_now=True, db_column="updatedAt")

    class Meta:
        db_table = "document"

    def __str__(self):
        # for human readable representation
        return f"{self.get_document_type_display()} - {self.uploaded_by.name if self.uploaded_by else 'Unknown'}"

    def save(self, *args, **kwargs):
        """Auto-populate file metadata before saving"""
        is_new = self._state.adding  # Check if this is a new object

        if self.file and is_new:
            # File upload mode
            if not self.original_filename:
                self.original_filename = os.path.basename(self.file.name)

            # Set file size
            if hasattr(self.file, "size"):
                self.file_size = self.file.size

            # Set link to internal file path
            self.link = f"/media/{self.file.name}"

            # Detect MIME type
            if not self.mime_type or self.mime_type == "application/octet-stream":
                ext = os.path.splitext(self.file.name)[1].lower()
                mime_types = {
                    ".pdf": "application/pdf",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".doc": "application/msword",
                    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ".txt": "text/plain",
                    ".csv": "text/csv",
                }
                self.mime_type = mime_types.get(ext, "application/octet-stream")

        elif self.link and is_new and not self.file:
            # External link mode
            if not self.original_filename:
                # Extract filename from URL if possible
                filename = os.path.basename(self.link)
                if filename:
                    self.original_filename = filename
                else:
                    self.original_filename = f"{self.document_type}.file"

            # Try to determine MIME type from URL extension
            if not self.mime_type or self.mime_type == "application/octet-stream":
                ext = os.path.splitext(self.link)[1].lower()
                mime_types = {
                    ".pdf": "application/pdf",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".doc": "application/msword",
                    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                }
                self.mime_type = mime_types.get(ext, "application/octet-stream")

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete the actual file when document is deleted (only for file uploads)"""
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)

    # Properties to check storage mode
    @property
    def is_file_upload(self):
        """Check if document uses file upload"""
        return bool(self.file)

    @property
    def is_external_link(self):
        """Check if document uses external link"""
        return bool(self.link and not self.file)

    @property
    def storage_mode(self):
        """Get storage mode"""
        if self.file:
            return "FILE_UPLOAD"
        elif self.link:
            return "EXTERNAL_LINK"
        return "UNKNOWN"

    @property
    def file_url(self):
        """Get URL for accessing the file (works for both modes)"""
        if self.file:
            return self.file.url
        elif self.link:
            # Check if it's already a full URL
            if self.link.startswith(("http://", "https://")):
                return self.link
            # Assume it's a relative path
            return self.link
        return None

    @property
    def download_url(self):
        """Get URL for download"""
        return self.file_url

    @property
    def file_extension(self):
        """Get file extension from original filename"""
        if self.original_filename:
            return os.path.splitext(self.original_filename)[1].lower()
        return ""

    @property
    def is_approved(self):
        return self.status == "APPROVED"

    @property
    def is_rejected(self):
        return self.status == "REJECTED"

    @property
    def is_pending(self):
        return self.status == "PENDING"

    @property
    def document_type_display(self):
        return self.get_document_type_display()

    @property
    def status_display(self):
        return self.get_status_display()

    def get_download_response(self):
        """Prepare file download response (for file uploads only)"""
        if not self.file:
            return None

        from django.http import FileResponse

        response = FileResponse(self.file.open(), as_attachment=True)
        response["Content-Disposition"] = f'attachment; filename="{self.original_filename}"'
        response["Content-Type"] = self.mime_type
        response["Content-Length"] = self.file_size
        return response
