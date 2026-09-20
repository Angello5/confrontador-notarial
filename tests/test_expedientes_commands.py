"""Contrato de comandos de limpieza y supresión F4."""

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

pytestmark = pytest.mark.django_db


def test_limpiar_temporales_solo_elimina_huerfanos_antiguos(usuario_ficticio, tmp_path):
    from expedientes.models import Documento, Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-050", creado_por=usuario_ficticio
    )
    antiguo = tmp_path / "antiguo-ficticio.tmp"
    reciente = tmp_path / "reciente-ficticio.tmp"
    antiguo.write_bytes(b"antiguo")
    reciente.write_bytes(b"reciente")
    documento_antiguo = Documento.objects.create(
        expediente=expediente,
        rol="FUENTE",
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

    call_command("limpiar_temporales")

    assert not antiguo.exists()
    assert reciente.exists()


def test_suprimir_texto_vacia_compartidos_e_informa_expedientes_afectados(
    usuario_ficticio, capsys
):
    from expedientes.models import Documento, Expediente, TextoExtraido

    texto = TextoExtraido.objects.create(
        hash_archivo="4" * 64,
        version_extractor="ocr-ficticio-v1",
        texto="dato sintético que debe desaparecer",
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
            rol="FUENTE",
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
    assert "2" in capsys.readouterr().out
    assert Documento.objects.filter(texto_extraido=texto).count() == 2
