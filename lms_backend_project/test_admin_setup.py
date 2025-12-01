# test_admin_setup.py

import os

import django
from django.contrib.admin.sites import site

# Create a test superuser if needed
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms_backend_project.settings")
django.setup()


print("Testing Admin Registration...")
print("=" * 60)

# Check which models are registered
registered_models = site._registry
print(f"Total models registered in admin: {len(registered_models)}")
print()

# List all registered models
for model, admin_class in registered_models.items():
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    print(f"✅ {app_label}.{model_name} -> {admin_class.__class__.__name__}")

print()
print("=" * 60)
print("Admin setup complete!")


User = get_user_model()

if not User.objects.filter(is_superuser=True).exists():
    print("\n⚠️  No superuser found. Create one with:")
    print("   uv run python manage.py createsuperuser")
else:
    print(f"\n✅ Superuser exists: {User.objects.filter(is_superuser=True).count()} superuser(s)")
