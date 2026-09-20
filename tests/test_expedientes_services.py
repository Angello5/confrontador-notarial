"""Contrato de servicios de hash, temporales y caché F4."""

import hashlib
from pathlib import Path

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


def test_hash_y_nombre_temporal_no_dependen_del_nombre_original(tmp_path):
    from expedientes.services import calcular_hash, crear_temporal

    archivo = tmp_path / "entrada-sintetica.txt"
    archivo.write_bytes(b"contenido ficticio")
    ruta = crear_temporal(archivo, "nombre-no-usado.txt", tmp_path)

    assert calcular_hash(archivo) == hashlib.sha256(b"contenido ficticio").hexdigest()
    assert Path(ruta).parent == tmp_path
    assert Path(ruta).name != "nombre-no-usado.txt"


@pytest.mark.parametrize("resultado", ["LISTO", "ERROR"])
def test_procesamiento_borra_temporal_en_exito_y_error(resultado, tmp_path):
    from expedientes.services import procesar_documento

    ruta = tmp_path / "temporal-ficticio.txt"
    ruta.write_bytes(b"entrada sintetica")
    procesar_documento(ruta, resultado_esperado=resultado)

    assert not ruta.exists()


def test_reutilizacion_de_cache_no_ejecuta_extractor_y_actualiza_uso():
    from expedientes.services import extraer_o_reutilizar

    llamadas = []
    resultado = extraer_o_reutilizar(
        "d" * 64,
        "ocr-ficticio-v1",
        lambda: llamadas.append(True) or "texto sintetico",
    )

    assert resultado.texto == "texto sintetico"
    assert llamadas == [True]


def test_version_distinta_crea_otra_entrada_de_cache():
    from expedientes.services import extraer_o_reutilizar

    extraer_o_reutilizar("e" * 64, "ocr-ficticio-v1", lambda: "primero")
    segundo = extraer_o_reutilizar("e" * 64, "ocr-ficticio-v2", lambda: "segundo")

    assert segundo.texto == "segundo"


def test_eliminar_documento_conserva_texto_extraido_compartido(usuario_ficticio):
    from expedientes.models import Documento, Expediente, TextoExtraido
    from expedientes.services import eliminar_documento

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-021", creado_por=usuario_ficticio
    )
    texto = TextoExtraido.objects.create(
        hash_archivo="5" * 64,
        version_extractor="ocr-ficticio-v1",
        texto="texto que sigue disponible",
        ultimo_uso_el=timezone.now(),
    )
    documento = Documento.objects.create(
        expediente=expediente,
        rol="FUENTE",
        nombre_original="eliminar-ficticio.txt",
        hash_archivo="5" * 64,
        tamano_bytes=5,
        texto_extraido=texto,
        estado="LISTO",
        subido_por=usuario_ficticio,
    )

    eliminar_documento(documento, confirmado=True)

    assert not Documento.objects.filter(pk=documento.pk).exists()
    assert TextoExtraido.objects.get(pk=texto.pk).texto == "texto que sigue disponible"
