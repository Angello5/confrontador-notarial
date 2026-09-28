"""Contrato de la accion protegida de confrontacion F5."""

import re

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
    assert "Lingüístico" in contenido
    assert "ortografia-titulo" in contenido
    assert "[DNI]" not in contenido


def test_resultado_muestra_aviso_linguistico_sin_bloquear(
    client, usuario_ficticio, monkeypatch
):
    """F23 FR-003 y FR-006."""
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-F23", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    monkeypatch.setattr(
        "expedientes.views.confrontar_borrador",
        lambda *_: {
            "estado": "RESULTADO",
            "mensaje": "",
            "regla": [],
            "ortografia": [],
            "linguistico_aviso": "Ortografía y tildes no disponibles: aviso ficticio.",
        },
    )
    client.force_login(usuario_ficticio)

    contenido = client.post(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()

    assert "Lingüístico" in contenido
    assert "aviso ficticio" in contenido
    assert "Regla" in contenido


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


def test_resultado_muestra_personas_una_vez_con_procedencia_segura(
    client, usuario_ficticio, monkeypatch
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-PERSONAS", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    monkeypatch.setattr(
        "expedientes.views.confrontar_borrador",
        lambda *_: {
            "estado": "RESULTADO",
            "mensaje": "",
            "personas": [
                {
                    "formato": "persona",
                    "tipo": "DOCUMENTO_CRUZADO",
                    "nombre": "ALBA ZAFIRO LUMARIA",
                    "hallado": "90000022",
                    "esperado": "90000011",
                    "motivo": "El documento pertenece a otra persona según las fuentes.",
                    "procedencias": [
                        {"archivo": "biometrica-ficticia.pdf", "pagina": 2},
                        {"archivo": "sunarp-ficticio.pdf", "pagina": 4},
                    ],
                    "ubicacion": {"linea": 1, "fragmento": "DNI 90000022"},
                }
            ],
            "extraccion": {
                "personas": [
                    {
                        "nombre": "ALBA ZAFIRO LUMARIA",
                        "documento": "90000011",
                        "estado": "CONFIRMADA",
                        "estado_civil": "CASADO",
                        "fecha_nacimiento": "1990-07-03",
                        "domicilio": "Av. Luna 12",
                        "distrito": "Miraflores",
                        "procedencia_estado_civil": {
                            "archivo": "reniec-ficticio.pdf",
                            "pagina": 2,
                        },
                        "procedencia_fecha_nacimiento": {
                            "archivo": "reniec-ficticio.pdf",
                            "pagina": 2,
                        },
                        "procedencia_domicilio": {
                            "archivo": "reniec-ficticio.pdf",
                            "pagina": 2,
                        },
                        "procedencia_distrito": {
                            "archivo": "reniec-ficticio.pdf",
                            "pagina": 2,
                        },
                        "procedencias": [
                            {"archivo": "biometrica-ficticia.pdf", "pagina": 2},
                            {"archivo": "sunarp-ficticio.pdf", "pagina": 4},
                        ],
                    }
                ],
                "paginas_descartadas": [],
                "paginas_no_clasificadas": [],
                "documentos": [],
            },
            "regla": [],
            "ortografia": [],
        },
    )
    client.force_login(usuario_ficticio)

    contenido = client.post(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()

    assert "Personas con ficha" in contenido
    assert contenido.count("ALBA ZAFIRO LUMARIA") == 2
    assert "biometrica-ficticia.pdf" in contenido
    assert "sunarp-ficticio.pdf" in contenido
    assert "CASADO" in contenido
    assert "1990-07-03" in contenido
    assert "Av. Luna 12" in contenido
    assert "Miraflores" in contenido
    assert contenido.count("reniec-ficticio.pdf, página 2") == 4
    assert "/srv/privado" not in contenido
    assert "sha256" not in contenido.lower()
    assert "texto completo ficticio" not in contenido


def test_sondeo_no_expone_resumen_de_extraccion(client, usuario_ficticio):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-SONDEO", creado_por=usuario_ficticio
    )
    fuente, _ = _documentos(expediente, usuario_ficticio)
    fuente.texto_extraido.texto = (
        "CUI: 90000011 - 5\nAPELLIDO PATERNO  LUMARIA\n"
        "APELLIDO MATERNO  ZAFIRO\nNOMBRES  ALBA\n"
        "ESTADO CIVIL  CASADA\nFECHA DE NACIMIENTO  03/07/1990\n"
        "DIRECCION  Av. Luna 12\nDISTRITO DE DOMICILIO  Miraflores\f"
        "DECLARACION JURADA\nAPELLIDOS: LUMARIA ZAFIRO\nNOMBRES: ALBA\n"
        "NOMBRES Y APELLIDOS DEL CONYUGE: EMILIO SOLANO QUIMERA\f"
        "CLARA FICTELIA SOLARIA, DE NACIONALIDAD PERUANA. DNI 90000033"
    )
    fuente.texto_extraido.save(update_fields=("texto",))
    client.force_login(usuario_ficticio)

    respuesta = client.get(f"/expedientes/{expediente.pk}/estado/")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert "extraccion" not in datos
    assert "catalogo" not in datos
    assert "texto completo ficticio" not in str(datos)
    for privado in ("CASADA", "1990", "Luna", "Miraflores", "EMILIO", "CLARA"):
        assert privado not in str(datos)
    for campo in ("menciones", "adjuntos", "conyuge", "procedencias"):
        assert campo not in str(datos)


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


def _persona_legible(nombre, documento, **extra):
    fila = {
        "nombre": nombre,
        "documento": documento,
        "estado": "Confirmada",
        "procedencias": [{"archivo": "reniec-ficticio.pdf", "pagina": 1}],
        "estado_civil": None,
        "fecha_nacimiento": None,
        "domicilio": None,
        "distrito": None,
        "procedencia_estado_civil": None,
        "procedencia_fecha_nacimiento": None,
        "procedencia_domicilio": None,
        "procedencia_distrito": None,
        "conyuge": None,
        "procedencia_conyuge": None,
        "adjuntos": [],
    }
    return {**fila, **extra}


def _post_extraccion(client, usuario, monkeypatch, codigo, extraccion):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(codigo=codigo, creado_por=usuario)
    _, borrador = _documentos(expediente, usuario)
    monkeypatch.setattr(
        "expedientes.views.confrontar_borrador",
        lambda *_: {
            "estado": "RESULTADO",
            "mensaje": "",
            "regla": [],
            "ortografia": [],
            "extraccion": {
                "catalogo": {"NOMBRE": [], "DNI": [], "PARTIDA": [], "MONTO": []},
                "paginas_descartadas": [],
                "paginas_no_clasificadas": [],
                **extraccion,
            },
        },
    )
    client.force_login(usuario)
    return client.post(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()


def test_extraccion_separa_personas_con_ficha_y_menciones_sin_ficha(
    client, usuario_ficticio, monkeypatch
):
    contenido = _post_extraccion(
        client,
        usuario_ficticio,
        monkeypatch,
        "EXP-FICTICIO-ANCLAS",
        {
            "personas": [
                _persona_legible(
                    "ALBA LUMARIA ZAFIRO",
                    "90000011",
                    conyuge="EMILIO <b>SOLANO</b>",
                    procedencia_conyuge={
                        "archivo": "declaracion-ficticia.txt",
                        "pagina": 3,
                    },
                    adjuntos=[
                        {
                            "nombre": "Sin nombre",
                            "documento": "90000011",
                            "procedencias": [
                                {"archivo": "suelto-ficticio.txt", "pagina": 2}
                            ],
                        }
                    ],
                ),
                _persona_legible("BRUNO TELURIO NEBULOSA", "90000022"),
            ],
            "menciones": [
                _persona_legible(
                    "CLARA FICTELIA SOLARIA",
                    "Sin documento",
                    estado="Sin ficha",
                    procedencias=[{"archivo": "minuta-ficticia.txt", "pagina": 4}],
                    conyuge="DARIO FICTICIO",
                )
            ],
            "documentos": [
                {
                    "nombre": "reniec-ficticio.pdf",
                    "caracteres": 10,
                    "catalogo": {},
                    "aporta": True,
                    "personas": [{}, {}],
                    "menciones": [{}],
                }
            ],
        },
    )

    assert "Personas con ficha" in contenido
    assert (
        "Cada ficha RENIEC o biométrica es una persona. "
        "Los demás documentos solo añaden datos."
    ) in contenido
    assert "EMILIO &lt;b&gt;SOLANO&lt;/b&gt;" in contenido
    assert "<b>SOLANO</b>" not in contenido
    assert "declaracion-ficticia.txt, página 3" in contenido
    assert "Sin nombre · 90000011" in contenido
    assert "suelto-ficticio.txt, página 2" in contenido
    assert "No declarado" in contenido
    assert "Ninguno" in contenido
    assert "Menciones sin ficha" in contenido
    assert (
        "Aparecen en los documentos pero no tienen ficha en el legajo. "
        "Se verifican campo por campo, no como persona. "
        "Si es un compareciente, falta su ficha."
    ) in contenido
    assert "minuta-ficticia.txt, página 4" in contenido
    assert "DARIO FICTICIO" in contenido
    assert "Personas con ficha: 2" in contenido
    assert "Menciones sin ficha: 1" in contenido


def test_extraccion_sin_fichas_avisa_y_muestra_catalogo(
    client, usuario_ficticio, monkeypatch
):
    contenido = _post_extraccion(
        client,
        usuario_ficticio,
        monkeypatch,
        "EXP-FICTICIO-SIN-FICHAS",
        {"personas": [], "menciones": [], "documentos": []},
    )

    assert "Ninguna ficha RENIEC o biométrica en el legajo." in contenido
    assert "Catálogo agregado" in contenido
    assert "Menciones sin ficha" not in contenido


def test_resultado_muestra_cabecera_y_metricas_por_capa(
    client, usuario_ficticio, monkeypatch
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-METRICAS", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    ubicacion = {"linea": None, "fragmento": ""}
    monkeypatch.setattr(
        "expedientes.views.confrontar_borrador",
        lambda expediente, documento: {
            "estado": "RESULTADO",
            "regla": [
                {
                    "campo": "DNI",
                    "hallado": "1",
                    "esperado": "2",
                    "ubicacion": ubicacion,
                }
            ]
            * 2,
            "personas": [{"nombre": "NOMBRE FICTICIO", "ubicacion": ubicacion}],
            "extraccion": {
                "personas": [{"nombre": "UNO FICTICIO"}] * 3,
                "documentos": [],
            },
            "ortografia": [],
        },
    )
    client.force_login(usuario_ficticio)

    contenido = client.post(
        f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()

    assert "<h1>Resultado de la confrontación</h1>" in contenido
    assert "EXP-FICTICIO-METRICAS · borrador-ficticio.txt" in contenido
    assert contenido.count('class="card metrica"') == 3
    etiquetas = re.findall(r'<p class="metrica-etiqueta">([^<]+)</p>', contenido)
    valores = re.findall(r'<p class="metrica-valor">([^<]+)</p>', contenido)
    assert list(zip(etiquetas, valores)) == [
        ("Personas con ficha", "3"),
        ("Identidad", "1"),
        ("Regla", "2"),
    ]
    assert "Ortografía" not in etiquetas
    assert 'class="chip" data-estado="REVISION">2</span>' in contenido
