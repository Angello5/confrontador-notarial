# Feature Specification: F20 · Manifiesto de auditoría, catálogo de reglas versionado y severidad

**Feature Branch**: `f20-manifiesto`

**Created**: 2026-09-28

**Status**: Implementado e integrado (PR #51)

**Input**: Anexo A del contrato, fase CONSTRUCCIÓN: capa 5 «Motor de reglas: catálogo versionado y legible», capa 6 «asignación de severidad», capa 7 «Manifiesto de auditoría: registro inmutable de la corrida». Anexo B: P-01 (tres corridas idénticas → informes idénticos), P-06 (100 % de corridas con versión del catálogo y hashes de entrada), P-07 (interrupción → estado recuperable sin pérdida), P-08 (100 % de los casos reconstruible desde el manifiesto). Hoy `confrontar_borrador()` no persiste nada y las severidades no existen.

## Principio

**Cada confrontación deja un registro inmutable que basta para repetirla y comprobar que da lo mismo.**

## Requirements *(mandatory)*

- **FR-001 (catálogo)**: `nucleo/catalogo_reglas.toml` (leído con `tomllib` de la biblioteca estándar) tiene `version` y una tabla por regla con `descripcion` y `severidad` (`ALTA`, `MEDIA`, `BAJA`): NOMBRE, DNI, PARTIDA, MONTO, PARRAFO, NUMERO_EN_LETRAS, DOCUMENTO_CRUZADO, DOCUMENTO_SIN_TITULAR, ESTADO_CIVIL_DISCREPANTE, CONYUGE_NO_MENCIONADO, MENOR_DE_EDAD, DOMICILIO_NO_ENCONTRADO, ORTOGRAFIA, y RUC y DIRECCION reservadas para las fases que las agregan.
- **FR-002 (severidad)**: Cada observación del resultado (`personas`, `regla`, `ortografia`) lleva `severidad` tomada del catálogo por su campo o tipo. Un campo que no está en el catálogo recibe `default_severidad` y no rompe. La pantalla de resultado muestra la severidad.
- **FR-003 (corrida)**: Cada confrontación crea una `Corrida` con: expediente, id y hash del borrador, por cada entrada (borrador y fuentes, en el orden usado) rol, nombre, hash del archivo, `version_extractor` y hash SHA-256 del texto extraído; versión del catálogo; versión del software; usuario; fecha y hora; fecha de referencia (la usada por MENOR_DE_EDAD); estado (`RESULTADO`, `ADVERTENCIA`, `NO_DISPONIBLE`, `ERROR`); hallazgos en JSON canónico (`sort_keys`, sin espacios, UTF-8) y su huella SHA-256.
- **FR-004 (hallazgos)**: Los hallazgos son `estado`, `mensaje`, `personas`, `regla` y `ortografia` del resultado, tal como se muestran en pantalla (con severidad). No incluyen el resumen de extracción.
- **FR-005 (inmutable)**: `Corrida` y `DecisionCorreccion` no se editan ni se borran: `save()` sobre una fila existente, `delete()` y `update()`/`delete()` de su queryset lanzan error; no se registran en el admin; el expediente y los usuarios quedan protegidos (`PROTECT`).
- **FR-006 (decisiones)**: `DecisionCorreccion` (FK a `Corrida`, usuario confirmante, fecha y hora, correcciones excluidas en JSON) queda lista para la fase que aplica correcciones; esta fase no la crea.
- **FR-007 (reconstruir)**: `manage.py reconstruir_corrida <id>` localiza cada texto por hash del archivo + `version_extractor`, comprueba el hash del texto, vuelve a confrontar con la fecha de referencia registrada y compara la huella. Informa `CONFORME` o la diferencia (huellas y número de hallazgos, sin contenido) y termina con error si no es conforme o falta un texto. Si la versión actual del catálogo difiere de la registrada, lo informa; no reconstruye catálogos antiguos.
- **FR-008 (historial)**: «Historial de confrontaciones» del expediente: lista de corridas (fecha, usuario, estado, versión de reglas, hallazgos por severidad) y detalle de solo lectura. Mismos permisos que el expediente.
- **FR-009 (P-07)**: Si la confrontación falla a medias, la corrida queda en `ERROR` con el mensaje seguro, sin hallazgos parciales y sin tocar documentos; nada se escribe en el log. Una corrida ERROR se reconstruye como ERROR si el fallo persiste.
- **FR-010 (privacidad)**: La corrida no aparece en el sondeo JSON ni en logs. Los hashes de texto permiten detectar la supresión (Ley 29733): tras `suprimir_texto_expediente` la corrida deja de ser reconstruible y el comando lo dice.

## Success Criteria *(mandatory)*

- **SC-001 (P-01)**: Tres confrontaciones del mismo borrador con las mismas fuentes producen tres corridas con la misma huella.
- **SC-002 (P-06)**: Toda corrida, en cualquier estado, registra la versión del catálogo y los hashes de las entradas disponibles.
- **SC-003 (P-08)**: `reconstruir_corrida` da `CONFORME` para una corrida recién creada.
- **SC-004 (P-07)**: Un fallo en el núcleo deja una corrida `ERROR` sin hallazgos y los documentos sin cambios.

## Clarifications

- [NEEDS CLARIFICATION] Severidades. Por defecto: ALTA para datos de validación obligatoria (NOMBRE, DNI, RUC, PARTIDA, MONTO, NUMERO_EN_LETRAS, DIRECCION, DOCUMENTO_CRUZADO, DOCUMENTO_SIN_TITULAR); MEDIA para reglas de persona (ESTADO_CIVIL_DISCREPANTE, CONYUGE_NO_MENCIONADO, MENOR_DE_EDAD, DOMICILIO_NO_ENCONTRADO) y PARRAFO; BAJA para ORTOGRAFIA; MEDIA para un campo desconocido.
- [NEEDS CLARIFICATION] Versión del software. Por defecto `ERP_VERSION` en `config/settings.py` (`0.20.0`), que se incrementa junto con `sonar.projectVersion` al publicar.
- [NEEDS CLARIFICATION] Lista de hallazgos. Se conserva el orden en que el núcleo los produce (determinista); «ordenado» se aplica a las claves del JSON.

## Assumptions

- Sin dependencias nuevas: `tomllib`, `hashlib` y `json` son de la biblioteca estándar.
- El núcleo no lee archivos (Principio II): `services.py` lee el TOML una vez al importar.
- La reconstrucción usa instancias `Documento` no guardadas con el texto localizado; `confrontar_borrador` acepta fuentes y fecha explícitas.
