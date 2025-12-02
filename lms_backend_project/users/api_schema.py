# users/api_schema.py
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Loan Management System API",
        default_version="v1",
        description="""
        # Loan Management System API

        ## Authentication

        This API uses JWT (JSON Web Tokens) for authentication.

        ### Steps:
        1. **Register** a new user at `/api/auth/register/`
        2. **Login** at `/api/auth/login/` to get JWT tokens
        3. Use the **access token** in the Authorization header:

        ```
        Authorization: Bearer <your_access_token_here>
        ```

        ### Token Types:
        - **Access Token**: Short-lived (1 day), used for API requests
        - **Refresh Token**: Long-lived (7 days), used to get new access tokens

        ## Endpoints

        ### Authentication
        - `POST /api/auth/register/` - Register new user
        - `POST /api/auth/login/` - User login
        - `POST /api/auth/token/refresh/` - Refresh access token
        - `GET /api/auth/profile/` - Get user profile
        - `PUT /api/auth/profile/` - Update user profile
        - `POST /api/auth/logout/` - User logout

        ### Loan Management
        - *Coming soon* - Loan simulation
        - *Coming soon* - Loan application
        - *Coming soon* - Document upload
        - *Coming soon* - Payment tracking
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@lms.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
