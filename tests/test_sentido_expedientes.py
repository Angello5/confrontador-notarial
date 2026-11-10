"""F61 · Capa de sentido en el ERP: worker, pantalla, interruptor y supresión.

Datos ficticios y modelos simulados (los de tests/test_sentido_nucleo.py).
"""
# ruff: noqa: F811  (fixtures reutilizados como parámetros)

import logging
from io import StringIO
from types import SimpleNamespace

import pytest
from django.core.management import call_command

from tests.test_expedientes_confrontacion import (  # noqa: F401 fixtures reutilizados
    crear_documento_listo,
    expediente_confrontacion,
)
from tests.test_manifiesto_auditoria import BORRADOR, RENIEC
from tests.test_sentido_nucleo import CLASIFICADORES, MINUTA, analizar, parecido

pytestmark = pytest.mark.django_db

PROYECTO = (
    BORRADOR
    + "\n"
    + MINUTA.replace("EL VENDEDOR SE OBLIGA", "EL VENDEDOR NO SE OBLIGA").replace(
        "MINUTA DE COMPRAVENTA.", "ESCRITURA PUBLICA."
    )
)
MODELOS = SimpleNamespace(
    analizar=analizar, parecido=parecido, clasificadores=CLASIFICADORES
)


@pytest.fixture
def activa(settings, tmp_path):
    from adaptadores.modelos_sentido import leer_manifiesto, _archivos

    for nombre, _ in _archivos(leer_manifiesto()):
        (tmp_path / nombre).write_bytes(b"")
    settings.SENTIDO_ACTIVO = True
    settings.SENTIDO_MODELOS_DIR = tmp_path
    return settings


@pytest.fixture
def corrida(expediente_confrontacion, crear_documento_listo):
    from expedientes.models import Corrida, Documento
    from expedientes.services import confrontar_automaticamente

    crear_documento_listo(
        expediente_confrontacion, Documento.CLIENTE, "reniec-ficticio.pdf", RENIEC
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-ficticia.txt",
        "ALBA LUMARIA ZAFIRO\n" + MINUTA,
    )
    crear_documento_listo(
        expediente_confrontacion, Documento.BORRADOR, "borrador-ficticio.txt", PROYECTO
    )
    confrontar_automaticamente()
    corrida = Corrida.objects.get()
    assert corrida.estado == Corrida.RESULTADO
    return corrida


def _pagina(client, usuario, corrida):
    client.force_login(usuario)
    ruta = f"/expedientes/{corrida.expediente_id}/documentos/{corrida.id_borrador}/resultado/"
    return client.get(ruta).content.decode()


def _estado(client, usuario, corrida):
    client.force_login(usuario)
    ruta = f"/expedientes/{corrida.expediente_id}/documentos/{corrida.id_borrador}/sentido/"
    respuesta = client.get(ruta, {"corrida": corrida.pk})
    assert respuesta["Cache-Control"] == "no-store"
    return respuesta.json()["estado"]


def test_con_el_interruptor_apagado_todo_queda_como_antes(
    client, usuario_ficticio, corrida
):
    from expedientes import sentido
    from expedientes.models import AnalisisSentido

    assert sentido.analizar_pendientes(modelos=MODELOS) == 0
    assert not AnalisisSentido.objects.exists()
    assert 'id="sentido-titulo"' not in _pagina(client, usuario_ficticio, corrida)
    assert _estado(client, usuario_ficticio, corrida) == "INACTIVA"


def test_analiza_la_corrida_sin_tocar_sus_hallazgos(
    client, usuario_ficticio, corrida, activa
):
    from expedientes import sentido
    from expedientes.models import AnalisisSentido, Corrida

    pagina = _pagina(client, usuario_ficticio, corrida)
    assert "Analizando el sentido de las cláusulas" in pagina
    assert "sondeoSentido" in pagina
    assert _estado(client, usuario_ficticio, corrida) == "PENDIENTE"

    huella, hallazgos = corrida.huella, corrida.hallazgos
    assert sentido.analizar_pendientes(modelos=MODELOS) == 1
    assert sentido.analizar_pendientes(modelos=MODELOS) == 0  # no repite

    analisis = AnalisisSentido.objects.get(corrida=corrida)
    assert analisis.estado == AnalisisSentido.LISTO
    assert [(a["nivel"], a["tipo"]) for a in analisis.anotaciones] == [
        ("OBSERVACION", "CONTRADICE")
    ]
    assert analisis.version_modelos.startswith("2026-10-22+")
    assert len(analisis.huella) == 64
    vuelta = Corrida.objects.get(pk=corrida.pk)
    assert (vuelta.huella, vuelta.hallazgos) == (huella, hallazgos)

    pagina = _pagina(client, usuario_ficticio, corrida)
    assert "Contradice la minuta" in pagina
    assert "1 observación" in pagina
    assert "Dice minuta" in pagina and "EL VENDEDOR NO SE OBLIGA" in pagina
    # F69: se ve lo que cambia; la cláusula completa queda plegada.
    assert "<mark>NO</mark>" in pagina
    assert '<details class="sentido-completo">' in pagina
    assert "Ver cláusula completa" in pagina
    assert 'data-seccion="SENTIDO"' in pagina  # también en el informe
    assert _estado(client, usuario_ficticio, corrida) == "LISTO"


def test_mismo_resultado_en_dos_analisis(corrida, activa):
    from expedientes import sentido
    from expedientes.models import AnalisisSentido

    sentido.analizar(corrida, MODELOS)
    primera = AnalisisSentido.objects.get()
    primera.delete()
    sentido.analizar(corrida, MODELOS)
    assert AnalisisSentido.objects.get().huella == primera.huella


def test_el_worker_analiza_despues_de_confrontar(corrida, activa, monkeypatch):
    from expedientes.models import AnalisisSentido

    monkeypatch.setattr("expedientes.sentido._cargar", lambda: MODELOS)
    call_command("procesar_documentos", stdout=StringIO())
    assert AnalisisSentido.objects.get(corrida=corrida).estado == "LISTO"


def test_un_fallo_queda_registrado_sin_texto_en_el_log(
    client, usuario_ficticio, corrida, activa, caplog
):
    from expedientes import sentido
    from expedientes.models import AnalisisSentido

    def falla(_textos):
        raise RuntimeError("EL VENDEDOR NO SE OBLIGA")

    with caplog.at_level(logging.ERROR):
        assert (
            sentido.analizar(
                corrida, SimpleNamespace(**{**vars(MODELOS), "analizar": falla})
            )
            == 1
        )
    analisis = AnalisisSentido.objects.get()
    assert (analisis.estado, analisis.anotaciones) == (AnalisisSentido.ERROR, [])
    assert "RuntimeError" in caplog.text and "VENDEDOR" not in caplog.text
    assert "No se pudo analizar el sentido" in _pagina(
        client, usuario_ficticio, corrida
    )


def test_sin_modelos_no_registra_y_avisa(
    client, usuario_ficticio, corrida, activa, monkeypatch, tmp_path
):
    from adaptadores.modelos_sentido import ModelosNoDisponibles
    from expedientes import sentido
    from expedientes.models import AnalisisSentido

    def sin_modelos():
        raise ModelosNoDisponibles("e5.onnx: no está")

    monkeypatch.setattr("expedientes.sentido._cargar", sin_modelos)
    assert sentido.analizar_pendientes() == 0
    assert not AnalisisSentido.objects.exists()
    activa.SENTIDO_MODELOS_DIR = tmp_path / "vacia"
    assert "no está disponible en este equipo" in _pagina(
        client, usuario_ficticio, corrida
    )
    assert _estado(client, usuario_ficticio, corrida) == "NO_DISPONIBLE"


def test_sin_cambios_de_sentido(
    client, usuario_ficticio, expediente_confrontacion, crear_documento_listo, activa
):
    from expedientes import sentido
    from expedientes.models import Corrida, Documento
    from expedientes.services import confrontar_automaticamente

    crear_documento_listo(
        expediente_confrontacion, Documento.CLIENTE, "reniec-ficticio.pdf", RENIEC
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.MINUTA,
        "minuta-ficticia.txt",
        "ALBA LUMARIA ZAFIRO\n" + MINUTA,
    )
    crear_documento_listo(
        expediente_confrontacion,
        Documento.BORRADOR,
        "borrador-ficticio.txt",
        BORRADOR + "\n" + MINUTA,
    )
    confrontar_automaticamente()
    corrida = Corrida.objects.get()
    sentido.analizar_pendientes(modelos=MODELOS)
    assert "No se encontraron cambios de sentido" in _pagina(
        client, usuario_ficticio, corrida
    )


def test_transferencia_vehicular_no_lleva_seccion(corrida, activa):
    from expedientes import sentido
    from expedientes.models import Expediente

    Expediente.objects.filter(pk=corrida.expediente_id).update(
        tipo=Expediente.VEHICULAR
    )
    corrida.expediente.refresh_from_db()
    assert list(sentido.pendientes()) == []
    assert sentido.para_pantalla(corrida) is None


def test_supresion_borra_las_oraciones_y_conserva_la_huella(
    client, usuario_ficticio, corrida, activa
):
    from expedientes import sentido
    from expedientes.models import AnalisisSentido

    sentido.analizar(corrida, MODELOS)
    huella = AnalisisSentido.objects.get().huella
    call_command(
        "suprimir_texto_expediente", corrida.expediente.codigo, stdout=StringIO()
    )
    analisis = AnalisisSentido.objects.get()
    assert (analisis.estado, analisis.anotaciones, analisis.huella) == (
        "SUPRIMIDO",
        [],
        huella,
    )
    assert "se suprimió a solicitud" in _pagina(client, usuario_ficticio, corrida)


def test_estado_exige_sesion(client, corrida):
    ruta = f"/expedientes/{corrida.expediente_id}/documentos/{corrida.id_borrador}/sentido/"
    assert client.get(ruta, {"corrida": corrida.pk}).status_code == 302


def test_los_modelos_se_cargan_una_vez_por_proceso(activa, monkeypatch):
    from expedientes import sentido

    cargas = []
    monkeypatch.setattr(sentido, "_modelos", None)
    monkeypatch.setattr(
        "adaptadores.modelos_sentido.Modelos.cargar",
        classmethod(
            lambda cls, carpeta, hilos: cargas.append((carpeta, hilos)) or MODELOS
        ),
    )
    assert sentido._cargar() is sentido._cargar() is MODELOS
    assert cargas == [(activa.SENTIDO_MODELOS_DIR, activa.SENTIDO_HILOS)]


def test_verificar_modelos_informa_huellas(activa, monkeypatch):
    from django.core.management import CommandError

    with pytest.raises(CommandError, match="huella distinta"):
        call_command("verificar_modelos_sentido", stdout=StringIO())
    monkeypatch.setattr(
        "expedientes.management.commands.verificar_modelos_sentido.verificar",
        lambda carpeta: [],
    )
    salida = StringIO()
    call_command("verificar_modelos_sentido", stdout=salida)
    assert "Capa activa" in salida.getvalue()


def test_huella_depende_solo_de_las_anotaciones():
    from expedientes.sentido import huella

    anotaciones = [{"tipo": "CONTRADICE", "posicion": 0}]
    assert huella(anotaciones) == huella([{"posicion": 0, "tipo": "CONTRADICE"}])
    assert huella(anotaciones) != huella([])


def test_supresion_alcanza_a_otro_kardex_que_comparte_el_texto(
    corrida, activa, usuario_ficticio
):
    """El comando borra textos compartidos: también las anotaciones que los citan."""
    from expedientes import sentido
    from expedientes.models import AnalisisSentido, Corrida, Documento, Expediente
    from expedientes.services import confrontar_automaticamente

    otro = Expediente.objects.create(
        codigo="EXP-FICTICIO-F61-B", creado_por=usuario_ficticio
    )
    for documento in corrida.expediente.documentos.all():
        Documento.objects.create(
            expediente=otro,
            rol=documento.rol,
            nombre_original=documento.nombre_original,
            hash_archivo=documento.hash_archivo,
            tamano_bytes=documento.tamano_bytes,
            estado=documento.estado,
            texto_extraido=documento.texto_extraido,
            subido_por=usuario_ficticio,
        )
    confrontar_automaticamente()
    sentido.analizar(corrida, MODELOS)
    sentido.analizar(Corrida.objects.get(expediente=otro), MODELOS)
    call_command(
        "suprimir_texto_expediente", corrida.expediente.codigo, stdout=StringIO()
    )
    assert set(AnalisisSentido.objects.values_list("estado", flat=True)) == {
        "SUPRIMIDO"
    }
    assert not any(AnalisisSentido.objects.values_list("anotaciones", flat=True))


def test_supresion_durante_el_analisis_no_guarda_oraciones(corrida, activa):
    """Si el texto se suprime mientras los modelos trabajan, no se guarda nada de él."""
    from expedientes import sentido
    from expedientes.models import AnalisisSentido, TextoExtraido

    def suprime_a_mitad(textos):
        TextoExtraido.objects.update(texto="")
        return analizar(textos)

    assert (
        sentido.analizar(
            corrida, SimpleNamespace(**{**vars(MODELOS), "analizar": suprime_a_mitad})
        )
        == 1
    )
    analisis = AnalisisSentido.objects.get()
    assert (analisis.estado, analisis.anotaciones) == (AnalisisSentido.SUPRIMIDO, [])


def test_supresion_alcanza_corridas_cuyo_documento_ya_se_elimino(
    corrida, activa, usuario_ficticio
):
    """La corrida registra los textos que usó: aunque otro kardex ya no tenga el
    documento, sus anotaciones con ese texto también se borran."""
    from expedientes import sentido
    from expedientes.models import AnalisisSentido, Corrida, Documento, Expediente
    from expedientes.services import confrontar_automaticamente

    otro = Expediente.objects.create(
        codigo="EXP-FICTICIO-F61-C", creado_por=usuario_ficticio
    )
    copias = [
        Documento.objects.create(
            expediente=otro,
            rol=d.rol,
            nombre_original=d.nombre_original,
            hash_archivo=d.hash_archivo,
            tamano_bytes=d.tamano_bytes,
            estado=d.estado,
            texto_extraido=d.texto_extraido,
            subido_por=usuario_ficticio,
        )
        for d in corrida.expediente.documentos.all()
    ]
    confrontar_automaticamente()
    sentido.analizar(Corrida.objects.get(expediente=otro), MODELOS)
    Documento.objects.filter(pk__in=[d.pk for d in copias]).delete()
    call_command(
        "suprimir_texto_expediente", corrida.expediente.codigo, stdout=StringIO()
    )
    assert AnalisisSentido.objects.get().estado == "SUPRIMIDO"
