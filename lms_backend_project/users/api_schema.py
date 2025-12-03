from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .serializers import (
    UserLoginSerializer,
    UserRegisterSerializer,
    UserSerializer,
)

# --- Schemas for user/auth endpoints ---

# Register
register_schema = swagger_auto_schema(
    operation_description="Register a new user.",
    request_body=UserRegisterSerializer,
    responses={
        201: UserSerializer,
        400: "Bad Request",
    },
)


# Login
login_schema = swagger_auto_schema(
    operation_description="Login and retrieve access + refresh tokens.",
    request_body=UserLoginSerializer,
    responses={
        200: openapi.Response(
            description="Login successful",
            examples={"application/json": {"access": "<jwt_access_token>", "refresh": "<jwt_refresh_token>"}},
        ),
        401: "Unauthorized",
        400: "Bad Request",
    },
)


# Profile (GET / PUT)
profile_get_schema = swagger_auto_schema(
    operation_description="Get current user's profile.",
    responses={200: UserSerializer, 401: "Unauthorized"},
)

profile_put_schema = swagger_auto_schema(
    operation_description="Update current user's profile.",
    request_body=UserSerializer,
    responses={200: UserSerializer, 400: "Bad Request", 401: "Unauthorized"},
)


# Logout
logout_schema = swagger_auto_schema(
    operation_description="Logout the user (invalidate refresh token).",
    responses={200: "Logged out", 400: "Bad Request"},
)
