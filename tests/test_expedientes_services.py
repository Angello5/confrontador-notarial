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


@pytest.mark.parametrize(
    ("estado_esperado", "salida"),
    [("LISTO", "texto extraido ficticio"), ("ERROR", RuntimeError)],
)
def test_procesamiento_real_borra_temporal_en_exito_y_error(
    estado_esperado, salida, usuario_ficticio, monkeypatch, tmp_path, caplog
):
    from expedientes.models import Documento, Expediente
    from expedientes.services import procesar_documento

    expediente = Expediente.objects.create(
        codigo=f"EXP-FICTICIO-{estado_esperado}", creado_por=usuario_ficticio
    )
    ruta = tmp_path / f"temporal-{estado_esperado.lower()}.txt"
    ruta.write_bytes(b"entrada sintetica")
    documento = Documento.objects.create(
        expediente=expediente,
        rol="BORRADOR",
        nombre_original="documento-ficticio.txt",
        hash_archivo=("a" if estado_esperado == "LISTO" else "b") * 64,
        tamano_bytes=ruta.stat().st_size,
        ruta_temporal=str(ruta),
        subido_por=usuario_ficticio,
    )
    if estado_esperado == "LISTO":
        monkeypatch.setattr("expedientes.services.extraccion.leer", lambda _: salida)
    else:

        def extractor_falla(_):
            raise salida("fallo sintetico")

        monkeypatch.setattr("expedientes.services.extraccion.leer", extractor_falla)

    procesar_documento(documento)
    documento.refresh_from_db()

    assert not ruta.exists()
    assert documento.ruta_temporal == ""
    assert documento.estado == estado_esperado
    if estado_esperado == "ERROR":
        assert f"id={documento.pk}" in caplog.text
        assert "tipo=RuntimeError" in caplog.text
        assert "fallo sintetico" not in caplog.text


def test_validar_archivo_rechaza_tamano_antes_de_leer(monkeypatch, settings):
    from expedientes.services import validar_archivo

    class ArchivoGrande:
        name = "documento-ficticio.txt"
        size = settings.EXPEDIENTES_MAX_FILE_SIZE + 1

        def chunks(self):
            raise AssertionError("no debe leer un archivo sobredimensionado")

    monkeypatch.setattr(
        "expedientes.services._archivo_bytes",
        lambda _: (_ for _ in ()).throw(AssertionError("no debe leer bytes")),
    )

    with pytest.raises(ValueError, match="tamaño máximo"):
        validar_archivo(ArchivoGrande())


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
