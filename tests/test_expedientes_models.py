"""Contrato de los modelos de F4, antes de crear la aplicación."""

import pytest
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone

pytestmark = pytest.mark.django_db


def test_expediente_normaliza_codigo_y_no_tiene_estado_propio(usuario_ficticio):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="  EXP-FICTICIO-001  ", creado_por=usuario_ficticio
    )

    assert expediente.codigo == "EXP-FICTICIO-001"
    assert not hasattr(Expediente, "estado")


def test_codigo_de_expediente_es_unico(usuario_ficticio):
    from expedientes.models import Expediente

    Expediente.objects.create(codigo="EXP-FICTICIO-002", creado_por=usuario_ficticio)
    with pytest.raises(IntegrityError), transaction.atomic():
        Expediente.objects.create(
            codigo="EXP-FICTICIO-002", creado_por=usuario_ficticio
        )


def test_relaciones_de_expediente_protegen_al_creador(usuario_ficticio):
    from expedientes.models import Expediente

    Expediente.objects.create(codigo="EXP-FICTICIO-003", creado_por=usuario_ficticio)

    with pytest.raises(ProtectedError):
        usuario_ficticio.delete()


def test_documento_y_texto_extraido_aplican_roles_estados_y_unicidades(
    usuario_ficticio,
):
    from expedientes.models import Documento, Expediente, TextoExtraido

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-004", creado_por=usuario_ficticio
    )
    texto = TextoExtraido.objects.create(
        hash_archivo="a" * 64,
        version_extractor="ocr-ficticio-v1",
        texto="texto sintético sin datos personales",
        ultimo_uso_el=timezone.now(),
    )
    documento = Documento.objects.create(
        expediente=expediente,
        rol="CLIENTE",
        nombre_original="fuente-sintetica.txt",
        hash_archivo="a" * 64,
        tamano_bytes=12,
        texto_extraido=texto,
        subido_por=usuario_ficticio,
    )

    assert documento.estado == "PENDIENTE"
    assert documento.tamano_bytes > 0
    assert {choice[0] for choice in Documento.ROLES} == {
        "CLIENTE",
        "MINUTA",
        "BORRADOR",
    }
    assert {choice[0] for choice in Documento.ESTADOS} == {
        "PENDIENTE",
        "PROCESANDO",
        "LISTO",
        "ERROR",
    }

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Documento.objects.create(
                expediente=expediente,
                rol="CLIENTE",
                nombre_original="otra-fuente.txt",
                hash_archivo="a" * 64,
                tamano_bytes=20,
                subido_por=usuario_ficticio,
            )


def test_texto_extraido_es_unico_por_hash_y_version(usuario_ficticio):
    from django.db import transaction

    from expedientes.models import TextoExtraido

    valores = {
        "hash_archivo": "b" * 64,
        "version_extractor": "ocr-ficticio-v2",
        "texto": "salida sintética",
        "ultimo_uso_el": timezone.now(),
    }
    TextoExtraido.objects.create(**valores)
    with pytest.raises(IntegrityError), transaction.atomic():
        TextoExtraido.objects.create(**valores)
