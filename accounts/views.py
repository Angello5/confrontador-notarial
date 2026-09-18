from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .forms import InitialPasswordChangeForm, LoginForm


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = "registration/login.html"

    def get_success_url(self):
        if self.request.user.force_password_change:
            return reverse_lazy("password_change")
        return super().get_success_url()


class PasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    form_class = InitialPasswordChangeForm
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        messages.success(self.request, "La clave se actualizó correctamente.")
        return super().form_valid(form)


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("login")
