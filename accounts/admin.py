from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import router, transaction
from django.db.models.deletion import Collector, ProtectedError, RestrictedError
from django.template.response import TemplateResponse
from django.contrib.admin import helpers
from django.urls import reverse

from .admin_site import resumen_cuentas
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
    list_display = ("username", "role_name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("username",)
    ordering = ("username",)
    actions = ("deactivate_accounts", "activate_accounts")

    def role_name(self, obj):
        return obj.groups.filter(name__in=ROLES).first()

    role_name.short_description = "Rol"

    def changelist_view(self, request, extra_context=None):
        # Única página del admin: el resumen de cuentas va sobre la lista.
        lista = reverse("admin:accounts_user_changelist")
        return super().changelist_view(
            request,
            {
                "title": "Usuarios",
                "resumen_cuentas": resumen_cuentas(lista),
                **(extra_context or {}),
            },
        )

    def get_fieldsets(self, request, obj=None):
        return self.add_fieldsets if obj is None else self.fieldsets

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is not None:
            form.operator = request.user
        return form

    def motivo_para_no_eliminar(self, request, obj):
        """Por qué no se puede eliminar `obj`, o None si se puede.

        Kardex, documentos, confrontaciones y correcciones guardan quién los hizo
        (PROTECT, auditoría inmutable): una cuenta con historial se desactiva.
        """
        if obj.pk == request.user.pk:
            return "No puede eliminar su propia cuenta."
        if (
            obj.is_active
            and obj.groups.filter(name=ADMIN_ROLE).exists()
            and not User.objects.filter(is_active=True, groups__name=ADMIN_ROLE)
            .exclude(pk=obj.pk)
            .exists()
        ):
            return "No se puede eliminar el último Administrador activo."
        try:
            Collector(using=router.db_for_write(User)).collect([obj])
        except (ProtectedError, RestrictedError):
            return (
                "Esta cuenta tiene historial (kardex, documentos o confrontaciones) "
                "que debe conservarse. Desactívela para que ya no pueda ingresar."
            )
        return None

    def has_delete_permission(self, request, obj=None):
        # Solo cuenta por cuenta (sin acción masiva) y solo si no tiene historial.
        if obj is None or not self.has_change_permission(request, obj):
            return False
        return self.motivo_para_no_eliminar(request, obj) is None

    def get_actions(self, request):
        acciones = super().get_actions(request)
        acciones.pop("delete_selected", None)
        return acciones

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, object_id)
        motivo = obj and self.motivo_para_no_eliminar(request, obj)
        return super().change_view(
            request,
            object_id,
            form_url,
            {"motivo_no_eliminar": motivo, **(extra_context or {})},
        )

    def delete_model(self, request, obj):
        # Revalida dentro de la transacción: otra sesión pudo cambiarla.
        with transaction.atomic():
            Group.objects.select_for_update().get(name=ADMIN_ROLE)
            motivo = self.motivo_para_no_eliminar(request, obj)
            if motivo:
                raise PermissionDenied(motivo)
            super().delete_model(request, obj)

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
