from django.urls import include, path
from rest_framework.routers import DefaultRouter
from users.api_schema import schema_view

from .views import SimulationViewSet

router = DefaultRouter()
router.register(r"simulations", SimulationViewSet, basename="simulation")

urlpatterns = [
    path("", include(router.urls)),
    # API documentation endpoints for this app
    path("docs/", schema_view.with_ui("swagger", cache_timeout=0), name="simulations-swagger-ui"),
    path("docs/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="simulations-redoc"),
    path("docs/schema/", schema_view.without_ui(cache_timeout=0), name="simulations-schema-json"),
]
