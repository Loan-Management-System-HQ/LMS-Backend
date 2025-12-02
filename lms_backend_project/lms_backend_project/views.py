# lms_backend_project/views.py
from django.http import JsonResponse


def handler404(request, exception):
    return JsonResponse(
        {"error": "Not found", "message": "The requested resource was not found", "status_code": 404}, status=404
    )


def handler500(request):
    return JsonResponse(
        {"error": "Server error", "message": "An internal server error occurred", "status_code": 500}, status=500
    )
