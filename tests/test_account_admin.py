"""Pruebas del Django admin de cuentas con datos ficticios."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.messages import get_messages
from django.contrib.staticfiles import finders
from django.core.exceptions import PermissionDenied
from django.templatetags.static import static
from django.test import Client, override_settings
from django.urls import reverse

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


def test_sin_bloqueo_por_intentos_fallidos(client, cliente_administrador):
    cuenta = get_user_model().objects.create_user(
        username="cuenta_sin_bloqueo", password=CLAVE_TEMPORAL
    )
    for _ in range(8):
        client.post(
            reverse("login"),
            {"username": "cuenta_sin_bloqueo", "password": "clave-erronea"},
        )

    assert client.login(username="cuenta_sin_bloqueo", password=CLAVE_TEMPORAL)
    assert not hasattr(cuenta, "failed_login_attempts")
    lista = cliente_administrador.get(reverse("admin:accounts_user_changelist"))
    assert "Desbloquear" not in lista.content.decode()


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
    assert 'class="peligro" value="Desactivar 1 cuenta"' in content
    assert 'class="closelink">Volver sin cambios</a>' in content
    user.refresh_from_db()
    assert user.is_active


def test_reactivation_confirmation_names_the_action_and_count(cliente_administrador):
    usuarios = [
        get_user_model().objects.create_user(
            username=f"cuenta_baja_{n}", is_active=False
        )
        for n in (1, 2)
    ]
    response = cliente_administrador.post(
        reverse("admin:accounts_user_changelist"),
        {
            "action": "activate_accounts",
            "_selected_action": [u.pk for u in usuarios],
            "index": 0,
        },
    )
    content = response.content.decode()
    assert 'type="submit" value="Reactivar 2 cuentas"' in content
    assert "peligro" not in content


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


@override_settings(ERP_NOMBRE="Notaría Ficticia", ERP_LOGO="")
def test_admin_login_shows_the_notary_brand(client):
    content = client.get(reverse("admin:login")).content.decode()

    assert (
        "<title>Iniciar sesión | Administración · Notaría Ficticia</title>" in content
    )
    assert '<span class="marca-sello" aria-hidden="true">NF</span>' in content
    assert '<span class="marca-nombre">Notaría Ficticia</span>' in content
    assert static("css/admin.css") in content


def test_admin_brand_stylesheet_is_local_and_light_only(cliente_administrador):
    content = cliente_administrador.get(
        reverse("admin:accounts_user_changelist")
    ).content.decode()
    hoja = Path(finders.find("css/admin.css")).read_text(encoding="utf-8")

    assert static("css/admin.css") in content
    assert "://" not in hoja
    assert "@import" not in hoja
    # Solo diseño claro: ni hoja oscura, ni script de tema, ni selector.
    assert "data-theme" not in hoja
    assert "prefers-color-scheme" not in hoja
    assert "dark_mode.css" not in content
    assert "admin/js/theme.js" not in content
    assert "theme-toggle" not in content
    # F49: fondo blanco, foco visible, movimiento opcional y sin !important.
    assert "--darkened-bg: #fff;" in hoja
    assert ":focus-visible" in hoja
    assert "@media (prefers-reduced-motion: reduce)" in hoja
    assert "!important" not in hoja


def test_admin_es_una_sola_pagina(cliente_administrador):
    lista = reverse("admin:accounts_user_changelist")

    for url in (reverse("admin:index"), "/admin/accounts/"):
        respuesta = cliente_administrador.get(url)
        assert respuesta.status_code == 302, url
        assert respuesta["Location"] == lista, url


def test_admin_vuelve_al_erp_y_a_la_lista_con_botones_claros(cliente_administrador):
    lista = reverse("admin:accounts_user_changelist")
    en_lista = cliente_administrador.get(lista).content.decode()
    nuevo = cliente_administrador.get(
        reverse("admin:accounts_user_add")
    ).content.decode()

    assert '<a class="admin-volver" href="/">' in en_lista
    assert "Volver al ERP" in en_lista
    assert "Ver el sitio" not in en_lista
    assert "Volver a usuarios" not in en_lista
    assert f'<a class="admin-volver-lista" href="{lista}">' in nuevo
    assert "Nuevo usuario" in nuevo
    assert "Volver al ERP" in nuevo


def test_admin_list_summarizes_accounts_with_links_to_filtered_lists(
    cliente_administrador,
):
    get_user_model().objects.create_user(username="cuenta_activa")
    get_user_model().objects.create_user(username="cuenta_inactiva", is_active=False)

    lista = reverse("admin:accounts_user_changelist")
    response = cliente_administrador.get(lista)
    content = response.content.decode()

    assert [
        (m["etiqueta"], m["valor"]) for m in response.context["resumen_cuentas"]
    ] == [
        ("Todas", 3),
        ("Activas", 2),
        ("Inactivas", 1),
    ]
    assert f'href="{lista}"' in content
    assert f'href="{lista}?is_active__exact=1"' in content
    assert f'href="{lista}?is_active__exact=0"' in content


def test_admin_without_nav_sidebar_and_with_spanish_columns(cliente_administrador):
    content = cliente_administrador.get(
        reverse("admin:accounts_user_changelist")
    ).content.decode()

    assert 'id="nav-sidebar"' not in content
    assert "Intentos fallidos" not in content
    assert "Failed login attempts" not in content


def test_admin_names_the_accounts_app_in_spanish(cliente_administrador):
    content = cliente_administrador.get(
        reverse("admin:accounts_user_changelist")
    ).content.decode()

    assert "Accounts" not in content


def _admin_con_rol_real():
    """Administrador con los permisos sembrados del rol, no con todos."""
    admin = get_user_model().objects.create_user(
        username="admin_rol_real", password=CLAVE_TEMPORAL, is_staff=True
    )
    admin.groups.add(Group.objects.get(name="Administrador"))
    cliente = Client()
    cliente.force_login(admin)
    return admin, cliente


def test_admin_elimina_una_cuenta_sin_historial(db):
    _, cliente = _admin_con_rol_real()
    cuenta = get_user_model().objects.create_user(username="cuenta_por_error")
    ficha = reverse("admin:accounts_user_change", args=[cuenta.pk])
    borrar = reverse("admin:accounts_user_delete", args=[cuenta.pk])

    assert f'href="{borrar}"' in cliente.get(ficha).content.decode()
    respuesta = cliente.post(borrar, {"post": "yes"})

    assert respuesta.status_code == 302
    assert not get_user_model().objects.filter(pk=cuenta.pk).exists()


def test_cuenta_con_historial_no_se_elimina_y_dice_por_que(db):
    from expedientes.models import Expediente

    _, cliente = _admin_con_rol_real()
    cuenta = get_user_model().objects.create_user(username="cuenta_con_kardex")
    Expediente.objects.create(codigo="K-FICTICIO-HISTORIAL", creado_por=cuenta)
    ficha = cliente.get(reverse("admin:accounts_user_change", args=[cuenta.pk]))
    borrar = reverse("admin:accounts_user_delete", args=[cuenta.pk])

    contenido = ficha.content.decode()
    assert f'href="{borrar}"' not in contenido
    assert "Desactívela para que ya no pueda ingresar." in contenido
    assert cliente.post(borrar, {"post": "yes"}).status_code == 403
    assert get_user_model().objects.filter(pk=cuenta.pk).exists()


def test_no_puede_eliminarse_a_si_mismo_ni_en_lote(db):
    admin, cliente = _admin_con_rol_real()
    borrar = reverse("admin:accounts_user_delete", args=[admin.pk])

    ficha = cliente.get(reverse("admin:accounts_user_change", args=[admin.pk]))
    assert "No puede eliminar su propia cuenta." in ficha.content.decode()
    assert cliente.post(borrar, {"post": "yes"}).status_code == 403
    lista = cliente.get(reverse("admin:accounts_user_changelist")).content.decode()
    assert "delete_selected" not in lista
