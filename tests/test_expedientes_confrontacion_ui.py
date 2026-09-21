"""Contrato de la accion protegida de confrontacion F5."""

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


def _documentos(expediente, usuario, *, borrador=True):
    from django.utils import timezone

    from expedientes.models import Documento, TextoExtraido

    def crear(rol, nombre, texto):
        extraido = TextoExtraido.objects.create(
            hash_archivo=(nombre.replace(".", "")[:64]).ljust(64, "0"),
            version_extractor="extractor-ficticio-v1",
            texto=texto,
            ultimo_uso_el=timezone.now(),
        )
        return Documento.objects.create(
            expediente=expediente,
            rol=rol,
            nombre_original=nombre,
            hash_archivo=extraido.hash_archivo,
            tamano_bytes=max(len(texto), 1),
            estado=Documento.LISTO,
            texto_extraido=extraido,
            subido_por=usuario,
        )

    fuente = crear(Documento.CLIENTE, "cliente-ficticio.txt", "cliente ficticio")
    crear(Documento.MINUTA, "minuta-ficticia.docx", "minuta ficticia")
    documento = (
        crear(Documento.BORRADOR, "borrador-ficticio.txt", "borrador ficticio")
        if borrador
        else fuente
    )
    return fuente, documento


def test_creador_y_administrador_llegan_al_servicio(
    client, usuario_ficticio, administrador_ficticio, monkeypatch
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-UI", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    llamados = []
    monkeypatch.setattr(
        "expedientes.views.confrontar_borrador",
        lambda expediente, documento: (
            llamados.append((expediente.pk, documento.pk))
            or {"estado": "RESULTADO", "regla": [], "ortografia": []}
        ),
    )
    ruta = f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"

    client.force_login(usuario_ficticio)
    assert client.post(ruta).status_code == 200
    client.force_login(administrador_ficticio)
    assert client.post(ruta).status_code == 200
    assert llamados == [(expediente.pk, borrador.pk)] * 2


def test_accion_rechaza_metodo_invalido_y_csrf(client, usuario_ficticio):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-CSRF", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    ruta = f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    client.force_login(usuario_ficticio)

    assert client.get(ruta).status_code == 405
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(usuario_ficticio)
    assert csrf_client.post(ruta).status_code == 403


def test_usuario_sin_rol_no_puede_confrontar(client, usuario_ficticio):
    from django.contrib.auth import get_user_model
    from expedientes.models import Expediente

    sin_rol = get_user_model().objects.create_user(username="sin_rol_ficticio")
    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-SIN-ROL", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    ruta = f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    client.force_login(sin_rol)

    assert client.post(ruta).status_code == 403


def test_accion_no_revela_documento_ajeno_ni_documento_fuente(
    client, usuario_ficticio, administrador_ficticio
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-AJENO", creado_por=administrador_ficticio
    )
    fuente, borrador = _documentos(expediente, administrador_ficticio)
    ruta_ajena = f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ruta_fuente = f"/expedientes/{expediente.pk}/documentos/{fuente.pk}/confrontar/"
    client.force_login(usuario_ficticio)

    assert client.post(ruta_ajena).status_code in {403, 404}
    client.force_login(administrador_ficticio)
    assert client.post(ruta_fuente).status_code in {403, 404}


def test_resultado_muestra_tablas_accesibles_y_no_cadena_cruda(
    client, usuario_ficticio, monkeypatch
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-TABLA", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    monkeypatch.setattr(
        "expedientes.views.confrontar_borrador",
        lambda *_: {
            "estado": "RESULTADO",
            "mensaje": "",
            "regla": [
                {
                    "formato": "regla",
                    "campo": "DNI",
                    "hallado": "90000002",
                    "esperado": "90000001",
                    "motivo": "",
                    "ubicacion": {"linea": 1, "fragmento": "DNI 90000002."},
                }
            ],
            "ortografia": [
                {
                    "palabra": "palabraficticia",
                    "motivo": "motivo ficticio",
                    "sugerencia": "Sin sugerencia",
                    "ubicacion": {"linea": 2, "fragmento": "palabraficticia."},
                }
            ],
        },
    )
    client.force_login(usuario_ficticio)

    respuesta = client.post(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    )
    contenido = respuesta.content.decode()

    assert respuesta.status_code == 200
    assert "<table" in contenido
    assert '<th scope="col">Campo</th>' in contenido
    assert "Línea 1" in contenido
    assert "palabraficticia" in contenido
    assert "[DNI]" not in contenido


def test_resultado_muestra_verificacion_de_extraccion_sin_texto_completo(
    client, usuario_ficticio, monkeypatch
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-EXTRACCION", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    monkeypatch.setattr(
        "expedientes.views.confrontar_borrador",
        lambda *_: {
            "estado": "RESULTADO",
            "mensaje": "",
            "regla": [],
            "ortografia": [],
            "extraccion": {
                "catalogo": {
                    "NOMBRE": ["NOMBRE FICTICIO"],
                    "DNI": ["90000001"],
                    "PARTIDA": [],
                    "MONTO": ["1200.00"],
                },
                "documentos": [
                    {
                        "nombre": "cliente-ficticio.txt",
                        "caracteres": 32,
                        "catalogo": {
                            "NOMBRE": ["NOMBRE FICTICIO"],
                            "DNI": ["90000001"],
                            "PARTIDA": [],
                            "MONTO": [],
                        },
                        "aporta": True,
                    },
                    {
                        "nombre": "imagen-ficticia.jpg",
                        "caracteres": 4,
                        "catalogo": {
                            "NOMBRE": [],
                            "DNI": [],
                            "PARTIDA": [],
                            "MONTO": [],
                        },
                        "aporta": False,
                    },
                ],
            },
        },
    )
    client.force_login(usuario_ficticio)

    contenido = client.post(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()

    assert '<details class="card mb-3"' in contenido
    assert "Qué se extrajo de los documentos" in contenido
    assert "NOMBRE FICTICIO" in contenido
    assert "90000001" in contenido
    assert "1200.00" in contenido
    assert "cliente-ficticio.txt" in contenido
    assert "imagen-ficticia.jpg" in contenido
    assert "No aportó campos detectables" in contenido
    assert "32 caracteres" in contenido
    assert "texto completo ficticio que no debe aparecer" not in contenido


def test_sondeo_no_expone_resumen_de_extraccion(client, usuario_ficticio):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-SONDEO", creado_por=usuario_ficticio
    )
    _documentos(expediente, usuario_ficticio)
    client.force_login(usuario_ficticio)

    respuesta = client.get(f"/expedientes/{expediente.pk}/estado/")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert "extraccion" not in datos
    assert "catalogo" not in datos
    assert "texto completo ficticio" not in str(datos)


def test_tabla_de_regla_no_muestra_columnas_vacias(
    client, usuario_ficticio, monkeypatch
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-COLUMNAS", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    monkeypatch.setattr(
        "expedientes.views.confrontar_borrador",
        lambda *_: {
            "estado": "RESULTADO",
            "mensaje": "",
            "regla": [
                {
                    "formato": "regla",
                    "campo": "DNI",
                    "hallado": "90000002",
                    "esperado": "90000001",
                    "motivo": "",
                    "porcentaje": "",
                    "ubicacion": {"linea": 1, "fragmento": "DNI 90000002."},
                },
                {
                    "formato": "regla",
                    "campo": "PARRAFO",
                    "hallado": "No aparece o fue alterado",
                    "esperado": "texto de fuente ficticia…",
                    "motivo": "Coincidencia: 87.50%",
                    "porcentaje": "87.50",
                    "ubicacion": {"linea": None, "fragmento": "No ubicada"},
                },
            ],
            "ortografia": [],
        },
    )
    client.force_login(usuario_ficticio)

    contenido = client.post(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()

    encabezado_regla = contenido.split('<section class="card mb-3"', 1)[1].split(
        '<section class="card mb-3"', 1
    )[0]
    assert '<th scope="col">Motivo</th>' not in encabezado_regla
    assert '<th scope="col">Porcentaje</th>' not in encabezado_regla
    assert "Coincidencia: 87.50%" in encabezado_regla


def test_advertencia_de_correspondencia_es_distinta_de_una_observacion(
    client, usuario_ficticio, monkeypatch
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-ADVERTENCIA", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    monkeypatch.setattr(
        "expedientes.views.confrontar_borrador",
        lambda *_: {
            "estado": "ADVERTENCIA_CORRESPONDENCIA",
            "mensaje": "aviso seguro ficticio",
            "regla": [],
            "ortografia": [],
        },
    )
    client.force_login(usuario_ficticio)

    respuesta = client.post(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    )
    contenido = respuesta.content.decode()

    assert respuesta.status_code == 200
    assert 'role="alert"' in contenido
    assert "aviso seguro ficticio" in contenido
    assert "No se muestran diferencias campo por campo" in contenido
    assert "<table" not in contenido


def test_error_de_servicio_se_presenta_de_forma_segura(
    client, usuario_ficticio, monkeypatch
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-ERROR", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    monkeypatch.setattr(
        "expedientes.views.confrontar_borrador",
        lambda *_: (_ for _ in ()).throw(RuntimeError("detalle privado ficticio")),
    )
    client.force_login(usuario_ficticio)

    respuesta = client.post(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    )
    contenido = respuesta.content.decode()

    assert respuesta.status_code == 200
    assert 'role="alert"' in contenido
    assert "No se pudo completar la confrontación. Intente nuevamente" in contenido
    assert "detalle privado ficticio" not in contenido


def test_detalle_distingue_texto_suprimido_de_fallo_de_procesamiento(
    client, usuario_ficticio
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-SUPRIMIDO", creado_por=usuario_ficticio
    )
    fuente, borrador = _documentos(expediente, usuario_ficticio)
    borrador.texto_extraido.texto = ""
    borrador.texto_extraido.save(update_fields=("texto",))
    client.force_login(usuario_ficticio)

    respuesta = client.get(f"/expedientes/{expediente.pk}/")
    contenido = respuesta.content.decode()

    assert respuesta.status_code == 200
    assert "disabled>Confrontar borrador</button>" in contenido
    assert "texto del borrador ya no está disponible" in contenido
    assert fuente.pk != borrador.pk
