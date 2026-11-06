"""Contrato de la accion protegida de confrontacion F5."""

import re

from tests.flujo_confrontacion import confrontar_y_ver

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
        "expedientes.services.confrontar_borrador",
        lambda expediente, documento, **kwargs: (
            llamados.append((expediente.pk, documento.pk))
            or {"estado": "RESULTADO", "regla": [], "ortografia": []}
        ),
    )
    ruta = f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"

    client.force_login(usuario_ficticio)
    assert confrontar_y_ver(client, ruta).status_code == 200
    client.force_login(administrador_ficticio)
    assert confrontar_y_ver(client, ruta).status_code == 200
    assert llamados == [(expediente.pk, borrador.pk)]  # El segundo clic reutiliza.


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
        "expedientes.services.confrontar_borrador",
        lambda *_, **kwargs: {
            "estado": "RESULTADO",
            "mensaje": "",
            "regla": [
                {
                    "formato": "regla",
                    # F42: un dato del acto; el DNI ya va en «Generales de ley».
                    "campo": "PARTIDA",
                    "hallado": "80000002",
                    "esperado": "80000001",
                    "motivo": "",
                    "ubicacion": {"linea": 1, "fragmento": "PARTIDA 80000002."},
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

    respuesta = confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    )
    contenido = respuesta.content.decode()

    assert respuesta.status_code == 200
    assert "<table" in contenido
    assert '<th scope="col">Campo</th>' in contenido
    assert "Línea 1" in contenido
    assert "palabraficticia" in contenido
    assert '<span class="obs-capa">Lingüístico</span>' in contenido
    assert "[PARTIDA]" not in contenido


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
        "expedientes.services.confrontar_borrador",
        lambda *_, **kwargs: {
            "estado": "RESULTADO",
            "mensaje": "",
            "regla": [],
            "ortografia": [],
            "linguistico_aviso": "Ortografía y tildes no disponibles: aviso ficticio.",
        },
    )
    client.force_login(usuario_ficticio)

    contenido = confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
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
        "expedientes.services.confrontar_borrador",
        lambda *_, **kwargs: {
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

    contenido = confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()

    assert (
        '<details class="panel desplegable" aria-labelledby="extraccion-titulo"'
        in contenido
    )
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
        "expedientes.services.confrontar_borrador",
        lambda *_, **kwargs: {
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

    contenido = confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()

    assert "Personas con ficha" in contenido
    fichas = re.search(
        r'<table[^>]*aria-label="Personas con ficha"[^>]*>(.*?)</table>',
        contenido,
        re.S,
    ).group(1)
    assert fichas.count("ALBA ZAFIRO LUMARIA") == 1
    assert "biometrica-ficticia.pdf" in contenido
    assert "sunarp-ficticio.pdf" in contenido
    assert "CASADO" in contenido
    assert "1990-07-03" in contenido
    assert "Av. Luna 12" in contenido
    assert "Miraflores" in contenido
    assert fichas.count("reniec-ficticio.pdf, página 2") == 4
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
        "expedientes.services.confrontar_borrador",
        lambda *_, **kwargs: {
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

    contenido = confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()

    encabezado_regla = re.search(
        r'<div data-seccion="REGLA">(.*?)</table>', contenido, re.S
    ).group(1)
    assert '<th scope="col">Motivo</th>' not in encabezado_regla
    assert '<th scope="col">Porcentaje</th>' not in encabezado_regla
    assert "Coincidencia: 87.50%" in encabezado_regla


def test_ningun_campo_del_catalogo_sale_con_su_codigo_interno():
    """F51: «SIN_FICHA» o «CONYUGE_BIEN_PROPIO» no son títulos para el notario."""
    from django.template.loader import render_to_string

    from expedientes.services import CATALOGO_REGLAS

    def rotulo(campo):
        return render_to_string(
            "expedientes/_campo_nombre.html", {"campo": campo}
        ).strip()

    crudos = [
        campo
        for campo in [*CATALOGO_REGLAS["reglas"], "FORMATO_DESCONOCIDO"]
        if rotulo(campo) == campo and campo not in ("DNI", "RUC")
    ]
    assert crudos == []
    assert rotulo("SIN_FICHA") == "Persona sin ficha"
    assert rotulo("CONYUGE_BIEN_PROPIO") == "Cónyuge con bien propio"


def test_advertencia_de_correspondencia_es_distinta_de_una_observacion(
    client, usuario_ficticio, monkeypatch
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-ADVERTENCIA", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    monkeypatch.setattr(
        "expedientes.services.confrontar_borrador",
        lambda *_, **kwargs: {
            "estado": "ADVERTENCIA_CORRESPONDENCIA",
            "mensaje": "aviso seguro ficticio",
            "regla": [],
            "ortografia": [],
        },
    )
    client.force_login(usuario_ficticio)

    respuesta = confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
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
        "expedientes.services.confrontar_borrador",
        lambda *_, **kwargs: (_ for _ in ()).throw(
            RuntimeError("detalle privado ficticio")
        ),
    )
    client.force_login(usuario_ficticio)

    respuesta = confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
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
    assert respuesta.context["borradores_estado"][0]["puede_solicitar"] is False
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
        "expedientes.services.confrontar_borrador",
        lambda *_, **kwargs: {
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
    return confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
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
        "expedientes.services.confrontar_borrador",
        lambda expediente, documento, **kwargs: {
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

    contenido = confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()

    assert "<h1>EXP-FICTICIO-METRICAS</h1>" in contenido
    assert "Resultado de la confrontación" in contenido
    assert "borrador-ficticio.txt" in contenido
    assert "3 personas con ficha" in contenido
    assert len(re.findall(r'<li data-id="p\d+"', contenido)) == 1
    assert len(re.findall(r'<li data-id="r\d+"', contenido)) == 2
    assert len(re.findall(r'<li data-id="o\d+"', contenido)) == 0
    assert 'aria-label="Filtrar por severidad"' in contenido


def _items(contenido):
    return re.findall(
        r'<button type="button" class="obs-item".*?</button>', contenido, re.S
    )


def _texto(html):
    """El texto visible de un fragmento, con espacios simples."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def test_f56_cada_item_muestra_lo_hallado_y_lo_correcto(
    client, usuario_ficticio, monkeypatch
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-F56", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    ubicacion = {"linea": 3, "fragmento": "Fragmento ficticio."}
    monkeypatch.setattr(
        "expedientes.services.confrontar_borrador",
        lambda *_, **kwargs: {
            "estado": "RESULTADO",
            "personas": [
                {
                    "tipo": "DOCUMENTO_CRUZADO",
                    "nombre": "ALBA ZURBELIA LUMARIA",
                    "hallado": "90000002",
                    "esperado": "90000001",
                    "ubicacion": ubicacion,
                }
            ],
            "regla": [
                {
                    "campo": "NOMBRE",
                    "hallado": "ALBA LUNARIA",
                    "esperado": "ALBA LUMARIA",
                    "ubicacion": ubicacion,
                },
                {
                    "campo": "PARTIDA",
                    "hallado": "80000002",
                    "esperado": "80000001",
                    "ubicacion": ubicacion,
                },
            ],
            "ortografia": [
                {
                    "palabra": "clausla",
                    "motivo": "no existe en castellano",
                    "sugerencia": "cláusula",
                    "ubicacion": ubicacion,
                }
            ],
        },
    )
    client.force_login(usuario_ficticio)

    contenido = confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()
    items = _items(contenido)

    assert len(items) == 4
    pares = [
        ("90000002", "90000001", "Dice", "Debe decir", "90000002", "90000001"),
        ("ALBA LUNARIA", "ALBA LUMARIA", "Dice", "Debe decir", "LUNARIA", "LUMARIA"),
        ("80000002", "80000001", "Dice", "Debe decir", "80000002", "80000001"),
        ("clausla", "cláusula", "Texto", "Sugerencia", "clausla", "cláusula"),
    ]
    for hallado, esperado, dice, debe, distinto, correcto in pares:
        item = next(i for i in items if f"{dice} {hallado} " in _texto(i))
        # F65: dos líneas pequeñas con su rótulo, sin recortar el texto.
        assert f"{dice} {hallado} {debe} {esperado}" in _texto(item)
        # Solo lo que cambia va resaltado.
        assert '<span class="tachado">' in item and f"<mark>{distinto}</mark>" in item
        assert '<span class="correcto">' in item and f"<mark>{correcto}</mark>" in item
    assert '<span class="obs-capa">Generales de ley</span>' in contenido
    assert '<span class="obs-capa">Regla</span>' in contenido
    assert '<span class="obs-capa">Lingüístico</span>' in contenido
    assert '<strong class="obs-titulo">No existe en castellano</strong>' in contenido


def test_f56_una_sola_pestana_todas_y_siguen_los_filtros_de_severidad(
    client, usuario_ficticio, monkeypatch
):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-F56-TODAS", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    monkeypatch.setattr(
        "expedientes.services.confrontar_borrador",
        lambda *_, **kwargs: {
            "estado": "RESULTADO",
            "regla": [
                {
                    "campo": "PARTIDA",
                    "hallado": "80000002",
                    "esperado": "80000001",
                    "ubicacion": {"linea": 1, "fragmento": ""},
                }
            ],
            "linguistico_aviso": "Aviso lingüístico ficticio.",
        },
    )
    client.force_login(usuario_ficticio)

    contenido = confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()

    # F73: las pestañas separan documento y lista; las capas siguen sin pestañas.
    assert 'role="tablist" aria-label="Vista"' in contenido
    assert re.search(
        r'<h2 id="obs-titulo" class="obs-panel-titulo">Observaciones'
        r'<span class="capa-num" x-text="visibles.length">',
        contenido,
    )
    for retirada in ("IDENTIDAD", "REGLA", "LINGUISTICO"):
        assert f"capa === '{retirada}'" not in contenido
    # El aviso lingüístico ya no depende de una pestaña.
    assert re.search(r'<div class="aviso" role="status">\s*<svg', contenido)
    assert "Aviso lingüístico ficticio." in contenido
    for sev in ("ALTA", "MEDIA", "BAJA"):
        assert re.search(
            rf'class="sev-filtro" data-sev="{sev}" :aria-pressed="sev === \'{sev}\'"',
            contenido,
        )


def test_f56_la_hoja_de_estilos_no_oculta_el_dato_y_lo_recorta():
    from pathlib import Path

    from django.contrib.staticfiles import finders

    css = Path(finders.find("css/erp.css")).read_text(encoding="utf-8")

    assert not re.search(r"\.obs-item \.cambio \{[^}]*display: none", css)
    recorte = re.search(r"\.cambio \.tachado, \.cambio \.correcto \{([^}]*)\}", css)
    assert recorte
    assert "text-overflow: ellipsis" in recorte.group(1)
    assert "white-space: nowrap" in recorte.group(1)
    assert "!important" not in recorte.group(1)


# F60: datos ficticios de los avisos que no son una corrección.
_BIEN_PROPIO = {
    "campo": "CONYUGE_BIEN_PROPIO",
    "hallado": "ALBA ZURBELIA LUMARIA: Interviene sin su cónyuge por ser bien propio",
    "esperado": "RENIEC: CASADO",
    "motivo": "Fuente: ficha-ficticia.pdf, página 1",
}
_LETRAS = {
    "campo": "NUMERO_EN_LETRAS",
    "hallado": "2,50 (DOS MIL QUINIENTOS CON 00/100 SOLES)",
    "esperado": "2,50",
}
_DOMICILIO = {
    "campo": "DOMICILIO_NO_ENCONTRADO",
    "hallado": "ALBA ZURBELIA LUMARIA: No aparece en el borrador",
    "esperado": "RENIEC: CALLE FICTICIA 123",
}


@pytest.mark.parametrize(
    ("fila", "borrador", "verificar", "lista"),
    [
        (
            _BIEN_PROPIO,
            _BIEN_PROPIO["hallado"],
            "RENIEC indica CASADO. Confirme que el bien es propio; "
            "si no lo es, debe intervenir el cónyuge.",
            "ALBA ZURBELIA LUMARIA: casado según RENIEC · confirme bien propio",
        ),
        (
            _LETRAS,
            _LETRAS["hallado"],
            "La cifra y las letras no valen lo mismo. Corrija la que no corresponda.",
            "Cifra y letras no coinciden: 2,50 (DOS MIL QUINIENTOS CON 00/100 SOLES)",
        ),
        (
            {
                "campo": "AREA",
                "hallado": "CIEN METROS CUADRADOS (120 M2)",
                "esperado": "120 M2",
            },
            "CIEN METROS CUADRADOS (120 M2)",
            "La cifra y las letras del área no valen lo mismo. "
            "Corrija la que no corresponda.",
            "Cifra y letras no coinciden: CIEN METROS CUADRADOS (120 M2)",
        ),
        (
            {
                "campo": "COPROPIEDAD",
                "hallado": "50 % Y EL 40 %",
                "esperado": "100 %",
            },
            "50 % Y EL 40 %",
            "Las cuotas de copropiedad no suman 100 %. Corrija la que no corresponda.",
            "Las cuotas no suman 100 %: 50 % Y EL 40 %",
        ),
        (
            _DOMICILIO,
            "ALBA ZURBELIA LUMARIA: su domicilio de RENIEC no aparece en el borrador",
            "Domicilio según RENIEC: CALLE FICTICIA 123. "
            "Verifique el domicilio que el borrador indica para esta persona.",
            "ALBA ZURBELIA LUMARIA: su domicilio de RENIEC no aparece · "
            "CALLE FICTICIA 123",
        ),
        (
            {
                "campo": "MENOR_DE_EDAD",
                "hallado": "ALBA ZURBELIA LUMARIA: 16 años al 2026-10-20",
                "esperado": "Fecha de nacimiento: 2010-05-01",
            },
            "ALBA ZURBELIA LUMARIA",
            "Es menor de edad: 16 años al 2026-10-20. "
            "Fecha de nacimiento: 2010-05-01. Verifique cómo interviene.",
            "ALBA ZURBELIA LUMARIA: 16 años al 2026-10-20",
        ),
        (
            {
                "campo": "SIN_FICHA",
                "hallado": "ALBA ZURBELIA LUMARIA",
                "esperado": "Sin ficha RENIEC en los recaudos; "
                "la minuta dice «ALBA SURBELIA LUMARIA»",
            },
            "ALBA ZURBELIA LUMARIA",
            "Sin ficha RENIEC en los recaudos; la minuta dice «ALBA SURBELIA LUMARIA». "
            "No se pudo verificar: revíselo a mano o cargue la ficha.",
            "Sin ficha RENIEC en los recaudos: ALBA ZURBELIA LUMARIA",
        ),
        (
            {
                "campo": "NOMBRE_MARCA_AGUA",
                "hallado": "ALBA ZURBELIA LUNARIA",
                "esperado": "Posible Ñ por marca de agua; verifique el DNI",
            },
            "ALBA ZURBELIA LUNARIA",
            "La ficha escaneada muestra una Ñ que puede ser la marca de agua. "
            "Verifique el nombre con el DNI.",
            "Posible Ñ por marca de agua: ALBA ZURBELIA LUNARIA",
        ),
        (
            {
                "tipo": "DOCUMENTO_SIN_TITULAR",
                "hallado": "90000009",
                "esperado": "Sin documento conocido",
            },
            "90000009",
            "Ninguna persona de los recaudos tiene este documento. "
            "Verifique el número.",
            "Sin titular en los recaudos: 90000009",
        ),
        (
            {
                "campo": "PARTIDA",
                "hallado": "80000009",
                "esperado": "No coincide con ninguna fuente",
            },
            "80000009",
            "No coincide con ninguna fuente. Verifique el dato en los documentos.",
            "No coincide con ninguna fuente: 80000009",
        ),
        (
            {"campo": "DNI", "hallado": "9000001", "esperado": "Debe tener 8 dígitos"},
            "9000001",
            "Debe tener 8 dígitos. Verifique el número.",
            "Debe tener 8 dígitos: 9000001",
        ),
        (
            {
                "campo": "ANEXO",
                "hallado": "No aparece en el borrador",
                "esperado": "ANEXO 1 - HOJA RESUMEN",
            },
            "No aparece en el borrador",
            "La minuta incluye «ANEXO 1 - HOJA RESUMEN». "
            "Verifique que el borrador lo incluya.",
            "Falta en el borrador: ANEXO 1 - HOJA RESUMEN",
        ),
        (
            {
                "campo": "PRECIO",
                "hallado": "No aparece en el borrador",
                "esperado": "Precio de la transferencia",
            },
            "No aparece en el borrador",
            "El acta no indica el precio de la transferencia. "
            "Verifique que lo incluya.",
            "El acta no indica el precio de la transferencia",
        ),
    ],
)
def test_f60_aviso_dice_que_verificar(fila, borrador, verificar, lista):
    from expedientes.services import aviso_de

    assert aviso_de(fila) == {
        "borrador": borrador,
        "verificar": verificar,
        "lista": lista,
    }


@pytest.mark.parametrize(
    "fila",
    [
        {"campo": "PARTIDA", "hallado": "80000002", "esperado": "80000001"},
        {"tipo": "DOCUMENTO_CRUZADO", "hallado": "90000002", "esperado": "90000001"},
        {
            "campo": "ESTADO_CIVIL_DISCREPANTE",
            "hallado": "ALBA ZURBELIA LUMARIA: SOLTERA",
            "esperado": "RENIEC: CASADO",
        },
        {
            "campo": "PLACA",
            "hallado": "No aparece en el borrador",
            "esperado": "ABC-123",
        },
        {"campo": "ORTOGRAFIA", "hallado": "clausla", "esperado": "cláusula"},
    ],
)
def test_f60_una_correccion_sigue_con_debe_decir(fila):
    from expedientes.services import aviso_de

    assert aviso_de(fila) is None


def test_f60_la_pantalla_dice_que_verificar_sin_debe_decir(
    client, usuario_ficticio, monkeypatch
):
    from expedientes.models import Corrida, Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-F60", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    ubicacion = {"linea": 2, "fragmento": "Fragmento ficticio."}
    partida = {"campo": "PARTIDA", "hallado": "80000002", "esperado": "80000001"}
    monkeypatch.setattr(
        "expedientes.services.confrontar_borrador",
        lambda *_, **kwargs: {
            "estado": "RESULTADO",
            "regla": [
                {**fila, "ubicacion": ubicacion}
                for fila in (_BIEN_PROPIO, _LETRAS, _DOMICILIO, partida)
            ],
        },
    )
    client.force_login(usuario_ficticio)

    contenido = confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()
    items = _items(contenido)

    # La corrida guarda el texto de siempre: el aviso se arma al mostrar.
    corrida = Corrida.objects.get(expediente=expediente)
    assert "RENIEC: CASADO" in corrida.hallazgos
    # Ningún sitio de la pantalla dice «Debe decir: RENIEC: CASADO».
    assert "RENIEC: CASADO" not in contenido

    bien_propio = next(i for i in items if "por ser bien propio" in i)
    assert "tachado" not in bien_propio
    assert (
        "En el borrador ALBA ZURBELIA LUMARIA: Interviene sin su cónyuge por ser "
        "bien propio Qué verificar RENIEC indica CASADO." in _texto(bien_propio)
    )
    letras = next(i for i in items if "La cifra y las letras no valen" in i)
    assert "tachado" not in letras
    domicilio = next(i for i in items if "CALLE FICTICIA 123" in i)
    assert "No aparece en el borrador" not in domicilio
    assert "su domicilio de RENIEC no aparece" in domicilio
    # La corrección de verdad conserva el tachado → correcto de F56.
    corregible = next(i for i in items if "<mark>80000002</mark>" in i)
    assert "<mark>80000002</mark>" in corregible
    assert "<mark>80000001</mark>" in corregible

    # F65: sin panel de detalle; la fila dice «En el borrador» y «Qué verificar».
    assert "Detalle de la observación" not in contenido
    assert contenido.count('<span class="obs-rot">En el borrador</span>') == 3
    assert contenido.count('<span class="obs-rot">Qué verificar</span>') == 3
    assert contenido.count('<span class="obs-rot">Debe decir</span>') == 1
    assert (
        "Qué verificar La cifra y las letras no valen lo mismo. "
        "Corrija la que no corresponda."
    ) in _texto(letras)
    assert (
        "En el borrador ALBA ZURBELIA LUMARIA: su domicilio de RENIEC no aparece "
        "en el borrador"
    ) in _texto(domicilio)

    # Datos del informe Word y de la tabla exportada: el aviso no trae «debe decir».
    assert re.search(
        r'data-hallado="2,50 \(DOS MIL QUINIENTOS CON 00/100 SOLES\)" '
        r'data-esperado="" data-verificar="La cifra y las letras no valen lo mismo\. '
        r'Corrija la que no corresponda\." data-aviso="Cifra y letras no coinciden: ',
        contenido,
    )
    assert 'data-esperado="80000001" data-verificar="" data-aviso=""' in contenido

    # Informe imprimible.
    informe = re.search(r'<div data-seccion="IDENTIDAD">(.*?)</table>', contenido, re.S)
    assert "Qué verificar: RENIEC indica CASADO." in informe.group(1)
    regla = re.search(r'<div data-seccion="REGLA">(.*?)</table>', contenido, re.S)
    assert "Qué verificar: La cifra y las letras no valen lo mismo." in regla.group(1)

    # Vista de la corrida en el historial.
    detalle = client.get(
        f"/expedientes/{expediente.pk}/confrontaciones/{corrida.pk}/"
    ).content.decode()
    assert "RENIEC: CASADO" not in detalle
    assert "Qué verificar: RENIEC indica CASADO." in detalle
    assert '<span class="tachado">80000002</span>' in detalle
    assert '<span class="tachado">2,50 (DOS MIL' not in detalle


def _resultado_f73(client, usuario, monkeypatch, codigo="EXP-FICTICIO-F73"):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(codigo=codigo, creado_por=usuario)
    _, borrador = _documentos(expediente, usuario)
    ubicacion = {"linea": 3, "fragmento": "Fragmento ficticio."}
    monkeypatch.setattr(
        "expedientes.services.confrontar_borrador",
        lambda *_, **kwargs: {
            "estado": "RESULTADO",
            "personas": [
                {
                    "tipo": "DOCUMENTO_CRUZADO",
                    "nombre": "ALBA ZURBELIA LUMARIA",
                    "hallado": "90000002",
                    "esperado": "90000001",
                    "motivo": "Motivo ficticio de persona.",
                    "procedencias": [{"archivo": "dni-ficticio.pdf", "pagina": 2}],
                    "ubicacion": ubicacion,
                }
            ],
            "regla": [
                {
                    "campo": "PARTIDA",
                    "hallado": "80000002",
                    "esperado": "80000001",
                    "motivo": "Motivo ficticio de regla.",
                    "ubicacion": ubicacion,
                }
            ],
            "ortografia": [
                {
                    "palabra": "clausla",
                    "motivo": "no existe en castellano",
                    "sugerencia": "cláusula",
                    "ubicacion": ubicacion,
                }
            ],
        },
    )
    client.force_login(usuario)
    return confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()


def test_f73_encabezado_unico_con_resumen_filtros_y_acciones(
    client, usuario_ficticio, monkeypatch
):
    contenido = _resultado_f73(client, usuario_ficticio, monkeypatch)

    cabecera = re.search(
        r'<section class="panel resultado-cab".*?</section>', contenido, re.S
    ).group()
    assert "<h1>EXP-FICTICIO-F73</h1>" in cabecera
    assert "observaciones para revisar" in cabecera
    assert 'aria-label="Filtrar por severidad"' in cabecera
    assert "Vista previa del informe" in cabecera
    assert "Descargar informe" in cabecera
    assert 'class="panel resumen"' not in contenido


def test_f73_el_detalle_se_despliega_en_la_fila(client, usuario_ficticio, monkeypatch):
    contenido = _resultado_f73(client, usuario_ficticio, monkeypatch)

    for identificador in ("p1", "r1", "o1"):
        assert f":aria-expanded=\"(sel === '{identificador}').toString()\"" in contenido
        assert f"""x-show="sel === '{identificador}'" x-cloak""" in contenido
    assert '<p class="obs-motivo">Motivo ficticio de persona.</p>' in contenido
    assert "<dt>Fuente</dt><dd>dni-ficticio.pdf, página 2</dd>" in contenido
    assert '<p class="obs-motivo">Motivo ficticio de regla.</p>' in contenido
    # Lingüístico solo informa; las demás capas dicen si se pueden corregir.
    assert contenido.count("Solo informa: no corrige el documento") >= 1
    assert "No admite corrección automática: corríjala a mano." in contenido
    assert "Ver en el borrador" in contenido
    # Lo hallado sigue en la fila (F65) y el fragmento sigue fuera de ella (F71).
    for item in _items(contenido):
        assert "Fragmento ficticio." not in item
        assert "Motivo ficticio" not in item


def test_f73_la_vista_previa_comparte_contenido_con_la_descarga(
    client, usuario_ficticio, monkeypatch
):
    contenido = _resultado_f73(client, usuario_ficticio, monkeypatch)

    assert contenido.count('x-model="rep.IDENTIDAD"') == 2
    assert 'class="modal modal-vista"' in contenido
    assert 'x-ref="informe"' in contenido
    assert ':disabled="generando || vistaVacia"' in contenido
    assert "No hay secciones seleccionadas" in contenido
    assert "No se pudo preparar la vista previa" in contenido
    assert "Para PDF o Excel use «Descargar informe»." in contenido


def test_f73_sin_resultado_no_ofrece_informe(client, usuario_ficticio, monkeypatch):
    from expedientes.models import Expediente

    expediente = Expediente.objects.create(
        codigo="EXP-FICTICIO-F73-NO", creado_por=usuario_ficticio
    )
    _, borrador = _documentos(expediente, usuario_ficticio)
    monkeypatch.setattr(
        "expedientes.services.confrontar_borrador",
        lambda *_, **kwargs: {
            "estado": "ERROR_SEGURO",
            "mensaje": "Mensaje ficticio.",
            "regla": [],
            "ortografia": [],
        },
    )
    client.force_login(usuario_ficticio)

    contenido = confrontar_y_ver(
        client, f"/expedientes/{expediente.pk}/documentos/{borrador.pk}/confrontar/"
    ).content.decode()

    assert "<h1>EXP-FICTICIO-F73-NO</h1>" in contenido
    assert "Vista previa del informe" not in contenido
    assert "Descargar informe" not in contenido
