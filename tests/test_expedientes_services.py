"""Contrato de servicios de hash, temporales y caché F4."""

import hashlib
import os
import stat
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
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


@pytest.mark.skipif(os.name == "nt", reason="los permisos POSIX no aplican en Windows")
@pytest.mark.parametrize("existe", [False, True])
def test_crear_temporal_restringe_el_directorio_al_usuario(tmp_path, settings, existe):
    from expedientes.services import crear_temporal

    destino = tmp_path / ("temporal-existente" if existe else "temporal-nuevo")
    if existe:
        destino.mkdir(mode=0o755)
    settings.EXPEDIENTES_TEMP_DIR = destino
    origen = tmp_path / "entrada-ficticia.txt"
    origen.write_bytes(b"contenido ficticio")

    crear_temporal(origen)

    assert stat.S_IMODE(destino.stat().st_mode) == 0o700


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
        monkeypatch.setattr(
            "expedientes.services.extraccion.leer_con_calidad", lambda _: salida
        )
    else:

        def extractor_falla(_):
            raise salida("fallo sintetico")

        monkeypatch.setattr(
            "expedientes.services.extraccion.leer_con_calidad", extractor_falla
        )

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


@pytest.mark.parametrize(
    ("nombre", "contenido"),
    [
        ("documento-ficticio.pdf", b"\x89PNG\r\n\x1a\ncontenido"),
        ("imagen-ficticia.png", b"%PDF-1.7 contenido"),
        ("documento-ficticio.docx", b"no es un zip ficticio"),
    ],
)
def test_validar_archivo_rechaza_firma_incompatible(nombre, contenido):
    from expedientes.services import validar_archivo

    with pytest.raises(ValueError, match="no coincide"):
        validar_archivo(SimpleUploadedFile(nombre, contenido))


def test_validar_archivo_rechaza_archivo_vacio():
    from expedientes.services import validar_archivo

    with pytest.raises(ValueError, match="vacío"):
        validar_archivo(SimpleUploadedFile("vacio-ficticio.txt", b""))


def test_registrar_documento_borra_temporal_si_la_fila_no_se_crea(
    usuario_ficticio, settings, tmp_path
):
    from expedientes.models import Documento, Expediente
    from expedientes.services import DocumentoDuplicado, registrar_documento

    destino = tmp_path / "temporales-ficticios"
    settings.EXPEDIENTES_TEMP_DIR = destino
    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-022", creado_por=usuario_ficticio
    )
    contenido = b"contenido duplicado ficticio"
    hash_archivo = hashlib.sha256(contenido).hexdigest()
    Documento.objects.create(
        expediente=expediente,
        rol="CLIENTE",
        nombre_original="anterior-ficticio.txt",
        hash_archivo=hash_archivo,
        tamano_bytes=len(contenido),
        subido_por=usuario_ficticio,
    )

    with pytest.raises(DocumentoDuplicado):
        registrar_documento(
            expediente,
            SimpleUploadedFile("duplicado-ficticio.txt", contenido),
            "CLIENTE",
            usuario_ficticio,
        )

    assert not list(destino.glob("*.tmp"))


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
        rol="CLIENTE",
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


def test_temporal_deduce_la_extension_del_origen_sin_nombre_explicito(tmp_path):
    """Sin la extension, extraccion.leer() lee el binario como texto plano."""
    from expedientes.services import crear_temporal

    origen = Path(__file__).parent / "fixtures" / "formatos" / "tabla.docx"

    ruta = crear_temporal(origen, destino=tmp_path)

    assert ruta.suffix == ".docx"
    assert ruta.stem != origen.stem
