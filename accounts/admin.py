from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction

from .forms import AccountChangeForm, AccountCreationForm
from .models import User

ADMIN_ROLE = "Administrador"

if Group in admin.site._registry:
    admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    form = AccountChangeForm
    add_form = AccountCreationForm
    fieldsets = (
        (None, {"fields": ("username", "role", "is_active")}),
        (
            "Bloqueo de ingreso",
            {"fields": ("failed_login_attempts", "login_locked_until")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "role", "password1", "password2"),
            },
        ),
    )
    list_display = ("username", "role_name", "is_active", "failed_login_attempts")
    list_filter = ("is_active",)
    search_fields = ("username",)
    ordering = ("username",)
    readonly_fields = ("failed_login_attempts", "login_locked_until")
    actions = ("deactivate_accounts", "activate_accounts", "unlock_accounts")

    def role_name(self, obj):
        return obj.groups.filter(name__in=("Administrador", "Usuario")).first()

    role_name.short_description = "Rol"

    def get_fieldsets(self, request, obj=None):
        return self.add_fieldsets if obj is None else self.fieldsets

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            Group.objects.select_for_update().get(name=ADMIN_ROLE)
            if change:
                previous = User.objects.select_for_update().get(pk=obj.pk)
                previous_is_admin = previous.groups.filter(name=ADMIN_ROLE).exists()
                next_is_admin = form.cleaned_data["role"].name == ADMIN_ROLE
                if (
                    request.user.pk == previous.pk
                    and previous.is_active
                    and not obj.is_active
                ):
                    raise PermissionDenied("No puede desactivar su propia cuenta.")
                if (
                    previous.is_active
                    and previous_is_admin
                    and (not obj.is_active or not next_is_admin)
                    and not User.objects.filter(is_active=True, groups__name=ADMIN_ROLE)
                    .exclude(pk=previous.pk)
                    .exists()
                ):
                    raise PermissionDenied(
                        "No se puede retirar el último Administrador activo."
                    )
                if (
                    previous.is_active != obj.is_active
                    or previous_is_admin != next_is_admin
                ):
                    obj.session_version = previous.session_version + 1
            super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.groups.set([form.cleaned_data["role"]])

    @admin.action(description="Desactivar cuentas seleccionadas")
    def deactivate_accounts(self, request, queryset):
        self._set_active(request, queryset, False)

    @admin.action(description="Reactivar cuentas seleccionadas")
    def activate_accounts(self, request, queryset):
        self._set_active(request, queryset, True)

    def _set_active(self, request, queryset, is_active):
        try:
            with transaction.atomic():
                # ponytail: a single role-row lock serializes lifecycle changes; per-account locks if account volume grows.
                Group.objects.select_for_update().get(name=ADMIN_ROLE)
                accounts = list(
                    User.objects.select_for_update()
                    .filter(pk__in=queryset.values("pk"))
                    .order_by("pk")
                )
                if not is_active and any(
                    user.pk == request.user.pk for user in accounts
                ):
                    raise PermissionDenied("No puede desactivar su propia cuenta.")
                active_admin_count = User.objects.filter(
                    is_active=True, groups__name=ADMIN_ROLE
                ).count()
                removing = sum(
                    user.is_active
                    and user.groups.filter(name=ADMIN_ROLE).exists()
                    and not is_active
                    for user in accounts
                )
                if active_admin_count - removing < 1:
                    raise PermissionDenied(
                        "No se puede retirar el último Administrador activo."
                    )
                for user in accounts:
                    if user.is_active != is_active:
                        user.is_active = is_active
                        user.session_version += 1
                        user.save(update_fields=["is_active", "session_version"])
        except PermissionDenied as error:
            self.message_user(request, str(error), level=messages.ERROR)
            return
        message = "reactivaron" if is_active else "desactivaron"
        self.message_user(request, f"Se {message} {len(accounts)} cuentas.")

    @admin.action(description="Desbloquear intentos de ingreso")
    def unlock_accounts(self, request, queryset):
        with transaction.atomic():
            accounts = User.objects.select_for_update().filter(
                pk__in=queryset.values("pk")
            )
            for user in accounts:
                user.failed_login_attempts = 0
                user.login_locked_until = None
                user.save(update_fields=["failed_login_attempts", "login_locked_until"])
        self.message_user(request, "Se desbloquearon las cuentas seleccionadas.")
