from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)
from django.contrib.auth.models import Group

from .models import User

ROLES = ("Administrador", "Usuario")


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "El usuario o la clave no son correctos.",
        "inactive": "El usuario o la clave no son correctos.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].label = "Clave"
        self.fields[
            "password"
        ].help_text = "Si olvidó su clave, pida al Administrador una clave temporal."


class InitialPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = (
            "Clave actual (temporal)"
            if self.user.force_password_change
            else "Clave actual"
        )
        self.fields["new_password1"].label = "Clave nueva"
        self.fields["new_password2"].label = "Confirmar clave nueva"

    def save(self, commit=True):
        self.user.force_password_change = False
        return super().save(commit)


class AccountCreationForm(UserCreationForm):
    role = forms.ModelChoiceField(
        label="Rol",
        queryset=Group.objects.filter(name__in=ROLES).order_by("name"),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)
        labels = {"username": "Nombre de usuario"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Clave temporal"
        self.fields["password2"].label = "Confirmar clave temporal"

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data["role"]
        user.force_password_change = True
        user.is_staff = role.name == "Administrador"
        if commit:
            user.save()
            user.groups.set([role])
        return user


class AccountChangeForm(UserChangeForm):
    role = forms.ModelChoiceField(
        label="Rol",
        queryset=Group.objects.filter(name__in=ROLES).order_by("name"),
    )

    class Meta(UserChangeForm.Meta):
        model = User
        fields = (
            "username",
            "is_active",
            "failed_login_attempts",
            "login_locked_until",
        )
        labels = {
            "username": "Nombre de usuario",
            "is_active": "Cuenta activa",
            "failed_login_attempts": "Intentos fallidos de ingreso",
            "login_locked_until": "Bloqueo hasta",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["role"].initial = self.instance.groups.filter(
                name__in=ROLES
            ).first()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = self.cleaned_data["role"].name == "Administrador"
        if commit:
            user.save()
            user.groups.set([self.cleaned_data["role"]])
        return user
