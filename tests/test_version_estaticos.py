"""Las URL de los estáticos llevan versión para que el navegador no use CSS o JS viejo tras actualizar."""

import re

import pytest
from django.urls import reverse

from core.context_processors import version_estaticos


def test_la_version_cambia_cuando_cambia_un_estatico(tmp_path):
    (tmp_path / "css").mkdir()
    hoja = tmp_path / "css" / "ficticia.css"
    hoja.write_text(".a { color: red; }")
    antes = version_estaticos(tmp_path)

    hoja.write_text(".a { color: blue; }")
    version_estaticos.cache_clear()

    assert re.fullmatch(r"[0-9a-f]{10}", antes)
    assert version_estaticos(tmp_path) != antes


@pytest.mark.django_db
@pytest.mark.parametrize("ruta", ["home", "login"])
def test_la_hoja_del_erp_se_pide_con_version(client, usuario_ficticio, ruta):
    if ruta == "home":
        client.force_login(usuario_ficticio)

    html = client.get(reverse(ruta)).content.decode()

    assert re.search(r'css/erp\.css\?v=[0-9a-f]{10}"', html)


@pytest.mark.django_db
def test_la_hoja_del_admin_se_pide_con_version(client):
    html = client.get(reverse("admin:login")).content.decode()

    assert re.search(r'css/admin\.css\?v=[0-9a-f]{10}"', html)
