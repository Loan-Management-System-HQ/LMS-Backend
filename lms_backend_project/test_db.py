# test_db.py
import sys
from pathlib import Path

# Get the project root directory (where manage.py is)
BASE_DIR = Path(__file__).resolve().parent
print(f"Project root (BASE_DIR): {BASE_DIR}")

# Add project root to Python path
sys.path.insert(0, str(BASE_DIR))

try:
    # Setup Django
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms_backend_project.settings")

    import django

    django.setup()

    from django.db import connection
    from decouple import config

    print("=" * 120)
    print("Testing Database Connection for Loan Management System")
    print("=" * 120)

    # Display environment info
    print(f"📁 Project root: {BASE_DIR}")
    print(f"⚙️  Settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")

    # Check .env file
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        print(f"✅ .env file: {env_path}")
    else:
        print(f"❌ .env file NOT found: {env_path}")

    # Test database connection
    try:
        with connection.cursor() as cursor:
            # Test 1: PostgreSQL version
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"\n📊 PostgreSQL: {version.split(',')[0]}")

            # Test 2: Database info
            cursor.execute("SELECT current_database(), current_user;")
            db_info = cursor.fetchone()
            print(f"📁 Database: {db_info[0]}")
            print(f"👤 User: {db_info[1]}")

            # Test 3: List tables
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()

            if tables:
                print(f"\n📋 Found {len(tables)} tables:")
                for i, (table_name,) in enumerate(tables[:15], 1):
                    print(f"  {i:2}. {table_name}")
                if len(tables) > 15:
                    print(f"  ... and {len(tables) - 15} more")
            else:
                print("\n📋 No tables found (this is normal for a fresh database)")

            # Test 4: Django migrations table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'django_migrations'
                )
            """)
            has_migrations = cursor.fetchone()[0]
            print(f"\n🔄 Django migrations table: {'✅ EXISTS' if has_migrations else '❌ NOT FOUND'}")

    except Exception as db_error:
        print(f"\n❌ Database error: {db_error}")
        print("\n💡 Troubleshooting tips:")
        print("1. Check if PostgreSQL is running: sudo systemctl status postgresql")
        print("2. Check .env file contains correct DB credentials")
        print("3. Test connection manually: psql -h localhost -U lms_user -d lms_db")

    print("=" * 120)
    print("Test complete!")
    print("=" * 120)

except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\n💡 Make sure you have activated the virtual environment:")
    print("   source .venv/bin/activate")
    print("   And installed requirements: uv add django psycopg2-binary python-decouple")

except django.core.exceptions.ImproperlyConfigured as e:
    print(f"\n❌ Django configuration error: {e}")
    print("\n💡 Check your settings.py file and .env configuration")

except Exception as e:
    print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")

    import traceback

    traceback.print_exc()
