"""La lectura dudosa es visible y persistente, sin inventar discrepancias."""

import pytest
from django.test import Client
from django.urls import reverse

from tests.test_correccion_expedientes import escenario as escenario
from tests.test_correccion_expedientes import directorios as directorios

pytestmark = pytest.mark.django_db

CALIDAD = {
    "version": 1,
    "paginas": [
        {
            "pagina": 2,
            "metodo": "ocr",
            "confianza": 0.64,
            "requiere_revision": True,
            "motivos": ["baja_confianza"],
        }
    ],
}


def test_cache_bd_conserva_calidad_y_no_vuelve_a_extraer():
    from expedientes.services import extraer_o_reutilizar

    texto = extraer_o_reutilizar(
        "a" * 64, "ficticio", lambda: {"texto": "TEXTO FICTICIO", "calidad": CALIDAD}
    )
    texto.refresh_from_db()
    assert texto.texto == "TEXTO FICTICIO"
    assert texto.calidad == CALIDAD
    assert (
        extraer_o_reutilizar(
            "a" * 64, "ficticio", lambda: pytest.fail("cache omitida")
        ).pk
        == texto.pk
    )


def test_resultado_y_corrida_guardan_aviso(escenario, usuario_ficticio):
    from expedientes.services import (
        confrontar_borrador,
        registrar_corrida,
        resultado_de_corrida,
    )
    from expedientes.models import Corrida

    expediente, borrador, _ = escenario
    fuente = expediente.documentos.get(rol="CLIENTE").texto_extraido
    fuente.calidad = CALIDAD
    fuente.save(update_fields=["calidad"])
    resultado = confrontar_borrador(expediente, borrador)
    avisos = resultado["calidad_lectura"]
    assert any(a["paginas"] == [2] for a in avisos)
    guardado = registrar_corrida(expediente, borrador, usuario_ficticio, resultado)
    corrida = Corrida.objects.get(pk=guardado["corrida_id"])
    assert resultado_de_corrida(corrida)["calidad_lectura"] == avisos
    cliente = Client()
    cliente.force_login(usuario_ficticio)
    respuesta = cliente.get(
        reverse("documento_resultado", args=[expediente.pk, borrador.pk])
    )
    html = respuesta.content.decode()
    assert "Calidad de lectura" in html
    assert "Lectura dudosa" in html
    assert "página" in html
    # F68: en pantalla es una línea desplegable; el informe impreso la lleva completa.
    pantalla, informe = html.split('class="solo-impresion reporte"', 1)
    assert '<details class="aviso-compacto" data-tono="advertencia"' in pantalla
    assert "Lectura que necesita revisión" in pantalla.split("</summary>", 1)[0]
    assert '<section class="aviso" data-tono="advertencia"' not in pantalla
    assert '<section class="aviso" data-tono="advertencia"' in informe


def test_historicos_sin_calidad_no_se_declaran_verificados(escenario):
    from expedientes.services import confrontar_borrador

    expediente, borrador, _ = escenario
    resultado = confrontar_borrador(expediente, borrador)
    assert resultado["calidad_lectura"]
    assert all(a["tipo"] == "SIN_MEDICION" for a in resultado["calidad_lectura"])
