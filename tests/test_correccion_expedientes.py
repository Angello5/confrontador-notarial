"""F21: conservación del borrador, confirmación única y registro (ficticio)."""

import hashlib
import stat
import zipfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from tests.test_correccion import crear_docx

pytestmark = pytest.mark.django_db

FUENTE = (
    "OPERACION FICTICIA DE PRUEBA.\n"
    "ALBA ZURBELIA LUMARIA, DE NACIONALIDAD PERUANA. DNI 90000001.\n"
    "PARTIDA ELECTRONICA N° 80000001. MONTO S/ 12,345.67.\n"
    "Esta clausula adicional describe una operacion completamente inventada "
    "para que el texto tenga el contexto habitual de un documento."
)
BORRADOR = FUENTE.replace("LUMARIA", "LUNARIA").replace("90000001", "90000002")


@pytest.fixture(autouse=True)
def directorios(settings, tmp_path):
    settings.EXPEDIENTES_TEMP_DIR = tmp_path / "temporales"
    settings.EXPEDIENTES_ORIGINALES_DIR = tmp_path / "originales"
    return settings


def _docx_bytes(tmp_path, texto):
    cuerpo = "".join(
        f"<w:p><w:r><w:t>{linea}</w:t></w:r></w:p>" for linea in texto.splitlines()
    )
    return crear_docx(tmp_path / "fuente-docx.docx", cuerpo).read_bytes()


def _texto(hash_archivo, texto):
    from expedientes.models import TextoExtraido

    return TextoExtraido.objects.create(
        hash_archivo=hash_archivo,
        version_extractor="extractor-ficticio-v1",
        texto=texto,
        ultimo_uso_el=timezone.now(),
    )


@pytest.fixture
def escenario(usuario_ficticio, tmp_path):
    from expedientes.models import Documento, Expediente
    from expedientes.services import registrar_documento

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-F21", creado_por=usuario_ficticio
    )
    for rol, nombre in (
        (Documento.MINUTA, "minuta-ficticia.txt"),
        (Documento.CLIENTE, "cliente-ficticio.txt"),
    ):
        hash_archivo = hashlib.sha256(nombre.encode()).hexdigest()
        Documento.objects.create(
            expediente=expediente,
            rol=rol,
            nombre_original=nombre,
            hash_archivo=hash_archivo,
            tamano_bytes=10,
            estado=Documento.LISTO,
            texto_extraido=_texto(hash_archivo, FUENTE),
            subido_por=usuario_ficticio,
        )
    contenido = _docx_bytes(tmp_path, BORRADOR)
    borrador = registrar_documento(
        expediente,
        SimpleUploadedFile("borrador-ficticio.docx", contenido),
        Documento.BORRADOR,
        usuario_ficticio,
    )
    borrador.estado = Documento.LISTO
    borrador.texto_extraido = _texto(borrador.hash_archivo, BORRADOR)
    borrador.save()
    return expediente, borrador, contenido


def _propuesta(expediente, borrador):
    from expedientes.services import confrontar_borrador

    resultado = confrontar_borrador(expediente, borrador)
    return resultado["correcciones"], resultado["huella"]


def test_solo_el_borrador_docx_se_conserva_inalterable(escenario, usuario_ficticio):
    from expedientes.models import Documento
    from expedientes.services import registrar_documento, ruta_original

    expediente, borrador, contenido = escenario
    ruta = ruta_original(borrador)
    assert ruta.read_bytes() == contenido
    assert stat.S_IMODE(ruta.stat().st_mode) == 0o400
    assert stat.S_IMODE(ruta.parent.stat().st_mode) == 0o700
    cliente = registrar_documento(
        expediente,
        SimpleUploadedFile("cliente-ficticio.docx", contenido),
        Documento.CLIENTE,
        usuario_ficticio,
    )
    assert not ruta_original(cliente).exists()


def test_confrontacion_propone_correcciones_con_fuente(escenario):
    expediente, borrador, _ = escenario
    correcciones, huella = _propuesta(expediente, borrador)
    pares = {(c["erroneo"], c["correcto"]) for c in correcciones}
    assert ("90000002", "90000001") in pares
    assert ("ALBA ZURBELIA LUNARIA", "ALBA ZURBELIA LUMARIA") in pares
    assert all(c["fuente"]["archivo"] == "minuta-ficticia.txt" for c in correcciones)
    assert len(huella) == 64


def test_vista_consolidada_con_casillas_y_un_boton(client, escenario, usuario_ficticio):
    expediente, borrador, _ = escenario
    client.force_login(usuario_ficticio)
    respuesta = client.post(
        reverse("documento_confrontar", args=(expediente.pk, borrador.pk))
    )
    html = respuesta.content.decode()
    assert "Correcciones propuestas" in html
    assert "minuta-ficticia.txt" in html
    assert html.count('name="aplicar"') >= 2
    assert html.count("checked") >= 2
    assert html.count("Aplicar correcciones") == 1
    assert 'name="confirmado"' in html
    assert "originales" not in html


def _aplicar(client, expediente, borrador, datos):
    return client.post(
        reverse("correcciones_aplicar", args=(expediente.pk, borrador.pk)), datos
    )


def test_sin_confirmacion_no_se_aplica_nada(client, escenario, usuario_ficticio):
    from expedientes.models import AplicacionCorreccion

    expediente, borrador, _ = escenario
    correcciones, huella = _propuesta(expediente, borrador)
    client.force_login(usuario_ficticio)
    respuesta = _aplicar(
        client,
        expediente,
        borrador,
        {"huella": huella, "aplicar": [c["id"] for c in correcciones]},
    )
    assert respuesta.status_code == 400
    assert not AplicacionCorreccion.objects.exists()
    assert [p.name for p in ruta_dir(borrador).iterdir()] == ["original.docx"]


def ruta_dir(borrador):
    from expedientes.services import ruta_original

    return ruta_original(borrador).parent


def test_huella_cambiada_no_aplica(client, escenario, usuario_ficticio):
    from expedientes.models import AplicacionCorreccion

    expediente, borrador, _ = escenario
    client.force_login(usuario_ficticio)
    respuesta = _aplicar(
        client, expediente, borrador, {"huella": "0" * 64, "confirmado": "1"}
    )
    assert respuesta.status_code == 400
    assert "Vuelva a confrontar" in respuesta.content.decode()
    assert not AplicacionCorreccion.objects.exists()


def test_confirmacion_aplica_registra_y_descarga(client, escenario, usuario_ficticio):
    from expedientes.models import AplicacionCorreccion

    expediente, borrador, contenido = escenario
    correcciones, huella = _propuesta(expediente, borrador)
    dni = next(c for c in correcciones if c["erroneo"] == "90000002")
    otras = sorted(c["id"] for c in correcciones if c is not dni)
    client.force_login(usuario_ficticio)
    antes = timezone.now()

    respuesta = _aplicar(
        client,
        expediente,
        borrador,
        {"huella": huella, "confirmado": "1", "aplicar": [dni["id"], "ajeno"]},
    )

    assert respuesta.status_code == 200
    aplicacion = AplicacionCorreccion.objects.get()
    assert aplicacion.confirmado_por == usuario_ficticio
    assert aplicacion.confirmado_el >= antes
    assert aplicacion.aplicadas == [dni["id"]]
    assert sorted(aplicacion.excluidas) == otras
    assert aplicacion.no_aplicadas == []
    assert aplicacion.huella_corrida == huella
    from expedientes.services import ruta_original

    assert ruta_original(borrador).read_bytes() == contenido
    html = respuesta.content.decode()
    descarga = reverse("correccion_descargar", args=(expediente.pk, aplicacion.pk))
    assert descarga in html

    archivo = client.get(descarga)
    assert archivo.status_code == 200
    assert "borrador-ficticio-corregido.docx" in archivo["Content-Disposition"]
    cuerpo = b"".join(archivo.streaming_content)
    assert hashlib.sha256(cuerpo).hexdigest() == aplicacion.corregido_hash
    ruta = ruta_dir(borrador) / "tmp.docx"
    ruta.write_bytes(cuerpo)
    with zipfile.ZipFile(ruta) as z:
        xml = z.read("word/document.xml").decode()
    assert "DNI 90000001." in xml
    assert "LUNARIA" in xml  # excluida


def test_aplicacion_es_inmutable(escenario, usuario_ficticio):
    from expedientes.models import AplicacionCorreccion

    _, borrador, _ = escenario
    aplicacion = AplicacionCorreccion.objects.create(
        borrador=borrador,
        huella_corrida="a" * 64,
        confirmado_por=usuario_ficticio,
        corregido_hash="b" * 64,
    )
    aplicacion.excluidas = ["x"]
    with pytest.raises(ValueError):
        aplicacion.save()
    with pytest.raises(ValueError):
        aplicacion.delete()


def test_permisos_y_csrf(client, escenario, usuario_ficticio):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    expediente, borrador, _ = escenario
    ajeno = get_user_model().objects.create_user(username="otro_ficticio")
    ajeno.groups.add(Group.objects.get(name="Usuario"))
    client.force_login(ajeno)
    assert (
        _aplicar(client, expediente, borrador, {"confirmado": "1"}).status_code == 403
    )
    assert (
        client.get(
            reverse("correcciones_aplicar", args=(expediente.pk, borrador.pk))
        ).status_code
        == 405
    )
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(usuario_ficticio)
    assert _aplicar(csrf, expediente, borrador, {"confirmado": "1"}).status_code == 403


def test_descarga_ajena_prohibida(client, escenario, usuario_ficticio):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    expediente, borrador, _ = escenario
    correcciones, huella = _propuesta(expediente, borrador)
    client.force_login(usuario_ficticio)
    _aplicar(
        client,
        expediente,
        borrador,
        {"huella": huella, "confirmado": "1", "aplicar": [correcciones[0]["id"]]},
    )
    from expedientes.models import AplicacionCorreccion

    descarga = reverse(
        "correccion_descargar",
        args=(expediente.pk, AplicacionCorreccion.objects.get().pk),
    )
    ajeno = get_user_model().objects.create_user(username="otro_ficticio")
    ajeno.groups.add(Group.objects.get(name="Usuario"))
    client.force_login(ajeno)
    assert client.get(descarga).status_code == 403


def test_borrador_sin_original_no_ofrece_aplicar(client, escenario, usuario_ficticio):
    from expedientes.services import ruta_original

    expediente, borrador, _ = escenario
    ruta_original(borrador).chmod(0o600)
    ruta_original(borrador).unlink()
    client.force_login(usuario_ficticio)
    html = client.post(
        reverse("documento_confrontar", args=(expediente.pk, borrador.pk))
    ).content.decode()
    assert "Correcciones propuestas" in html
    assert "Aplicar correcciones" not in html
    assert "no admite corrección automática" in html
    respuesta = _aplicar(
        client,
        expediente,
        borrador,
        {"huella": _propuesta(expediente, borrador)[1], "confirmado": "1"},
    )
    assert respuesta.status_code == 400


def test_eliminar_y_suprimir_borran_originales(escenario):
    from django.core.management import call_command

    from expedientes.services import eliminar_documento, ruta_original

    expediente, borrador, _ = escenario
    carpeta_expediente = ruta_original(borrador).parent.parent
    call_command("suprimir_texto_expediente", expediente.codigo)
    assert not carpeta_expediente.exists()

    ruta_original(borrador).parent.mkdir(parents=True)
    ruta_original(borrador).write_bytes(b"x")
    eliminar_documento(borrador, confirmado=True)
    assert not ruta_original(borrador).parent.exists()
