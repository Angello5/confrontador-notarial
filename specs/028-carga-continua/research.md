# Investigación

- Mantener precomputación y añadir intención persistente evita perder trabajo adelantado.
- Investigación independiente: recuperación ciega a 15 minutos duplica OCR; la restricción de caché evita filas duplicadas pero no cómputo duplicado. Usar locks PostgreSQL de sesión y reconsulta.
- Snapshot único para cálculo y registro: hoy registrar_corrida vuelve a consultar fuentes y puede incluir documentos no comparados.
- Reutilización incorpora versión de software y fecha por reglas de edad.
- Intercalar comparación y vista entre documentos; no activar consumidores extra en producción sin medición.
- Mantener tipografía y marca; quitar porcentajes ficticios y listas duplicadas.
- Sin hooks de extensiones. Clarify: alcance, cancelación, errores y privacidad resueltos en propuesta aprobada y límites de spec.md.
