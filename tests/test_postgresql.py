"""Lo que depende del motor PostgreSQL, con datos ficticios."""

from datetime import date, datetime

import pytest
from django.db import IntegrityError, transaction

pytestmark = pytest.mark.django_db


def test_numero_de_kardex_distingue_mayusculas_y_solo_cuenta_activos(
    usuario_ficticio,
):
    from django.utils import timezone

    from expedientes.forms import ExpedienteForm, codigo_ocupado
    from expedientes.models import Expediente

    primero = Expediente.objects.create(codigo="K-100", creado_por=usuario_ficticio)
    formulario = ExpedienteForm(data={"codigo": "K-100"})
    assert not formulario.is_valid()
    assert formulario.errors["codigo"] == [codigo_ocupado(Expediente.NOTARIAL, primero)]
    with pytest.raises(IntegrityError), transaction.atomic():
        Expediente.objects.create(codigo="K-100", creado_por=usuario_ficticio)

    assert ExpedienteForm(data={"codigo": "k-100"}).is_valid()
    Expediente.objects.create(codigo="k-100", creado_por=usuario_ficticio)

    primero.archivado_el = timezone.now()
    primero.save()
    Expediente.objects.create(codigo="K-100", creado_por=usuario_ficticio)
    assert Expediente.objects.filter(codigo="K-100").count() == 2


def test_usuarios_que_solo_difieren_en_mayusculas_son_distintos():
    from django.contrib.auth import get_user_model

    usuarios = get_user_model().objects
    usuarios.create_user(username="ana.ficticia")
    usuarios.create_user(username="Ana.Ficticia")
    assert usuarios.get(username="ana.ficticia") != usuarios.get(
        username="Ana.Ficticia"
    )


def test_la_semana_empieza_en_lunes_en_hora_de_lima(usuario_ficticio):
    from expedientes.services import actividad_semanal
    from tests.test_inicio import LIMA, _corrida, _expediente

    domingo = _expediente("EXP-FICTICIO-DOMINGO", usuario_ficticio)
    lunes = _expediente("EXP-FICTICIO-LUNES", usuario_ficticio)
    _corrida(domingo, usuario_ficticio, datetime(2026, 10, 11, 23, 0, tzinfo=LIMA))
    _corrida(lunes, usuario_ficticio, datetime(2026, 10, 12, 0, 30, tzinfo=LIMA))
    semanas = {
        s["inicio"]: s["kardex"] for s in actividad_semanal(hoy=date(2026, 10, 14))
    }
    assert semanas[date(2026, 10, 5)] == 1
    assert semanas[date(2026, 10, 12)] == 1
