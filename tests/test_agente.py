"""F75 · Agente de estudio de título: interruptor, permisos, adjuntos y proveedores."""

import json
import subprocess

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from agente import services
from agente.models import ConsultaAgente

pytestmark = pytest.mark.django_db


def _preguntar(client, pregunta, **extra):
    return client.post(
        "/agente/preguntar/",
        json.dumps({"pregunta": pregunta, **extra}),
        content_type="application/json",
    )


def _doc(nombre, texto, aviso=""):
    return {"nombre": nombre, "texto": texto, "aviso": aviso}


def _adjuntar(
    client, nombre="partida.txt", contenido=b"Partida ficticia 000. Area 120 m2"
):
    return client.post(
        "/agente/adjuntar/", {"archivo": SimpleUploadedFile(nombre, contenido)}
    )


def test_apagado_ninguna_ruta_existe(client, usuario_ficticio):
    client.force_login(usuario_ficticio)
    assert client.get("/agente/").status_code == 404
    assert _preguntar(client, "hola").status_code == 404
    assert _adjuntar(client).status_code == 404


@override_settings(AGENTE_ACTIVO=True)
def test_exige_login_y_rol(client, django_user_model):
    assert client.get("/agente/").status_code == 302
    assert _adjuntar(client).status_code == 302
    client.force_login(django_user_model.objects.create_user(username="sin_rol"))
    assert client.get("/agente/").status_code == 403
    assert _adjuntar(client).status_code == 403
    assert _preguntar(client, "hola").status_code == 403


@override_settings(AGENTE_ACTIVO=True)
def test_chat_muestra_menu_completo_y_no_menciona_kardex_selector(
    client, usuario_ficticio
):
    client.force_login(usuario_ficticio)
    html = client.get("/agente/").content.decode()
    assert "Expedientes" in html
    assert "Estudio de título" in html
    assert 'id="kardex"' not in html


@override_settings(AGENTE_ACTIVO=True)
def test_adjuntar_devuelve_el_texto_completo_y_no_guarda_nada(client, usuario_ficticio):
    client.force_login(usuario_ficticio)
    largo = b"".join(b"Linea ficticia %03d de la partida.\n" % i for i in range(200))
    r = _adjuntar(client, contenido=largo)
    assert r.status_code == 200
    # regresión: validar_archivo solo devuelve 16 bytes de firma; llegaba truncado
    assert r.json()["texto"].count("Linea ficticia") == 200
    assert "Linea ficticia 199" in r.json()["texto"]
    assert not ConsultaAgente.objects.exists()


@override_settings(AGENTE_ACTIVO=True, AGENTE_MAX_ADJUNTO=10)
def test_adjuntar_rechaza_tamano_formato_y_firma(client, usuario_ficticio):
    client.force_login(usuario_ficticio)
    assert _adjuntar(client, contenido=b"x" * 11).status_code == 400  # > límite
    with override_settings(AGENTE_MAX_ADJUNTO=10_000):
        assert _adjuntar(client, "virus.exe", b"MZ").status_code == 400  # formato
        assert _adjuntar(client, "falso.pdf", b"no es pdf").status_code == 400  # firma


@override_settings(AGENTE_ACTIVO=True)
def test_responde_pasa_documentos_e_historial_y_audita_sin_contenido(
    client, usuario_ficticio, monkeypatch
):
    visto = {}

    def falso(pregunta, documentos, historial):
        visto.update(documentos=documentos, historial=historial)
        return "Faltan 2 documentos. Fuentes: https://www.sunarp.gob.pe", []

    monkeypatch.setattr("agente.views.consultar", falso)
    client.force_login(usuario_ficticio)
    previo = [{"rol": "usuario", "texto": "hola"}, {"rol": "otro", "texto": "x"}]
    docs = [{"nombre": "partida.txt", "texto": "Area 120 m2"}, {"nombre": 5}]
    r = _preguntar(client, "estudio de título", documentos=docs, historial=previo)
    assert "Faltan 2" in r.json()["respuesta"]
    assert r.json()["aviso"] == ""
    assert visto["historial"] == [("usuario", "hola")]
    assert visto["documentos"] == [
        {"nombre": "partida.txt", "texto": "Area 120 m2", "aviso": ""}
    ]
    c = ConsultaAgente.objects.get()
    assert (c.usuario, c.adjuntos, c.ok) == (usuario_ficticio, 1, True)


@override_settings(AGENTE_ACTIVO=True)
def test_errores_van_en_json_y_se_audita_el_fallo(
    client, usuario_ficticio, monkeypatch
):
    client.force_login(usuario_ficticio)

    def falla(*a):
        raise services.AgenteError("sin sesión")

    monkeypatch.setattr("agente.views.consultar", falla)
    r = _preguntar(client, "hola")
    assert (r.status_code, r.json()) == (503, {"error": "sin sesión"})
    assert _preguntar(client, "   ").status_code == 400
    assert ConsultaAgente.objects.get().ok is False


def test_documentos_van_por_stdin_con_su_nombre_y_sin_claves_del_erp(monkeypatch):
    monkeypatch.setenv("DB_PASSWORD", "clave-ficticia")
    monkeypatch.setenv("CLAVE_AJENA_FICTICIA", "x")
    captura = {}

    def run(cmd, **kw):
        captura.update(cmd=cmd, **kw)
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    assert services.consultar(
        "pregunta", [_doc("partida.txt", "SECRETO-FICTICIO")]
    ) == (
        "ok",
        [],
    )
    assert "=== partida.txt ===" in captura["input"]
    assert "SECRETO-FICTICIO" in captura["input"]
    assert "SECRETO-FICTICIO" not in " ".join(captura["cmd"])
    assert "DB_PASSWORD" not in captura["env"]
    assert "CLAVE_AJENA_FICTICIA" not in captura["env"]


def test_cmd_claude_solo_busca_en_la_web():
    cmd, _ = services._claude("sis")
    assert cmd[cmd.index("--tools") + 1] == "WebSearch"
    assert "Bash" not in " ".join(cmd)
    assert "Edit" not in " ".join(cmd)


def test_codex_apagado_por_defecto():
    assert "codex" not in services.PROVEEDORES


def test_cmd_codex_no_hereda_la_config_personal_y_acepta_modelo(settings):
    settings.AGENTE_CODEX_MODELO = "modelo-ficticio"
    cmd, salida = services._codex("sis")
    salida.unlink()
    assert cmd.index("--search") < cmd.index("exec")
    assert "--ignore-user-config" in cmd
    assert cmd[cmd.index("-m") + 1] == "modelo-ficticio"
    assert "read-only" in cmd


def test_timeout_cli_ausente_y_sesion_vencida_son_errores_amigables(monkeypatch):
    for exc in (subprocess.TimeoutExpired("x", 1), FileNotFoundError()):

        def run(*a, exc=exc, **k):
            raise exc

        monkeypatch.setattr(subprocess, "run", run)
        with pytest.raises(services.AgenteError):
            services.consultar("p")

    def vencida(cmd, **kw):
        return subprocess.CompletedProcess(
            cmd, 1, stdout="Failed to authenticate: OAuth session expired", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", vencida)
    with pytest.raises(services.AgenteError, match="claude auth login"):
        services.consultar("p")


def test_prompt_es_de_estudio_de_titulo_y_trata_documentos_como_datos():
    p = services.prompt_sistema()
    assert "estudio de título" in p
    assert "Falta" in p
    assert "Fuentes:" in p
    assert "no instrucciones" in p
    assert "RENIEC" in p


def test_el_recorte_nunca_es_silencioso_ni_deja_documentos_vacios(settings):
    settings.AGENTE_MAX_CONTEXTO = 10
    texto, recortados = services.contexto_documentos(
        [_doc("a.txt", "x" * 6), _doc("b.txt", "y" * 20), _doc("c.txt", "z" * 5)]
    )[:2]
    assert recortados == ["b.txt", "c.txt"]  # b cortado, c omitido por completo
    assert "yyyy" in texto
    assert "zzzzz" not in texto
    assert (
        services.contexto_documentos([_doc("a.txt", "x" * 10)])[1] == []
    )  # justo en el límite


def test_el_modelo_recibe_el_aviso_de_estudio_parcial(settings, monkeypatch):
    settings.AGENTE_MAX_CONTEXTO = 5
    captura = {}

    def run(cmd, **kw):
        captura.update(kw)
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    _, recortados = services.consultar("p", [_doc("partida.txt", "x" * 50)])
    assert recortados == ["partida.txt"]
    assert "AVISO DEL SISTEMA" in captura["input"]
    assert "PARCIAL" in captura["input"]
    services.consultar("p", [_doc("partida.txt", "xx")])
    assert "AVISO DEL SISTEMA" not in captura["input"]


@override_settings(AGENTE_ACTIVO=True, AGENTE_MAX_CONTEXTO=5)
def test_la_respuesta_trae_el_aviso_de_recorte_para_el_abogado(
    client, usuario_ficticio, monkeypatch
):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr=""),
    )
    client.force_login(usuario_ficticio)
    r = _preguntar(
        client, "estudio", documentos=[{"nombre": "partida.txt", "texto": "x" * 50}]
    )
    assert "partida.txt" in r.json()["aviso"]
    assert "parcial" in r.json()["aviso"]
    assert "límite 5" in r.json()["aviso"]


def _pdf_de_paginas(textos):
    """PDF real con una página por texto (vacío = página sin capa de texto)."""
    import pymupdf

    doc = pymupdf.open()
    for texto in textos:
        pagina = doc.new_page()
        if texto:
            pagina.insert_text((72, 72), texto)
    return doc.tobytes()


@override_settings(AGENTE_ACTIVO=True)
def test_pdf_de_varias_paginas_casi_vacio_se_marca_como_lectura_deficiente(
    client, usuario_ficticio
):
    client.force_login(usuario_ficticio)
    escaneo = _pdf_de_paginas(["Sello ficticio"] + [""] * 4)
    r = _adjuntar(client, "escaneo.pdf", escaneo)
    assert r.status_code == 200
    assert "escaneo" in r.json()["aviso"]
    assert "5 páginas" in r.json()["aviso"]
    normal = _pdf_de_paginas(
        ["\n".join(f"Linea {i} ficticia de la partida registral." for i in range(40))]
        * 2
    )
    assert _adjuntar(client, "normal.pdf", normal).json()["aviso"] == ""


def test_el_modelo_recibe_la_marca_de_lectura_deficiente(monkeypatch):
    captura = {}

    def run(cmd, **kw):
        captura.update(kw)
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    services.consultar(
        "p", [_doc("escaneo.pdf", "poco", aviso="Se leyeron solo 4 caracteres")]
    )
    assert "[LECTURA DEFICIENTE:" in captura["input"]
    assert "AVISO DEL SISTEMA" in captura["input"]
    assert "escaneo.pdf" in captura["input"]


def test_el_adjunto_no_deja_copia_en_la_cache_de_ocr(tmp_path, monkeypatch):
    from adaptadores import extraccion

    monkeypatch.setattr(extraccion, "CACHE", tmp_path / "cache")
    ruta = tmp_path / "a.png"
    ruta.write_bytes(b"datos")
    llamadas = []
    resultado = extraccion._cacheado(
        ruta.read_bytes(), lambda: llamadas.append(1) or ["texto ficticio"], False
    )
    assert resultado == ["texto ficticio"]
    assert not (tmp_path / "cache").exists()
