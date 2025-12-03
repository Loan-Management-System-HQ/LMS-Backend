from django.urls import include, path
from rest_framework.routers import DefaultRouter
from users.api_schema import schema_view

from . import views

router = DefaultRouter()
router.register(r"applications", views.LoanApplicationViewSet, basename="loanapplication")
router.register(r"loans", views.LoanViewSet, basename="loan")
router.register(r"installments", views.InstallmentViewSet, basename="installment")

urlpatterns = [
    path("", include(router.urls)),
    # API documentation endpoints for this app
    path("docs/", schema_view.with_ui("swagger", cache_timeout=0), name="loans-swagger-ui"),
    path("docs/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="loans-redoc"),
    path("docs/schema/", schema_view.without_ui(cache_timeout=0), name="loans-schema-json"),
    path("calculator/", views.LoanCalculatorView.as_view(), name="loan-calculator"),
    path("payments/", views.PaymentView.as_view(), name="make-payment"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard-stats"),
]
