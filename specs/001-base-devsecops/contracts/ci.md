# Contrato CI · F1

Interfaz externa entre GitHub Actions, SonarQube Cloud y protección de `main`. Sin endpoints nuevos del ERP.

## Entorno

Python 3.13 tanto en CI como localmente; runner CI Ubuntu 24.04. Validar dependencias fijadas en esa versión antes de activar workflows.

## Arranque único en dos PRs

- **PR 1 (etapas 1–5)**: solo `lint`, `tests`, `dependencies` y `secrets`, todos en verde antes del merge. No incluye `sonar` ni `ci-required`; no hay un agregado rojo que se ignore. Commit/push, PR en borrador, validación de cuatro checks, merge y comprobación de main por separado. No usar bypass.
- **Entre PRs**: el usuario conecta Cloud privado y realiza el primer análisis de main saneada con cobertura de esa revisión. `sonar-project.properties` estará preparado antes de conectar; no analizar commits anteriores ni exponer historia sensible. No se solicita ningún secreto en chat.
- **PR 2 (etapa 6)**: añade los jobs `sonar` y `ci-required` definidos abajo, gate y protección final. Incluye enmienda constitucional para TODO(SONAR) y esta excepción única de arranque. Desde PR 2 todos los controles son obligatorios.

## Eventos y resultados

- Cada apertura, reapertura o actualización de PR y cada push a `main` inicia controles; sin filtros por rutas. La revisión evaluada y la base del PR se registran explícitamente.
- Nombres de jobs estables en el estado final (PR 2): `lint`, `tests`, `sonar`, `dependencies`, `secrets`, `ci-required`. Verificar los nombres de checks realmente publicados antes de exigirlos en protección.
- `ci-required` depende de los cinco jobs y usa `always()`: únicamente aprueba si todos existen y terminaron con `success`. Nunca aceptar `skipped`, `neutral`, cancelación o ausencia. Usa exactamente `needs: [lint, tests, sonar, dependencies, secrets]`, `if: always()` y un solo paso, sin checkout ni script propio:

```yaml
ci-required:
  needs: [lint, tests, sonar, dependencies, secrets]
  if: always()
  runs-on: ubuntu-24.04
  steps:
    - run: test "${{ join(needs.*.result, ',') }}" = "success,success,success,success,success"
```

- No `continue-on-error`. Si falla tests, Sonar puede quedar omitido por dependencia; el conjunto y agregado deben quedar bloqueados, nunca aparentar un análisis ejecutado.

| Job | Entrada | Éxito exigido |
|---|---|---|
| lint | Código de la revisión | ruff check y format --check sin errores. |
| tests | Revisión + fixtures generados | Casos recolectados, tests aprobados, XML de cobertura válido/no vacío. Marker local_reference no ejecutado. |
| sonar | Misma revisión + cobertura de su ejecución | Análisis Cloud privado terminado y Quality Gate OK calculado para esa revisión; timeout/estado ausente falla. |
| dependencies | Requisitos productivos y de desarrollo, transitivas resueltas | pip-audit estricto sin hallazgos no exceptuados ni errores de resolución. |
| secrets | Árbol actual y cambios introducidos por la revisión | gitleaks con salida redactada sin hallazgos ni errores. Rango de commits explícito; no ocultar nuevos secretos borrados antes del último commit. |

Checkout: historial completo para SCM, sin publicar `.git` ni analizar revisiones anteriores a la baseline saneada. Verificación del contenido y metadatos transmisibles antes del primer envío; no asumir que un clone superficial demuestra privacidad.

Cobertura: `coverage.xml`, rutas relativas al checkout, solo código productivo en el denominador. Archivo transferido dentro del mismo workflow e intento; no buscar el último artefacto disponible de otra ejecución. No transferir expedientes, capturas OCR ni directorios de trabajo completos. Retención de cobertura: 7 días, acceso privado.

Escaneo de secretos histórico previo: ejecutar localmente con redacción; no imprimir rutas históricas sensibles en CI. La falta de reescritura de historia no permite conservar un secreto activo: un hallazgo real exige tratamiento y rotación por el responsable antes de considerar CI limpio. No fabricar una lista global de exclusiones de historia.

## Reglas de seguridad de Ruff

En `pyproject.toml`, `[tool.ruff.lint.per-file-ignores]` permite únicamente `S101` para `"test_*.py"` y `"tests/**"`. No se justifica cada assert: la política de pruebas se documenta una vez en el PR. S101 sigue activo fuera de esos patrones y todas las demás reglas S permanecen activas sin exclusiones, incluidas las pruebas.

## Protección y confianza

`main`: PR obligatorio, los seis checks requeridos, rama actualizada, cero reviews requeridas mientras haya un mantenedor, sin force push, sin bypass ni escrituras directas. Cambiar un nombre de job exige actualizar y verificar la protección conjuntamente.

Jobs sin token de Sonar para instalar dependencias/ejecutar tests. Escaneo en runner separado; token exclusivamente en ese paso. Fork sin secreto: error explícito y PR bloqueado. Dependabot: secreto en su almacén correspondiente, mismo nombre, alcance mínimo. El código/configuración de workflow no confiable no se ejecuta con secretos por el mero hecho de estar en un PR.

## Gate y activación

Gate personalizado: nuevas vulnerabilidades=0, nuevos bugs=0, hotspots revisados=100 %, cobertura nueva>=80 %, tolerancia de cambios pequeños desactivada. Cero bugs nuevos es deliberadamente más estricto que el mínimo constitucional por gravedad. Ante cambio sin líneas productivas nuevas, verificar la semántica del servicio: un gate calculado OK sin condición de cobertura aplicable es admisible, pero un informe global ausente o gate no calculado falla.

Conectar Cloud solo después del merge de PR 1, saneamiento y comprobación de capacidades privadas. El usuario realiza el primer análisis de esa main; en PR 2 se activa el análisis desde workflow y la protección completa. F1 no se declara implantada por la mera presencia del YAML. Historial sensible nunca se publica ni se envía al analizador; si una configuración requiere enviarlo, activación bloqueada.

## Hallazgos existentes y código nuevo

Después del primer análisis de main, vulnerabilidades, bugs y Security Hotspots existentes se corrigen o justifican individualmente por escrito en PR 2. Los code smells existentes se registran con enlace/ID en `docs/deuda-f3.md` y no bloquean. Esto no excluye código del análisis, no desactiva reglas Ruff ni reduce umbrales de código nuevo.

## Checkpoints de integración

Cada PR sigue validación previa → commit/push → apertura/actualización de PR → checks requeridos verdes → merge → verificación de main. PR 1 exige cuatro checks; PR 2 exige los cinco controles y el agregado. No se exige ensayo de forks ni escenario separado de SHA obsoleto; se conserva rama actualizada y la prohibición de `pull_request_target`.
