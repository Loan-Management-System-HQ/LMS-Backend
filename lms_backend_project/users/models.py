import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


# generic user manager class
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# User model
class User(AbstractBaseUser, PermissionsMixin):
    # Django best practice: use 'id' as PK field name
    # Maps to 'userID' in database
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column="userID")

    # User fields
    email = models.EmailField(unique=True, max_length=128)
    phone = models.CharField(max_length=32, blank=True, null=True)
    name = models.CharField(max_length=128)
    is_active = models.BooleanField(default=False, db_column="isActive")
    verification_link = models.CharField(max_length=255, blank=True, null=True, db_column="verificationLink")

    # Django required fields
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    # FIX: Add custom related_name to avoid conflict with Django Users
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to.",
        related_name="lms_user_set",  # CUSTOM related_name
        related_query_name="lms_user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="lms_user_set",  # CUSTOM related_name
        related_query_name="lms_user",
    )

    class Meta:
        db_table = "user"

    def __str__(self):
        return f"{self.name} ({self.email})"


# staff model extending User
class Staff(models.Model):
    ROLE_CHOICES = [
        ("LOAN_OFFICER", "Loan Officer"),
        ("ADMIN", "Administrator"),
        ("MANAGER", "Manager"),
    ]

    # Use 'id' as PK, maps to 'staffID' in DB
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column="staffID")

    # ForeignKey follows Django convention (lowercase model name)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff_profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="LOAN_OFFICER")

    # Timestamps (not in ERD but useful)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "staff"
        verbose_name_plural = "staff"

    def __str__(self):
        return f"{self.user.name} ({self.get_role_display()})"  # this is for human readability for role display


# Customer model extending User
class Customer(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
        ("SUSPENDED", "Suspended"),
        ("CLOSED", "Closed"),
    ]

    # Custom PK from ERD
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column="customerID")

    # One-to-one with User (as per ERD)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile", db_column="userID")

    # Status field from ERD
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE", db_column="status")

    # Timestamps (not in ERD but useful)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customer"

    def __str__(self):
        return f"Customer {self.id.hex[:8]} - {self.user.name}"
