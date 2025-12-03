from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SimulationViewSet

router = DefaultRouter()
router.register(r"simulations", SimulationViewSet, basename="simulation")

urlpatterns = [
    path("", include(router.urls)),
    # API documentation endpoints for this app
]
