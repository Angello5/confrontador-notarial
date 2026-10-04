# Datos

SolicitudConfrontacion: OneToOne borrador CASCADE, usuario PROTECT, token UUID, estado PENDIENTE/PROCESANDO/LISTO/ERROR/CANCELADA/CAMBIADA, solicitada_el y actualizada_el. Sin texto. Solicitar reutiliza una activa; reintento genera otro token. Solo token vigente publica. Corrida inmutable existente.
Documento: métricas JSON con duraciones recepción servidor, cola y lectura/reutilización. Corrida.presentacion conserva métricas de análisis sin contenido.
Locks por tarea e identidad determinística; coordinación transitoria, liberada al cerrar conexión.
