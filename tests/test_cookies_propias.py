"""F62: el ERP usa cookies propias para no chocar con otra app Django en el mismo host.

Los navegadores separan las cookies por host, no por puerto: otra app Django en
127.0.0.1:8001 recibía `sessionid` del ERP, no la reconocía y la borraba, y el
ERP volvía al login en el siguiente clic.
"""

import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_cookies_con_nombre_propio_del_erp():
    assert settings.SESSION_COOKIE_NAME == "confrontador_sesion"
    assert settings.CSRF_COOKIE_NAME == "confrontador_csrftoken"


def test_cookie_ajena_sessionid_no_cierra_la_sesion(client, usuario_ficticio):
    client.force_login(usuario_ficticio)
    # otra app Django en el mismo host deja (o borra) su propia «sessionid»
    client.cookies["sessionid"] = "de-otra-aplicacion"
    respuesta = client.get(reverse("expediente_lista"))
    assert respuesta.status_code == 200
    assert "sessionid" not in respuesta.cookies
