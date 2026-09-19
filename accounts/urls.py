from django.urls import path

from .views import LoginView, LogoutView, PasswordChangeView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path(
        "password-change/",
        PasswordChangeView.as_view(),
        name="password_change",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
]
