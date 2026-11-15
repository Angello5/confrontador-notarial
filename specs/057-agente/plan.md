# Implementation Plan: F75 · Agente de estudio de título

**Spec**: `specs/057-agente/spec.md`

## Summary

App Django `agente` con tres vistas (pantalla, adjuntar, preguntar), un servicio que lee adjuntos con el extractor del ERP y lanza la CLI del proveedor, y un modelo de auditoría. Skills como `.md`. Sin dependencias nuevas.

## Constitution Check

| Principio | Estado |
|---|---|
| I Determinismo / sin IA externa | **Contradice.** Enmienda 3.0.0 propuesta en la spec; módulo apagado por defecto y sin autoridad sobre hallazgos |
| II Núcleo puro | No toca el núcleo; `services.py` solo orquesta |
| III Pruebas | `tests/test_agente.py` (interruptor, permisos, contexto, argv/entorno, errores) |
| IV Privacidad | Auditoría sin contenido; adjuntos temporales, borrados siempre, sin persistir texto; **abierto**: aceptación de la notaría |
| V Simplicidad | Sin API, SPA, colas ni caché. Tabla de proveedores justificada por dos implementaciones reales |
| VI Seguridad | Login + rol en las tres rutas; herramientas limitadas a búsqueda web; adjuntos validados por contenido; **abierto**: requiere internet |

## Estructura

```text
agente/
  models.py        # ConsultaAgente (auditoría: usuario, adjuntos, proveedor, resultado)
  services.py      # leer_adjunto, contexto_documentos, prompt_sistema, consultar (claude | codex)
  views.py         # consulta, adjuntar, preguntar
  urls.py
  prompt/          # skills: sistema.md (estudio de título), fuentes_peru.md
templates/agente/consulta.html
tests/test_agente.py
```

## Ejecución en otro puerto (desarrollo)

```bash
AGENTE_ACTIVO=1 python manage.py runserver 8001   # la app principal sigue en 8000
```

Variables: `AGENTE_ACTIVO`, `AGENTE_PROVEEDOR` (`claude`|`codex`), `AGENTE_CODEX_PERMITIDO` (opt-in para codex), `AGENTE_CODEX_MODELO` (vacío = el de la CLI), `AGENTE_MAX_ADJUNTO` (10 MB), `AGENTE_MAX_CONTEXTO` (120 000 caracteres), `AGENTE_TIMEOUT` (120), `AGENTE_SIMULTANEAS` (2). Con codex: `AGENTE_ACTIVO=1 AGENTE_PROVEEDOR=codex AGENTE_CODEX_PERMITIDO=1 python manage.py runserver 8001`. Codex requiere la CLI 0.167 o superior. Requiere `claude` o `codex` instalado y con sesión iniciada en la cuenta que corre el servidor.

## Complexity Tracking

Ninguna adición fuera de lo permitido; la única excepción es la constitucional descrita arriba.

## Más allá del chat: cotejo por código y checklist por acto

- **Cotejo determinista** (`agente/cotejo.py`): el código extrae áreas, partidas, montos y señales (hipoteca, embargo, pago en efectivo, poder, casado) de cada documento y calcula las discrepancias entre ellos. El modelo recibe el resultado como «COTEJO DEL SISTEMA» y lo interpreta; lo exacto no lo decide el modelo. Alcance actual: áreas y partidas (si dos documentos no comparten ningún valor, se reporta). Siguiente: nombres, DNI y montos.
- **Checklist por acto** (`agente/actos/<acto>.md`): se carga si la pregunta o los documentos nombran el acto. Hoy solo `compraventa.md`.
  - [NEEDS CLARIFICATION] El checklist de compraventa es un **borrador técnico**; la notaría debe validarlo antes de producción, y definir los de poder, donación y vehicular.
