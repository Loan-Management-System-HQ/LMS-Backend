from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .api_schema import schema_view
from .views import LoginView, LogoutView, ProfileView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # API documentation endpoints
    path("docs/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger_ui"),
    path("docs/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
    path("docs/schema/", schema_view.without_ui(cache_timeout=0), name="schema_json"),
]
