from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        allowed_paths = {
            reverse("password_change"),
            reverse("logout"),
        }
        if (
            user.is_authenticated
            and user.force_password_change
            and request.path_info not in allowed_paths
        ):
            return redirect("password_change")
        return self.get_response(request)
