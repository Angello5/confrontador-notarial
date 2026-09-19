"""Pruebas del Django admin de cuentas con datos ficticios."""

from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from accounts.forms import AccountChangeForm

pytestmark = pytest.mark.django_db
CLAVE_TEMPORAL = "Clave-temporal-72!"


@pytest.fixture
def cliente_administrador(client, db):
    admin = get_user_model().objects.create_user(
        username="administrador_prueba", password=CLAVE_TEMPORAL, is_staff=True
    )
    grupo = Group.objects.get(name="Administrador")
    grupo.permissions.set(
        Permission.objects.filter(content_type__app_label__in=["accounts", "auth"])
    )
    admin.groups.add(grupo)
    client.force_login(admin)
    return client


def test_admin_creates_account_with_one_temporary_role_and_no_email(
    cliente_administrador,
):
    grupo_usuario = Group.objects.get(name="Usuario")
    response = cliente_administrador.post(
        reverse("admin:accounts_user_add"),
        {
            "username": "cuenta_nueva",
            "password1": CLAVE_TEMPORAL,
            "password2": CLAVE_TEMPORAL,
            "role": grupo_usuario.pk,
        },
    )

    user = get_user_model().objects.get(username="cuenta_nueva")
    assert response.status_code == 302
    assert user.email == ""
    assert user.is_active
    assert not user.is_staff
    assert not user.is_superuser
    assert user.force_password_change
    assert user.check_password(CLAVE_TEMPORAL)
    assert list(user.groups.values_list("name", flat=True)) == ["Usuario"]


def test_admin_account_form_uses_spanish_labels_and_minimum_fields(
    cliente_administrador,
):
    response = cliente_administrador.get(reverse("admin:accounts_user_add"))
    content = response.content.decode()

    assert "Nombre de usuario" in content
    assert "Clave temporal" in content
    assert "Confirmar clave temporal" in content
    assert "Rol" in content
    assert 'id="id_email"' not in content
    assert 'id="id_failed_login_attempts"' not in content
    assert 'id="id_login_locked_until"' not in content


def test_admin_rejects_role_tampering_and_superuser_escalation(
    cliente_administrador,
):
    grupo_extra, _ = Group.objects.get_or_create(name="Grupo ajeno")
    grupo_admin = Group.objects.get(name="Administrador")

    response = cliente_administrador.post(
        reverse("admin:accounts_user_add"),
        {
            "username": "cuenta_manipulada",
            "password1": CLAVE_TEMPORAL,
            "password2": CLAVE_TEMPORAL,
            "role": grupo_extra.pk,
            "groups": [grupo_admin.pk],
            "is_superuser": "on",
            "is_staff": "on",
        },
    )

    assert response.status_code == 200
    assert not get_user_model().objects.filter(username="cuenta_manipulada").exists()


def test_admin_can_unlock_account_from_changelist(cliente_administrador):
    blocked = get_user_model().objects.create_user(
        username="cuenta_bloqueada",
        failed_login_attempts=5,
        login_locked_until=timezone.now() + timedelta(minutes=15),
    )

    response = cliente_administrador.post(
        reverse("admin:accounts_user_changelist"),
        {"action": "unlock_accounts", "_selected_action": [blocked.pk], "index": 0},
    )

    blocked.refresh_from_db()
    action_messages = list(get_messages(response.wsgi_request))
    assert response.status_code == 302
    assert str(action_messages[0]) == "Se desbloquearon 1 cuenta."
    assert blocked.failed_login_attempts == 0
    assert blocked.login_locked_until is None


def test_admin_password_change_forces_new_password_and_revokes_sessions(
    cliente_administrador,
):
    target = get_user_model().objects.create_user(
        username="cuenta_clave", password=CLAVE_TEMPORAL
    )
    target.groups.add(Group.objects.get(name="Usuario"))
    target_client = Client()
    target_client.force_login(target)
    old_version = target.session_version

    response = cliente_administrador.post(
        reverse("admin:auth_user_password_change", args=[target.pk]),
        {
            "password1": "Clave-nueva-73!",
            "password2": "Clave-nueva-73!",
            "usable_password": "true",
        },
    )

    target.refresh_from_db()
    assert response.status_code == 302
    assert target.force_password_change
    assert target.session_version == old_version + 1
    assert target_client.get(reverse("home")).status_code == 302


def test_account_change_rejects_self_disable_in_validation(cliente_administrador):
    administrador = get_user_model().objects.get(username="administrador_prueba")
    response = cliente_administrador.post(
        reverse("admin:accounts_user_change", args=[administrador.pk]),
        {
            "username": administrador.username,
            "role": Group.objects.get(name="Administrador").pk,
        },
    )
    assert response.status_code == 200
    assert "No puede desactivar su propia cuenta" in response.content.decode()


def test_account_change_rejects_removing_last_administrator_in_validation(
    cliente_administrador,
):
    admin = get_user_model().objects.get(username="administrador_prueba")
    form = AccountChangeForm(
        data={
            "username": admin.username,
            "is_active": "on",
            "role": Group.objects.get(name="Usuario").pk,
        },
        instance=admin,
    )

    assert not form.is_valid()
    assert (
        "No se puede retirar el último Administrador activo." in form.errors["__all__"]
    )


def test_save_model_rejects_last_administrator_under_race(cliente_administrador):
    user_admin = get_user_model().objects.get(username="administrador_prueba")
    user_admin.is_active = True
    form = SimpleNamespace(
        cleaned_data={"role": Group.objects.get(name="Usuario")},
    )
    model_admin = admin.site._registry[get_user_model()]

    with pytest.raises(PermissionDenied, match="último Administrador"):
        model_admin.save_model(
            SimpleNamespace(user=SimpleNamespace(pk=None)),
            user_admin,
            form,
            True,
        )


def test_lifecycle_actions_require_confirmation(cliente_administrador):
    user = get_user_model().objects.create_user(username="cuenta_confirmacion")
    response = cliente_administrador.post(
        reverse("admin:accounts_user_changelist"),
        {"action": "deactivate_accounts", "_selected_action": [user.pk], "index": 0},
    )
    assert response.status_code == 200
    content = response.content.decode()
    assert "Confirme la desactivación" in content
    assert f"<li>{user.username}</li>" in content
    assert content.count("<h1") == 1
    assert reverse("admin:accounts_user_changelist") in content
    user.refresh_from_db()
    assert user.is_active


def test_action_message_uses_changed_count_and_singular(cliente_administrador):
    user = get_user_model().objects.create_user(username="cuenta_singular")
    response = cliente_administrador.post(
        reverse("admin:accounts_user_changelist"),
        {"action": "deactivate_accounts", "_selected_action": [user.pk], "index": 0},
    )
    response = cliente_administrador.post(
        reverse("admin:accounts_user_changelist"),
        {
            "action": "deactivate_accounts",
            "_selected_action": [user.pk],
            "index": 0,
            "post": "yes",
        },
    )
    assert response.status_code == 302
    assert (
        str(list(get_messages(response.wsgi_request))[-1]) == "Se desactivó 1 cuenta."
    )


def test_administrator_role_has_minimum_user_admin_permissions(db):
    permissions = set(
        Group.objects.get(name="Administrador")
        .permissions.filter(codename__in=("add_user", "change_user", "view_user"))
        .values_list("codename", flat=True)
    )

    assert permissions == {"add_user", "change_user", "view_user"}
