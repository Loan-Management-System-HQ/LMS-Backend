from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"documents", views.DocumentViewSet, basename="document")

urlpatterns = [
    path("", include(router.urls)),
    # API documentation endpoints for this app
    # Statistics
    path("stats/", views.DocumentStatsView.as_view(), name="document-stats"),
    # Staff dashboard
    path("staff/dashboard/", views.StaffDocumentDashboardView.as_view(), name="staff-dashboard"),
    # Additional endpoints (these are also available through the router)
    path("upload/", views.DocumentViewSet.as_view({"post": "upload"}), name="document-upload"),
    path("my-documents/", views.DocumentViewSet.as_view({"get": "my_documents"}), name="my-documents"),
    path("pending/", views.DocumentViewSet.as_view({"get": "pending"}), name="pending-documents"),
    path("approved/", views.DocumentViewSet.as_view({"get": "approved"}), name="approved-documents"),
    path("by-type/", views.DocumentViewSet.as_view({"get": "by_type"}), name="documents-by-type"),
]
