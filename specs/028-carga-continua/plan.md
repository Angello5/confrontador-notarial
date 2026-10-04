# Implementation Plan: F34 · Carga continua

**Date**: 2026-10-03 | **Spec**: [spec.md](spec.md) | Sin rama: copia sin Git.

## Summary
Django, Alpine y PostgreSQL existentes. Subida XMLHttpRequest con progreso real y cancelación; JSON negociado sobre vistas actuales y fallback HTML. SolicitudConfrontacion persistente por borrador. Comparación anticipada y solicitada comparten ejecución exclusiva, snapshot y publicación condicional. Worker intercala comparación/vista con documentos y ofrece modo continuo opt-in.

## Technical Context
Python 3.13, dependencias fijadas actuales, PostgreSQL, JavaScript y Alpine local. Sin paquetes nuevos ni cambios al núcleo. Pruebas pytest, Node y navegador con datos ficticios. Diez usuarios. Despliegue en servidores fuera de esta sesión.

## Constitution Check
I–III: reglas intactas y tests de integración primero. IV: retención DOCX sin ampliación; telemetría sin textos. V: monolito, misma cola y dependencias. VI: permisos y CSRF. VII: controles locales y migración, CI/Sonar obligatorios para merge. VIII: estados reales, cancelación, teclado y reducción de duplicaciones. Entorno sin .git: no se puede crear worktree/PR; integración pendiente. Revalidación después del diseño: no se requieren enmiendas.

## Project Structure
expedientes/models.py y migrations/: solicitud y métricas mínimas.
expedientes/bloqueos.py: lock PostgreSQL de sesión usado por OCR, caché, comparación y vista.
expedientes/solicitudes.py: solicitar, cancelar y publicar con transacciones breves.
expedientes/services.py: snapshot al registrar; reutilización por versiones/fecha; métricas, OCR protegido y preview anticipado.
expedientes/views.py y urls.py: JSON y solicitudes.
static/js/carga-expediente.js, templates/expedientes/detalle.html y CSS: carga continua.
templates/expedientes/confrontacion.html: visor principal y correcciones.
tests/: HTTP, concurrencia PostgreSQL, cancelación y JS.

## Decisions
Se conserva precomputación automática; cancelación la inhibe hasta nueva solicitud. Un resultado exige entradas, catálogo, software y fecha iguales. Cancelar no mata OCR compartido a mitad de llamada; impide publicar comparación cancelada. Locks de sesión distinguen trabajo vivo de abandonado sin transacciones largas. Caché concurrente se reconsulta bajo lock; si está ocupado se difiere. Worker intercala trabajos acotados.

## Complexity Tracking
Entidad de solicitud necesaria para navegación y cancelación; un booleano del navegador no basta. Locks de sesión evitan hilos de heartbeat y se reutilizan en cuatro tareas concretas.
