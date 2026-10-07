"""F42: los datos de los comparecientes van en la pestaña «Generales de ley»."""

import re

import pytest
from django.test import Client
from django.urls import reverse

from tests.test_correccion_expedientes import escenario as escenario
from tests.test_correccion_expedientes import directorios as directorios

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "campo",
    [
        "NOMBRE",
        "DNI",
        "ESTADO_CIVIL_DISCREPANTE",
        "GENERO",
        "RAZON_SOCIAL",
        "RUC",
        # Decisión del usuario (2026-10-07): partida y dirección también.
        "PARTIDA",
        "DIRECCION",
    ],
)
def test_datos_del_compareciente_son_generales_de_ley(campo):
    from expedientes.services import capa_de

    assert capa_de(campo) == "IDENTIDAD"


@pytest.mark.parametrize("campo", ["MONTO", "NUMERO_EN_LETRAS", "ANEXO", "CORRELATIVO"])
def test_datos_del_acto_siguen_en_datos(campo):
    from expedientes.services import capa_de

    assert capa_de(campo) == "REGLA"


def test_pantalla_agrupa_el_nombre_en_generales_de_ley(escenario, usuario_ficticio):
    from expedientes.services import confrontar_borrador, registrar_corrida

    expediente, borrador, _ = escenario
    registrar_corrida(
        expediente,
        borrador,
        usuario_ficticio,
        confrontar_borrador(expediente, borrador),
    )
    cliente = Client()
    cliente.force_login(usuario_ficticio)
    html = cliente.get(
        reverse("documento_resultado", args=[expediente.pk, borrador.pk])
    ).content.decode()

    assert re.search(r'role="tab"[^>]*>Generales de ley<', html)
    assert not re.search(r'role="tab"[^>]*>Identidad<', html)
    assert re.search(r'data-capa="IDENTIDAD"[^>]*data-campo="Nombre"', html)
    assert not re.search(r'data-capa="REGLA"[^>]*data-campo="Nombre"', html)
