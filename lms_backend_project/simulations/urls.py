from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_schema import DecoratedSimulationViewSet

router = DefaultRouter()
router.register(r"simulations", DecoratedSimulationViewSet, basename="simulation")

urlpatterns = [
    path("", include(router.urls)),
]
