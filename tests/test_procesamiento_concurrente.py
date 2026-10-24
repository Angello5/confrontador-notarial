"""Locks reales entre conexiones SQL Server, sin documentos privados."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from threading import Event

import pytest
from django.db import connection, connections
from django.utils import timezone

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def roles():
    from django.contrib.auth.models import Group

    Group.objects.get_or_create(name="Usuario")
    Group.objects.get_or_create(name="Administrador")


def otra_conexion(funcion):
    def ejecutar():
        try:
            return funcion()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(ejecutar).result(timeout=10)


def test_lock_excluye_otro_proceso_y_se_libera():
    from expedientes.bloqueos import exclusivo

    def intentar():
        with exclusivo("test", "ficticio") as adquirido:
            return adquirido

    assert connection.vendor == "microsoft"
    with exclusivo("test", "ficticio") as adquirido:
        assert adquirido
        assert otra_conexion(intentar) is False
    assert otra_conexion(intentar) is True


def test_subir_el_borrador_no_encola_la_vista(usuario_ficticio, settings, tmp_path):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.db import transaction
    from expedientes.models import Documento, Expediente
    from expedientes.services import preparar_vistas, registrar_documento
    from tests.test_correccion_expedientes import _docx_bytes

    settings.EXPEDIENTES_TEMP_DIR = tmp_path / "temporales"
    settings.EXPEDIENTES_ORIGINALES_DIR = tmp_path / "originales"
    expediente = Expediente.objects.create(
        codigo="FICTICIO-COMMIT", creado_por=usuario_ficticio
    )
    with transaction.atomic():
        registrar_documento(
            expediente,
            SimpleUploadedFile(
                "ficticio.docx", _docx_bytes(tmp_path, "texto ficticio")
            ),
            Documento.BORRADOR,
            usuario_ficticio,
        )
        assert otra_conexion(preparar_vistas) == 0
    # La copia en PDF solo se genera cuando alguien abre la vista.
    assert not list(settings.EXPEDIENTES_TEMP_DIR.glob("vista-*"))


def test_no_recupera_documento_lento_con_lock_vivo(usuario_ficticio):
    from expedientes.bloqueos import exclusivo
    from expedientes.models import Documento, Expediente
    from expedientes.services import recuperar_documentos_vencidos

    expediente = Expediente.objects.create(
        codigo="FICTICIO-CONCURRENCIA", creado_por=usuario_ficticio
    )
    documento = Documento.objects.create(
        expediente=expediente,
        rol="CLIENTE",
        nombre_original="ficticio.txt",
        hash_archivo="a" * 64,
        tamano_bytes=1,
        subido_por=usuario_ficticio,
        estado="PROCESANDO",
        procesando_el=timezone.now() - timedelta(hours=1),
    )
    with exclusivo("documento", documento.pk):
        assert otra_conexion(recuperar_documentos_vencidos) == 0
    assert otra_conexion(recuperar_documentos_vencidos) == 1


def test_dos_consumidores_no_duplican_extraccion_y_reutilizan():
    from expedientes.services import extraer_o_reutilizar, ExtraccionOcupada

    leyendo, continuar = Event(), Event()
    llamadas = []

    def leer():
        llamadas.append(1)
        leyendo.set()
        assert continuar.wait(10)
        return "Texto exclusivamente ficticio"

    def primero():
        try:
            return extraer_o_reutilizar("f" * 64, "ficticio", leer).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as executor:
        futuro = executor.submit(primero)
        try:
            assert leyendo.wait(10)
            with pytest.raises(ExtraccionOcupada):
                extraer_o_reutilizar("f" * 64, "ficticio", leer)
        finally:
            continuar.set()
        pk = futuro.result(timeout=10)
    assert extraer_o_reutilizar("f" * 64, "ficticio", leer).pk == pk
    assert llamadas == [1]


@pytest.mark.parametrize("ronda", range(10))
def test_dos_workers_no_toman_el_mismo_documento(usuario_ficticio, ronda):
    from expedientes.models import Documento, Expediente
    from expedientes.services import tomar_pendiente

    expediente = Expediente.objects.create(
        codigo=f"FICTICIO-COLA-{ronda}", creado_por=usuario_ficticio
    )
    Documento.objects.bulk_create(
        Documento(
            expediente=expediente,
            rol="CLIENTE",
            nombre_original=f"ficticio-{numero}.txt",
            hash_archivo=f"{numero:064x}",
            tamano_bytes=1,
            subido_por=usuario_ficticio,
        )
        for numero in range(20)
    )

    def vaciar():
        tomados = []
        try:
            while documento := tomar_pendiente():
                tomados.append(documento.pk)
        finally:
            connections.close_all()
        return tomados

    with ThreadPoolExecutor(max_workers=2) as executor:
        workers = [executor.submit(vaciar) for _ in range(2)]
        tomados = [pk for worker in workers for pk in worker.result(timeout=60)]
    assert sorted(tomados) == sorted(Documento.objects.values_list("pk", flat=True))


def test_el_worker_continuo_sobrevive_a_un_corte_de_la_base(monkeypatch):
    from django.core.management import call_command
    from django.db import OperationalError

    from expedientes.management.commands import procesar_documentos

    vueltas = []

    def vencidos():
        vueltas.append(1)
        if len(vueltas) == 1:
            raise OperationalError("conexión cortada (ficticio)")
        return 0

    def esperar(_segundos):
        if len(vueltas) >= 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(procesar_documentos, "recuperar_documentos_vencidos", vencidos)
    monkeypatch.setattr(procesar_documentos, "sleep", esperar)
    call_command(
        "procesar_documentos", "--continuo", stdout=StringIO(), stderr=StringIO()
    )
    assert len(vueltas) == 2
