import os
import subprocess
import tempfile
import threading
from pathlib import Path

from django.conf import settings

from adaptadores import extraccion
from expedientes.services import validar_archivo


# Cada .md de prompt/ es una «skill»: añadir una es soltar un archivo.
PROMPT = Path(__file__).parent / "prompt"
_cupo = threading.BoundedSemaphore(settings.AGENTE_SIMULTANEAS)


class AgenteError(Exception):
    """Mensaje apto para mostrar al usuario; nunca lleva contenido de documentos."""


def prompt_sistema():
    return "\n\n".join(
        p.read_text(encoding="utf-8") for p in sorted(PROMPT.glob("*.md"))
    )


MIN_CARACTERES_PAGINA = 200  # menos que esto por página sugiere un escaneo sin leer


def leer_adjunto(archivo):
    """Texto de un archivo adjunto y, si se leyó casi vacío, un aviso. El archivo es
    temporal: se escribe, se lee con el extractor del ERP y se borra siempre; nada
    queda en disco ni en la base."""
    if archivo.size > settings.AGENTE_MAX_ADJUNTO:
        raise AgenteError("El archivo supera los 10 MB permitidos.")
    try:
        validar_archivo(archivo)  # solo valida; devuelve apenas el prefijo de la firma
    except ValueError as e:
        raise AgenteError(str(e)) from None
    archivo.seek(0)
    contenido = archivo.read()
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / f"adjunto{Path(archivo.name).suffix.lower()}"
        ruta.write_bytes(contenido)
        try:
            informe = extraccion.leer_con_calidad(ruta)
        except Exception:
            raise AgenteError("No se pudo leer el archivo.") from None
    texto = informe["texto"].strip()
    if not texto:
        raise AgenteError("No se encontró texto legible en el archivo.")
    paginas = len(informe["calidad"]["paginas"]) or 1
    aviso = ""
    if paginas >= 2 and len(texto) / paginas < MIN_CARACTERES_PAGINA:
        aviso = (
            f"Se leyeron solo {len(texto):,} caracteres en {paginas} páginas: "
            "probablemente es un escaneo sin texto legible. Pida el original o una copia en Word."
        )
    return {"texto": texto, "aviso": aviso}


def contexto_documentos(documentos):
    """Une los documentos hasta AGENTE_MAX_CONTEXTO caracteres. Devuelve el texto, los
    nombres recortados u omitidos y los de lectura deficiente: ninguno es silencioso."""
    partes, total, recortados, deficientes = [], 0, [], []
    for d in documentos:
        resto = max(0, settings.AGENTE_MAX_CONTEXTO - total)
        if len(d["texto"]) > resto:
            recortados.append(d["nombre"])
        texto = d["texto"][:resto]
        total += len(texto)
        marca = ""
        if d.get("aviso"):
            deficientes.append(d["nombre"])
            marca = f"[LECTURA DEFICIENTE: {d['aviso']}]\n"
        partes.append(f"=== {d['nombre']} ===\n{marca}{texto}")
    return "\n\n".join(partes), recortados, deficientes


def _claude(sistema):
    return [
        "claude",
        "-p",
        "--system-prompt",
        sistema,
        "--tools",
        "WebSearch,WebFetch",
        "--permission-mode",
        "dontAsk",
        "--allowedTools",
        "WebSearch,WebFetch",
        "--disable-slash-commands",
        "--strict-mcp-config",
        "--no-session-persistence",
    ], None


def _codex(sistema):
    salida = Path(tempfile.mkstemp(suffix=".txt")[1])
    # --ignore-user-config: no hereda el modelo, el esfuerzo ni los hooks personales.
    # --search es opción del `codex` principal (0.167+), va antes de `exec`.
    cmd = ["codex", "--search", "exec", "--ignore-user-config", "-s", "read-only"]
    if settings.AGENTE_CODEX_MODELO:
        cmd += ["-m", settings.AGENTE_CODEX_MODELO]
    return [
        *cmd, "-c", "model_reasoning_effort=low", "--ephemeral",
        "--skip-git-repo-check", "-o", str(salida), "-",
    ], salida  # fmt: skip


# Lista de permitidos, no de bloqueo: ninguna clave del ERP llega al agente.
ENTORNO_PERMITIDO = (
    "PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT",
    "USERPROFILE", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "APPDATA", "LOCALAPPDATA", "PATHEXT", "COMSPEC",
)  # fmt: skip
PROVEEDORES = {"claude": _claude}
# codex no puede quitarse el shell: con `-s read-only` aún lee el disco. Solo con
# opt-in explícito y en un usuario del sistema sin acceso al ERP ni a sus claves.
if settings.AGENTE_CODEX_PERMITIDO:
    PROVEEDORES["codex"] = _codex


def consultar(pregunta, documentos=(), historial=()):
    """Devuelve (respuesta, documentos_recortados). La pregunta y los documentos van por
    stdin (no por argumentos, que `ps` deja ver). Corre en un directorio vacío
    y sin las claves del ERP en el entorno."""
    proveedor = settings.AGENTE_PROVEEDOR
    if proveedor not in PROVEEDORES:
        raise AgenteError("Proveedor del agente no configurado.")
    prompt = ""
    if historial:
        prompt += "Conversación previa (de más antigua a más reciente):\n"
        prompt += "\n".join(f"{rol.upper()}: {texto}" for rol, texto in historial)
        prompt += "\n\n"
    prompt += f"Pregunta del abogado:\n{pregunta}"
    recortados = deficientes = []
    if documentos:
        contexto, recortados, deficientes = contexto_documentos(documentos)
        prompt += f"\n\nDocumentos del cliente:\n{contexto}"
    if deficientes:
        prompt += (
            "\n\nAVISO DEL SISTEMA: se leyeron casi vacíos (probables escaneos): "
            + ", ".join(deficientes)
            + ". No concluyas que falta lo que pudo estar en ellos: ponlos en «Falta» "
            "como «lectura ilegible, pedir mejor copia»."
        )
    if recortados:
        prompt += (
            "\n\nAVISO DEL SISTEMA: por tamaño se recortó o se omitió el final de: "
            + ", ".join(recortados)
            + ". El estudio es PARCIAL: dilo en la Conclusión y no afirmes «No consta» "
            "sobre lo que pudo estar en la parte cortada."
        )
    sistema = prompt_sistema()
    cmd, salida = PROVEEDORES[proveedor](sistema)
    if proveedor == "codex":  # codex no tiene opción de system prompt
        prompt = f"{sistema}\n\n---\n\n{prompt}"
    env = {k: os.environ[k] for k in ENTORNO_PERMITIDO if k in os.environ}
    if not _cupo.acquire(blocking=False):
        raise AgenteError("El agente está atendiendo otras consultas. Reintente.")
    try:
        with tempfile.TemporaryDirectory() as vacio:
            r = subprocess.run(  # noqa: S603 - argv fijo; la entrada va por stdin
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=settings.AGENTE_TIMEOUT,
                cwd=vacio,
                env=env,
            )
        texto = salida.read_text(encoding="utf-8") if salida else r.stdout
    except subprocess.TimeoutExpired:
        raise AgenteError("El agente tardó demasiado. Reformule o reintente.") from None
    except FileNotFoundError:
        raise AgenteError(f"No se encontró «{cmd[0]}» en el servidor.") from None
    finally:
        _cupo.release()
        if salida:
            salida.unlink(missing_ok=True)
    if r.returncode or not texto.strip():
        if "authenticate" in (r.stderr + r.stdout).lower():
            raise AgenteError(
                "La sesión de Claude del servidor venció. Ejecute «claude auth login» en el servidor."
            )
        raise AgenteError(
            "El agente no pudo responder. Revise su sesión en el servidor."
        )
    return texto.strip(), recortados
