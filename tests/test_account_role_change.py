"""Pruebas de cambios de rol y revocación de sesión."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_role_change_updates_staff_group_and_invalidates_existing_session(db):
    admin = get_user_model().objects.create_user(
        username="administrador_rol", is_staff=True
    )
    admin_group = Group.objects.get(name="Administrador")
    admin_group.permissions.set(
        Permission.objects.filter(content_type__app_label__in=["accounts", "auth"])
    )
    admin.groups.add(admin_group)
    admin_client = Client()
    admin_client.force_login(admin)

    user = get_user_model().objects.create_user(username="usuario_cambio_rol")
    user.groups.add(Group.objects.get(name="Usuario"))
    version = user.session_version
    auth_hash = user.get_session_auth_hash()
    user_client = Client()
    user_client.force_login(user)

    response = admin_client.post(
        reverse("admin:accounts_user_change", args=[user.pk]),
        {
            "username": user.username,
            "role": admin_group.pk,
            "is_active": "on",
        },
    )

    user.refresh_from_db()
    assert response.status_code == 302
    assert user.is_staff
    assert list(user.groups.values_list("name", flat=True)) == ["Administrador"]
    assert user.session_version > version
    assert user.get_session_auth_hash() != auth_hash
    assert user_client.get(reverse("home")).status_code == 302
