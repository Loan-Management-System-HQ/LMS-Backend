"""
URL configuration for lms_backend_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView

# Swagger / OpenAPI
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Loan Management System API",
        default_version="v1",
        description="API documentation for Users, Loans, Documents, and Simulations",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Redirect root to docs
    path("", RedirectView.as_view(url="/api/docs/", permanent=False)),
    # Admin
    path("admin/", admin.site.urls),
    # API Authentication
    path("api/auth/", include("users.urls")),
    # API Documents
    path("api/documents/", include("documents.urls")),
    # Loans app
    path("api/loans/", include("loans.urls")),
    # Simulations endpoints (included so schema generation picks them up)
    path("api/simulations/", include("simulations.urls")),
    # Swagger/OpenAPI docs
    re_path(r"^api/schema(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("api/docs/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

# Add error handlers (optional but good for debugging)
handler404 = "lms_backend_project.views.handler404"
handler500 = "lms_backend_project.views.handler500"


# serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
