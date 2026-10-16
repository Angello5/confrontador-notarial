"""Contrato de comandos de limpieza y supresión F4."""

import os
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

pytestmark = pytest.mark.django_db


def test_limpiar_temporales_solo_elimina_huerfanos_antiguos(
    usuario_ficticio, tmp_path, capsys, settings
):
    from expedientes.models import Documento, Expediente

    settings.EXPEDIENTES_TEMP_DIR = tmp_path
    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-050", creado_por=usuario_ficticio
    )
    antiguo = tmp_path / "antiguo-ficticio.tmp"
    reciente = tmp_path / "reciente-ficticio.tmp"
    antiguo.write_bytes(b"antiguo")
    reciente.write_bytes(b"reciente")
    documento_antiguo = Documento.objects.create(
        expediente=expediente,
        rol="CLIENTE",
        nombre_original="antiguo-ficticio.txt",
        hash_archivo="2" * 64,
        tamano_bytes=7,
        ruta_temporal=str(antiguo),
        subido_por=usuario_ficticio,
    )
    Documento.objects.filter(pk=documento_antiguo.pk).update(
        subido_el=timezone.now() - timedelta(hours=25)
    )
    Documento.objects.create(
        expediente=expediente,
        rol="BORRADOR",
        nombre_original="reciente-ficticio.txt",
        hash_archivo="3" * 64,
        tamano_bytes=8,
        ruta_temporal=str(reciente),
        subido_por=usuario_ficticio,
    )
    huerfano_antiguo = tmp_path / "huerfano-antiguo-ficticio.tmp"
    huerfano_reciente = tmp_path / "huerfano-reciente-ficticio.tmp"
    huerfano_antiguo.write_bytes(b"huerfano antiguo")
    huerfano_reciente.write_bytes(b"huerfano reciente")
    antiguo_timestamp = (timezone.now() - timedelta(hours=25)).timestamp()
    os.utime(huerfano_antiguo, (antiguo_timestamp, antiguo_timestamp))

    call_command("limpiar_temporales")

    assert not antiguo.exists()
    assert reciente.exists()
    assert not huerfano_antiguo.exists()
    assert huerfano_reciente.exists()
    salida = capsys.readouterr().out
    assert "Temporales referenciados eliminados: 1" in salida
    assert "Temporales huérfanos eliminados: 1" in salida
    assert "Total de temporales eliminados: 2" in salida


def test_suprimir_texto_vacia_compartidos_e_informa_expedientes_afectados(
    usuario_ficticio, capsys
):
    from expedientes.models import Documento, Expediente, TextoExtraido

    texto = TextoExtraido.objects.create(
        hash_archivo="4" * 64,
        version_extractor="ocr-ficticio-v1",
        texto="dato sintético que debe desaparecer",
        calidad={"paginas": [{"cajas": [{"texto": "dato ficticio privado"}]}]},
        ultimo_uso_el=timezone.now(),
    )
    expedientes = [
        Expediente.objects.create(
            codigo=f"EXP-FICTICIO-05{i}", creado_por=usuario_ficticio
        )
        for i in range(2)
    ]
    for expediente in expedientes:
        Documento.objects.create(
            expediente=expediente,
            rol="CLIENTE",
            nombre_original="compartido-ficticio.txt",
            hash_archivo="4" * 64,
            tamano_bytes=8,
            texto_extraido=texto,
            estado="LISTO",
            subido_por=usuario_ficticio,
        )

    call_command("suprimir_texto_expediente", expedientes[0].codigo)
    texto.refresh_from_db()

    assert texto.texto == ""
    assert texto.calidad == {}
    salida = capsys.readouterr().out
    assert "Expediente solicitado incluido: 1" in salida
    assert "Otros expedientes que compartían el texto: 1" in salida
    assert Documento.objects.filter(texto_extraido=texto).count() == 2


def _con_texto(usuario, n, **campos):
    """Expediente EXP-FICTICIO-F50 con un recaudo cuyo texto es solo suyo."""
    from expedientes.models import Documento, Expediente, TextoExtraido

    texto = TextoExtraido.objects.create(
        hash_archivo=str(n) * 64,
        version_extractor="ocr-ficticio-v1",
        texto="dato sintético",
        ultimo_uso_el=timezone.now(),
    )
    Documento.objects.create(
        expediente=Expediente.objects.create(
            codigo="EXP-FICTICIO-F50", creado_por=usuario, **campos
        ),
        rol="CLIENTE",
        nombre_original="recaudo-ficticio.txt",
        hash_archivo=texto.hash_archivo,
        tamano_bytes=8,
        texto_extraido=texto,
        estado="LISTO",
        subido_por=usuario,
    )
    return texto


def test_suprimir_solo_el_activo_aunque_un_archivado_repita_el_codigo(
    usuario_ficticio,
):
    """F50: decisión del usuario (2026-10-16): nunca los archivados."""
    activo = _con_texto(usuario_ficticio, 6)
    archivado = _con_texto(usuario_ficticio, 7, archivado_el=timezone.now())

    call_command("suprimir_texto_expediente", "EXP-FICTICIO-F50")

    activo.refresh_from_db()
    archivado.refresh_from_db()
    assert (activo.texto, archivado.texto) == ("", "dato sintético")


@pytest.mark.parametrize("dos_activos", [False, True])
def test_suprimir_sin_un_unico_activo_no_suprime_nada(usuario_ficticio, dos_activos):
    from django.core.management.base import CommandError

    from expedientes.models import Expediente, TextoExtraido

    _con_texto(usuario_ficticio, 8, archivado_el=timezone.now())
    if dos_activos:  # un kardex y una transferencia vehicular (F43)
        _con_texto(usuario_ficticio, 9)
        _con_texto(usuario_ficticio, 5, tipo=Expediente.VEHICULAR)

    with pytest.raises(CommandError, match="No se suprimió nada"):
        call_command("suprimir_texto_expediente", "EXP-FICTICIO-F50")

    assert not TextoExtraido.objects.filter(texto="").exists()
