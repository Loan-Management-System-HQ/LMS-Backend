import os
import urllib.parse

from django.utils import timezone
from rest_framework import serializers
from users.serializers import StaffSerializer, UserSerializer

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    """Main serializer for Document model"""

    requested_by = StaffSerializer(read_only=True)
    uploaded_by = UserSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    document_type_display = serializers.CharField(source="get_document_type_display", read_only=True)
    file_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    is_approved = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    is_pending = serializers.SerializerMethodField()
    stored_filename = serializers.SerializerMethodField()
    storage_mode = serializers.SerializerMethodField()
    is_file_upload = serializers.SerializerMethodField()
    is_external_link = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "requested_by",
            "uploaded_by",
            "status",
            "status_display",
            "document_type",
            "document_type_display",
            "file",
            "link",
            "file_url",
            "download_url",
            "original_filename",
            "file_size",
            "file_extension",
            "mime_type",
            "uploaded_at",
            "updated_at",
            "is_approved",
            "is_rejected",
            "is_pending",
            "storage_mode",
            "is_file_upload",
            "is_external_link",
            "rejection_note",
            "stored_filename",
            "loan_application",
        ]
        read_only_fields = [
            "id",
            "requested_by",
            "uploaded_by",
            "status",
            "uploaded_at",
            "updated_at",
            "file_size",
            "mime_type",
            "original_filename",
            "file_extension",
            "storage_mode",
            "is_file_upload",
            "is_external_link",
            "rejection_note",
        ]

    def get_file_url(self, obj):
        """Get URL for accessing the file"""
        request = self.context.get("request")
        if obj.file:
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        elif obj.link:
            return obj.link
        return None

    def get_download_url(self, obj):
        """Get download URL"""
        return self.get_file_url(obj)

    def get_file_extension(self, obj):
        """Get file extension from original filename"""
        if obj.original_filename:
            return os.path.splitext(obj.original_filename)[1].lower()
        return ""

    def get_is_approved(self, obj):
        return obj.status == "APPROVED"

    def get_is_rejected(self, obj):
        return obj.status == "REJECTED"

    def get_is_pending(self, obj):
        return obj.status == "PENDING"

    def get_storage_mode(self, obj):
        """Get storage mode"""
        if obj.file:
            return "FILE_UPLOAD"
        elif obj.link:
            return "EXTERNAL_LINK"
        return "UNKNOWN"

    def get_is_file_upload(self, obj):
        """Check if document uses file upload"""
        return bool(obj.file)

    def get_is_external_link(self, obj):
        """Check if document uses external link"""
        return bool(obj.link and not obj.file)

    def validate(self, data):
        """Validate document data - ensure either file or link is provided"""
        has_file = "file" in data and data["file"]
        has_link = "link" in data and data.get("link")

        # Require either file or link, but not both
        if not has_file and not has_link:
            raise serializers.ValidationError({"error": "Either file or link must be provided"})

        # If both are provided, prioritize file upload
        if has_file and has_link:
            # Remove link if file is provided (file takes precedence)
            data.pop("link", None)

        # Validate file if provided
        if has_file:
            file = data["file"]

            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise serializers.ValidationError({"file": "File size exceeds maximum allowed size of 10MB"})

            # Check file extension
            allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".txt", ".csv"]
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    {"file": f'File type "{ext}" not allowed. Allowed types: {", ".join(allowed_extensions)}'}
                )

        # Validate link if provided (and no file)
        elif has_link:
            link = data["link"]

            # Basic URL validation
            if not (link.startswith("http://") or link.startswith("https://") or link.startswith("/")):
                raise serializers.ValidationError(
                    {"link": "Link must be a valid URL (http://, https://) or start with / for relative paths"}
                )

        return data

    def create(self, validated_data):
        """Create document with current user as uploaded_by"""
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["uploaded_by"] = request.user

        # Set original filename
        if "file" in validated_data:
            file = validated_data["file"]
            validated_data["original_filename"] = file.name
            if "display_filename" not in validated_data or not validated_data["display_filename"]:
                validated_data["display_filename"] = file.name

        elif "link" in validated_data:
            link = validated_data["link"]
            # Try to extract filename from URL
            filename = os.path.basename(urllib.parse.urlparse(link).path)
            if filename:
                validated_data["original_filename"] = filename
                if "display_filename" not in validated_data or not validated_data["display_filename"]:
                    validated_data["display_filename"] = filename
            else:
                validated_data["original_filename"] = f"{validated_data.get('document_type', 'document')}.file"
                if "display_filename" not in validated_data or not validated_data["display_filename"]:
                    validated_data["display_filename"] = validated_data["original_filename"]

        return super().create(validated_data)


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload (file or link)"""

    document_type = serializers.ChoiceField(choices=Document.DOCUMENT_TYPES)

    # Accept either file OR link
    file = serializers.FileField(required=False, allow_null=True)
    link = serializers.CharField(required=False, allow_null=True, max_length=500)

    # Optional loan application ID to link document to application
    loan_application_id = serializers.UUIDField(required=False, allow_null=True)

    display_filename = serializers.CharField(
        required=False, allow_blank=True, max_length=255, help_text="Optional custom display name"
    )

    def validate(self, data):
        """Validate that either file or link is provided"""
        has_file = "file" in data and data["file"] is not None
        has_link = "link" in data and data.get("link")

        if not has_file and not has_link:
            raise serializers.ValidationError({"error": "Either file or link must be provided"})

        if has_file:
            # File validation
            file = data["file"]
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise serializers.ValidationError({"file": "File size exceeds maximum allowed size of 10MB"})

            allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".txt", ".csv"]
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError({"file": f'File type "{ext}" not allowed'})

        elif has_link:
            # Link validation
            link = data["link"]
            if not (link.startswith("http://") or link.startswith("https://") or link.startswith("/")):
                raise serializers.ValidationError({"link": "Link must be a valid URL or start with /"})

        return data


# ===== Staff Action Serializers =====
# approve
class DocumentApproveSerializer(serializers.Serializer):
    """Simplified serializer for approving documents"""

    notes = serializers.CharField(
        required=False, allow_blank=True, max_length=500, help_text="Optional approval notes or comments"
    )


# reject
class DocumentRejectSerializer(serializers.Serializer):
    """Simplified serializer for rejecting documents"""

    reason = serializers.CharField(
        required=True, max_length=1000, help_text="Detailed reason for rejection (required) - will be sent to user"
    )

    notify_user = serializers.BooleanField(default=True, help_text="Whether to notify the user about the rejection")


# review
class DocumentReviewSerializer(serializers.Serializer):
    """For staff review (approve/reject) - REQUIRED"""

    action = serializers.ChoiceField(choices=["approve", "reject"])
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data["action"] == "reject" and not data.get("notes"):
            raise serializers.ValidationError("Notes are required when rejecting")
        return data


# request new
class DocumentRequestSerializer(serializers.Serializer):
    """Detailed serializer for staff to request documents from users"""

    user_id = serializers.UUIDField()
    document_type = serializers.ChoiceField(choices=Document.DOCUMENT_TYPES)
    description = serializers.CharField(
        required=False, allow_blank=True, max_length=500, help_text="Description of what document is needed and why"
    )

    priority = serializers.ChoiceField(
        choices=[
            ("LOW", "Low - Within 30 days"),
            ("MEDIUM", "Medium - Within 14 days"),
            ("HIGH", "High - Within 7 days"),
            ("URGENT", "Urgent - Within 24 hours"),
        ],
        default="MEDIUM",
        help_text="Priority level for this document request",
    )

    deadline = serializers.DateField(
        required=False, allow_null=True, help_text="Specific deadline for document submission (YYYY-MM-DD)"
    )

    instructions = serializers.CharField(
        required=False, allow_blank=True, max_length=1000, help_text="Specific instructions for the user"
    )

    notify_user = serializers.BooleanField(default=True, help_text="Whether to notify the user about this request")

    allow_multiple_uploads = serializers.BooleanField(
        default=False, help_text="Whether user can upload multiple files for this request"
    )

    required_fields = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        help_text="Required information fields in the document",
    )

    def validate(self, data):
        # Check if user exists
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            user = User.objects.get(id=data["user_id"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_id": "User not found."})

        data["user"] = user

        # Validate deadline is in the future
        if data.get("deadline") and data["deadline"] < timezone.now().date():
            raise serializers.ValidationError({"deadline": "Deadline must be in the future"})

        return data


# reset
class DocumentResetSerializer(serializers.Serializer):
    """Serializer for resetting document status to pending"""

    reason = serializers.CharField(required=True, max_length=500, help_text="Reason for resetting the document status")

    category = serializers.ChoiceField(
        choices=[
            ("DOCUMENT_EXPIRED", "Document Expired"),
            ("NEEDS_UPDATE", "Needs Updated Information"),
            ("ERROR", "Processing Error"),
            ("USER_REQUEST", "User Request"),
            ("SYSTEM_ERROR", "System Error"),
            ("OTHER", "Other"),
        ],
        required=False,
        default="OTHER",
        help_text="Category of reset reason",
    )

    notify_user = serializers.BooleanField(
        required=False, default=True, help_text="Whether to notify the user about the reset"
    )

    new_deadline = serializers.DateField(
        required=False, allow_null=True, help_text="New deadline for resubmission if applicable"
    )

    internal_notes = serializers.CharField(
        required=False, allow_blank=True, max_length=1000, help_text="Internal notes for staff reference"
    )

    def validate_new_deadline(self, value):
        """Validate new deadline is in the future"""
        if value and value < timezone.now().date():
            raise serializers.ValidationError("New deadline must be in the future")
        return value


class SimpleDocumentSerializer(serializers.ModelSerializer):
    """Simple serializer for basic document info (used by other apps)"""

    class Meta:
        model = Document
        fields = ["id", "original_filename", "document_type", "status", "uploaded_at"]


# ===== Statistics / Dashboard Serializers =====
class DocumentStatsSerializer(serializers.Serializer):
    """Serializer for document statistics responses"""

    total_documents = serializers.IntegerField()
    pending = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    by_document_type = serializers.DictField(
        child=serializers.DictField(), help_text="Mapping of document type to counts"
    )
    user_type = serializers.CharField()


class StaffDocumentDashboardSerializer(serializers.Serializer):
    """Serializer for staff dashboard response"""

    recent_activity = DocumentSerializer(many=True)
    urgent_pending = serializers.IntegerField()
    dashboard_actions = serializers.DictField(child=serializers.CharField())
