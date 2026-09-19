"""Pruebas del aprovisionamiento inicial del Administrador."""

from io import StringIO

import builtins
import getpass
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError

pytestmark = pytest.mark.django_db
CLAVE_TEMPORAL = "Clave-temporal-72!"


def test_bootstrap_creates_one_time_admin_without_printing_password(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _prompt: "administrador_inicial")
    monkeypatch.setattr(getpass, "getpass", lambda _prompt: CLAVE_TEMPORAL)
    output = StringIO()

    call_command(
        "bootstrap_admin",
        stdout=output,
    )

    admin = get_user_model().objects.get(username="administrador_inicial")
    assert admin.is_staff
    assert admin.is_active
    assert admin.force_password_change
    assert admin.check_password(CLAVE_TEMPORAL)
    assert list(admin.groups.values_list("name", flat=True)) == ["Administrador"]
    assert CLAVE_TEMPORAL not in output.getvalue()


def test_bootstrap_refuses_to_create_a_second_active_administrator(db, monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _prompt: "otro_administrador")
    monkeypatch.setattr(getpass, "getpass", lambda _prompt: CLAVE_TEMPORAL)
    admin = get_user_model().objects.create_user(
        username="administrador_existente", is_staff=True
    )
    admin.groups.add(Group.objects.get(name="Administrador"))

    with pytest.raises(CommandError, match="Ya existe un Administrador activo"):
        call_command("bootstrap_admin")
