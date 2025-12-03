"""
IGNORE TESTS FOR NOW
"""

# users/tests.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Customer, Staff

User = get_user_model()


class UserAPITestCase(APITestCase):
    def setUp(self):
        """Set up test data"""
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.profile_url = reverse("profile")
        self.logout_url = reverse("logout")
        self.refresh_url = reverse("token_refresh")

        # Test user data
        self.user_data = {
            "email": "testuser@example.com",
            "name": "Test User",
            "phone": "1234567890",
            "password": "testpass123",
            "password2": "testpass123",
        }

        # Existing user for login tests
        self.existing_user = User.objects.create_user(
            email="existing@example.com", name="Existing User", phone="9876543210", password="existingpass123"
        )
        self.existing_user.is_active = True
        self.existing_user.save()

    def test_user_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        # Check user data in response
        user_data = response.data["user"]
        self.assertEqual(user_data["email"], self.user_data["email"])
        self.assertEqual(user_data["name"], self.user_data["name"])
        self.assertEqual(user_data["phone"], self.user_data["phone"])

        # Check user was created in database
        self.assertTrue(User.objects.filter(email=self.user_data["email"]).exists())

    def test_user_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        data = self.user_data.copy()
        data["password2"] = "differentpassword"
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_user_registration_missing_fields(self):
        """Test registration with missing required fields"""
        # Test missing email
        data = self.user_data.copy()
        data.pop("email")
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test missing name
        data = self.user_data.copy()
        data.pop("name")
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        """Test successful user login"""
        data = {"email": "existing@example.com", "password": "existingpass123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {"email": "existing@example.com", "password": "wrongpassword"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_login_nonexistent_user(self):
        """Test login with non-existent user"""
        data = {"email": "nonexistent@example.com", "password": "somepassword"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_profile_authenticated(self):
        """Test retrieving user profile when authenticated"""
        # First login to get token
        login_data = {"email": "existing@example.com", "password": "existingpass123"}
        login_response = self.client.post(self.login_url, login_data, format="json")
        access_token = login_response.data["access"]

        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # Get profile
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "existing@example.com")
        self.assertEqual(response.data["name"], "Existing User")

    def test_get_user_profile_unauthenticated(self):
        """Test retrieving user profile without authentication"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_profile(self):
        """Test updating user profile"""
        # Login
        login_data = {"email": "existing@example.com", "password": "existingpass123"}
        login_response = self.client.post(self.login_url, login_data, format="json")
        access_token = login_response.data["access"]

        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # Update profile
        update_data = {"name": "Updated Name", "phone": "5555555555"}
        response = self.client.patch(self.profile_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Name")
        self.assertEqual(response.data["phone"], "5555555555")

        # Verify update in database
        user = User.objects.get(email="existing@example.com")
        self.assertEqual(user.name, "Updated Name")
        self.assertEqual(user.phone, "5555555555")

    def test_token_refresh(self):
        """Test refreshing access token"""
        # First login
        login_data = {"email": "existing@example.com", "password": "existingpass123"}
        login_response = self.client.post(self.login_url, login_data, format="json")
        refresh_token = login_response.data["refresh"]

        # Refresh token
        refresh_data = {"refresh": refresh_token}
        response = self.client.post(self.refresh_url, refresh_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_user_logout(self):
        """Test user logout"""
        # First login
        login_data = {"email": "existing@example.com", "password": "existingpass123"}
        login_response = self.client.post(self.login_url, login_data, format="json")
        refresh_token = login_response.data["refresh"]
        access_token = login_response.data["access"]

        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # Logout
        logout_data = {"refresh": refresh_token}
        response = self.client.post(self.logout_url, logout_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_create_staff_user(self):
        """Test creating a staff user through admin or API"""
        staff_user = User.objects.create_user(
            email="staff@example.com", name="Staff User", phone="1112223333", password="staffpass123", is_staff=True
        )

        # Create Staff profile
        staff_profile = Staff.objects.create(user=staff_user, role="LOAN_OFFICER")

        self.assertTrue(staff_user.is_staff)
        self.assertEqual(staff_profile.role, "LOAN_OFFICER")

    def test_create_customer(self):
        """Test creating a customer profile"""
        customer_user = User.objects.create_user(
            email="customer@example.com", name="Customer User", phone="4445556666", password="customerpass123"
        )

        # Create Customer profile
        customer_profile = Customer.objects.create(user=customer_user, status="ACTIVE")

        self.assertEqual(customer_profile.status, "ACTIVE")
        self.assertEqual(customer_profile.user.email, "customer@example.com")


class ModelTestCase(TestCase):
    def test_user_str_method(self):
        """Test User model string representation"""
        user = User.objects.create_user(email="test@example.com", name="Test User", password="testpass123")
        self.assertEqual(str(user), "Test User (test@example.com)")

    def test_staff_str_method(self):
        """Test Staff model string representation"""
        user = User.objects.create_user(email="staff@example.com", name="Staff User", password="staffpass123")
        staff = Staff.objects.create(user=user, role="LOAN_OFFICER")
        self.assertIn("Staff User", str(staff))
        self.assertIn("Loan Officer", str(staff))

    def test_customer_str_method(self):
        """Test Customer model string representation"""
        user = User.objects.create_user(email="customer@example.com", name="Customer User", password="customerpass123")
        customer = Customer.objects.create(user=user, status="ACTIVE")
        self.assertIn("Customer", str(customer))
        self.assertIn(str(customer.id)[:8], str(customer))
