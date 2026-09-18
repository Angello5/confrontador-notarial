import pytest
from django.contrib.auth.models import Group


@pytest.mark.django_db
def test_only_the_two_business_role_groups_are_available():
    assert set(Group.objects.values_list("name", flat=True)) == {
        "Administrador",
        "Usuario",
    }


def test_fictional_account_fixtures_have_their_expected_roles(
    administrador_ficticio, usuario_ficticio
):
    assert set(administrador_ficticio.groups.values_list("name", flat=True)) == {
        "Administrador"
    }
    assert set(usuario_ficticio.groups.values_list("name", flat=True)) == {"Usuario"}


def test_settings_require_a_secret_key():
    import os
    import subprocess
    import sys
    from pathlib import Path

    environment = os.environ.copy()
    environment.pop("DJANGO_SECRET_KEY", None)
    environment["DJANGO_SETTINGS_MODULE"] = "config.settings"
    result = subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode != 0
    assert "DJANGO_SECRET_KEY" in result.stderr
