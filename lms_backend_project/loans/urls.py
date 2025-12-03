from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"applications", views.LoanApplicationViewSet, basename="loanapplication")
router.register(r"loans", views.LoanViewSet, basename="loan")
router.register(r"installments", views.InstallmentViewSet, basename="installment")

urlpatterns = [
    path("", include(router.urls)),
    path("calculator/", views.LoanCalculatorView.as_view(), name="loan-calculator"),
    path("payments/", views.PaymentView.as_view(), name="make-payment"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard-stats"),
]
