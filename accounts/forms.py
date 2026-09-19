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
        )
        labels = {
            "username": "Nombre de usuario",
            "is_active": "Cuenta activa",
        }

    def __init__(self, *args, **kwargs):
        self.operator = kwargs.pop("operator", getattr(self, "operator", None))
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["role"].initial = self.instance.groups.filter(
                name__in=ROLES
            ).first()

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        if not role:
            return cleaned_data
        if (
            self.operator
            and self.operator.pk == self.instance.pk
            and self.instance.is_active
            and not cleaned_data.get("is_active")
        ):
            raise forms.ValidationError("No puede desactivar su propia cuenta.")
        was_admin = self.instance.groups.filter(name="Administrador").exists()
        will_be_admin = role.name == "Administrador"
        if (
            self.instance.is_active
            and was_admin
            and (not cleaned_data.get("is_active") or not will_be_admin)
            and not User.objects.filter(is_active=True, groups__name="Administrador")
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(
                "No se puede retirar el último Administrador activo."
            )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = self.cleaned_data["role"].name == "Administrador"
        if commit:
            user.save()
            user.groups.set([self.cleaned_data["role"]])
        return user
