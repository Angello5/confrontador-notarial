from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.template.response import TemplateResponse
from django.contrib.admin import helpers

from .forms import AccountChangeForm, AccountCreationForm, ROLES
from .models import User

ADMIN_ROLE = ROLES[0]


class AdminTemporaryPasswordForm(AdminPasswordChangeForm):
    def save(self, commit=True):
        self.user.force_password_change = True
        self.user.session_version += 1
        return super().save(commit)


if Group in admin.site._registry:
    admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    form = AccountChangeForm
    add_form = AccountCreationForm
    change_password_form = AdminTemporaryPasswordForm
    fieldsets = ((None, {"fields": ("username", "role", "is_active")}),)
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
    actions = ("deactivate_accounts", "activate_accounts", "unlock_accounts")

    def role_name(self, obj):
        return obj.groups.filter(name__in=ROLES).first()

    role_name.short_description = "Rol"

    def get_fieldsets(self, request, obj=None):
        return self.add_fieldsets if obj is None else self.fieldsets

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is not None:
            form.operator = request.user
        return form

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
        return self._set_active(request, queryset, False)

    @admin.action(description="Reactivar cuentas seleccionadas")
    def activate_accounts(self, request, queryset):
        return self._set_active(request, queryset, True)

    def _set_active(self, request, queryset, is_active):
        if not request.POST.get("post"):
            return TemplateResponse(
                request,
                "admin/accounts/user/action_confirmation.html",
                {
                    **self.admin_site.each_context(request),
                    "title": "Confirme la reactivación"
                    if is_active
                    else "Confirme la desactivación",
                    "queryset": queryset,
                    "action_name": "activate_accounts"
                    if is_active
                    else "deactivate_accounts",
                    "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
                    "opts": self.opts,
                },
            )
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
                changed = []
                for user in accounts:
                    if user.is_active != is_active:
                        user.is_active = is_active
                        user.session_version += 1
                        user.save(update_fields=["is_active", "session_version"])
                        changed.append(user)
        except PermissionDenied as error:
            self.message_user(request, str(error), level=messages.ERROR)
            return
        action = "reactivó" if is_active else "desactivó"
        noun = "cuenta" if len(changed) == 1 else "cuentas"
        self.message_user(request, f"Se {action} {len(changed)} {noun}.")

    @admin.action(description="Desbloquear intentos de ingreso")
    def unlock_accounts(self, request, queryset):
        with transaction.atomic():
            accounts = User.objects.select_for_update().filter(
                pk__in=queryset.values("pk")
            )
            changed = []
            for user in accounts:
                if user.failed_login_attempts or user.login_locked_until:
                    changed.append(user)
                user.failed_login_attempts = 0
                user.login_locked_until = None
                user.save(update_fields=["failed_login_attempts", "login_locked_until"])
        noun = "cuenta" if len(changed) == 1 else "cuentas"
        self.message_user(request, f"Se desbloquearon {len(changed)} {noun}.")
