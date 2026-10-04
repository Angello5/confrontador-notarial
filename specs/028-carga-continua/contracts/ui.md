# Contratos UI

POST documentos/ Accept application/json: 200 con recibidos, 400 si ninguno; errores individuales seguros. Sin Accept conserva HTML. GET estado/ añade etapa, solicitada y puede_solicitar por borrador, sin textos ni rutas.
POST documentos/<id>/confrontar/: 202 pendiente, 200 resultado reutilizado, 400 faltan roles o hay errores; HTML redirige. Nunca calcula en petición.
POST documentos/<id>/cancelar-confrontacion/: 200 o redirección, mismos permisos y CSRF.
Navegador mantiene cola serial de transferencias sin impedir nuevas selecciones. Confrontar espera transferencias y no continúa si fallan. Aviso al salir con transferencias sin recibir. Estados de lectura y comparación sin porcentajes inventados.
