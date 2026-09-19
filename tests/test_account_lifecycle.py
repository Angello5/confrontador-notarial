"""Pruebas de ciclo de vida de cuentas en Django admin."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import close_old_connections
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db
CLAVE_PRUEBA = "Clave-ficticia-81!"


@pytest.fixture
def administrador_con_cliente(db):
    admin = get_user_model().objects.create_user(
        username="administrador_ciclo", password=CLAVE_PRUEBA, is_staff=True
    )
    grupo = Group.objects.get(name="Administrador")
    grupo.permissions.set(
        Permission.objects.filter(content_type__app_label__in=["accounts", "auth"])
    )
    admin.groups.add(grupo)
    client = Client()
    client.force_login(admin)
    return admin, client


def test_deactivation_and_reactivation_invalidate_old_session(
    administrador_con_cliente,
):
    _admin, admin_client = administrador_con_cliente
    user = get_user_model().objects.create_user(
        username="cuenta_sesion", password=CLAVE_PRUEBA
    )
    user.groups.add(Group.objects.get(name="Usuario"))
    user_client = Client()
    user_client.force_login(user)
    session_hash = user.get_session_auth_hash()
    initial_version = user.session_version

    admin_client.post(
        reverse("admin:accounts_user_changelist"),
        {
            "action": "deactivate_accounts",
            "_selected_action": [user.pk],
            "index": 0,
            "post": "yes",
        },
    )
    user.refresh_from_db()
    assert not user.is_active
    assert user.session_version > initial_version
    assert user.get_session_auth_hash() != session_hash
    assert user_client.get(reverse("home")).status_code == 302

    admin_client.post(
        reverse("admin:accounts_user_changelist"),
        {
            "action": "activate_accounts",
            "_selected_action": [user.pk],
            "index": 0,
            "post": "yes",
        },
    )
    user.refresh_from_db()
    assert user.is_active
    assert user.session_version > initial_version
    assert user_client.get(reverse("home")).status_code == 302


def test_admin_cannot_disable_self_or_last_active_administrator(
    administrador_con_cliente,
):
    admin, admin_client = administrador_con_cliente
    other_admin = get_user_model().objects.create_user(
        username="ultimo_administrador", is_staff=True
    )
    other_admin.groups.add(Group.objects.get(name="Administrador"))

    self_response = admin_client.post(
        reverse("admin:accounts_user_changelist"),
        {
            "action": "deactivate_accounts",
            "_selected_action": [admin.pk],
            "index": 0,
            "post": "yes",
        },
    )
    other_response = admin_client.post(
        reverse("admin:accounts_user_changelist"),
        {
            "action": "deactivate_accounts",
            "_selected_action": [other_admin.pk],
            "post": "yes",
            "index": 0,
        },
    )

    admin.refresh_from_db()
    other_admin.refresh_from_db()
    assert self_response.status_code == other_response.status_code == 302
    assert admin.is_active
    assert not other_admin.is_active


@pytest.mark.django_db(transaction=True)
def test_concurrent_admin_deactivations_leave_an_active_administrator():
    grupo, _ = Group.objects.get_or_create(name="Administrador")
    perms = Permission.objects.filter(content_type__app_label__in=["accounts", "auth"])
    grupo.permissions.set(perms)
    administradores = []
    for nombre in ("admin_concurrente_1", "admin_concurrente_2"):
        user = get_user_model().objects.create_user(
            username=nombre, password=CLAVE_PRUEBA, is_staff=True
        )
        user.groups.add(grupo)
        administradores.append(user)

    def desactivar(actor, objetivo):
        try:
            client = Client()
            client.force_login(actor)
            return client.post(
                reverse("admin:accounts_user_changelist"),
                {
                    "action": "deactivate_accounts",
                    "_selected_action": [objetivo.pk],
                    "index": 0,
                    "post": "yes",
                },
            )
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(
            executor.map(
                lambda par: desactivar(*par),
                [administradores, administradores[::-1]],
            )
        )

    assert (
        get_user_model()
        .objects.filter(is_active=True, groups__name="Administrador")
        .exists()
    )
