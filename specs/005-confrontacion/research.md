# Research: F5 · Confrontación

**Alcance**: decisiones técnicas para conectar el texto ya extraído de F4 con
las capas `regla` y `ortografía`. `spec.md` es aprobado y no se reescribe en
esta etapa. La capa de léxico queda fuera de F5.

## Decisiones

### Límites y ubicación de la orquestación

- **Decisión**: reutilizar `expedientes/services.py` para una función de
  confrontación que reciba un expediente y el borrador seleccionado, construya
  el resultado en memoria y devuelva estructuras simples para la vista. La
  vista solo autoriza, valida el estado, llama al servicio y renderiza
  `templates/expedientes/confrontacion.html`.
- **Alternativas descartadas**: importar `app.py` o `app_ortografia.py`
  (son Streamlit y una de ellas importa `experimental/`), poner la lógica en
  la vista (viola las vistas delgadas) o crear una aplicación Django separada
  sin una frontera de dominio real (añade estructura sin entidades nuevas).

### Consumo del núcleo y conservación del comportamiento

- **Decisión**: consumir sin modificar `nucleo.verificar.catalogo`,
  `diagnostico`, `revisar` y `revisar_parrafos`, además de
  `nucleo.ortografia.revisar`. El umbral se fija internamente en `88`; no se
  recibe del formulario ni se muestra al usuario. El orden es diagnóstico,
  reglas (campos y párrafos) y ortografía.
- **Alternativas descartadas**: copiar las expresiones regulares o reimplementar
  la puntuación en `expedientes` (duplicaría la regla y podría cambiar la
  medición), exponer el umbral en la pantalla (contradice FR-008), o ejecutar
  ortografía antes del diagnóstico (haría trabajo y mostraría observaciones de
  un borrador que debe bloquearse).
- **Medición**: la implementación deberá conservar los tests sintéticos
  existentes y añadir una prueba de paridad de la salida de regla sobre datos
  ficticios. La medición privada `local_reference` sigue fuera de CI y se
  ejecuta solo con la selección explícita indicada por el repositorio.

### Fuentes, minutas y nombres de archivo

- **Decisión**: el servicio arma `fuentes` como `dict[str, str]` con la clave
  exacta `Documento.nombre_original` y el texto de cada `Documento` con rol
  `CLIENTE` o `MINUTA`. Se pasa ese diccionario directamente a `catalogo()` y
  `diagnostico()`, porque el núcleo decide si una fuente es imagen leyendo la
  extensión de esa clave. Las minutas para `revisar_parrafos()` son únicamente
  los textos de documentos con rol `MINUTA`; la extensión ya no clasifica el
  rol.
- **Alternativas descartadas**: usar el `pk`, un nombre temporal o una ruta
  reconstruida como clave (rompe la decisión de imagen por extensión y puede
  filtrar detalles del servidor); tratar todos los documentos como minutas
  (incluye identificaciones en la comparación de párrafos); o usar solo la
  primera fuente (omite datos válidos del resto del expediente).

### Diagnóstico, precondiciones y múltiples borradores

- **Decisión**: cada borrador se confronta de forma independiente. El botón
  solo está habilitado para un borrador con texto no vacío cuando existe al
  menos un `CLIENTE` y una `MINUTA` con texto no vacío y todos están en `LISTO`.
  Un documento pendiente/procesándose se muestra como espera; un
  documento con texto suprimido (`texto_extraido` nulo o `texto == ""`) se
  muestra como no disponible y pide volver a subirlo. No se ejecuta el núcleo
  para ninguna precondición fallida.
- Tras las precondiciones, `diagnostico(fuentes, borrador)` se ejecuta primero.
  Si devuelve aviso, se devuelve un estado de advertencia y no se llaman
  `revisar`, `revisar_parrafos` ni ortografía ni se listan observaciones de
  campos. Un resultado sin diferencias es un estado vacío exitoso.
- **Alternativas descartadas**: confrontar contra cadenas vacías (falsea
  faltantes), mezclar varios borradores en un único resultado (pierde la
  correspondencia documento-resultado), o permitir confrontar mientras hay
  extracción pendiente (resultado incompleto).

### Adaptación de observaciones de regla sin cambiar el núcleo

- **Decisión**: añadir en la capa de aplicación un parser pequeño y explícito
  para el formato actual de `list[str]`. El prefijo `[CAMPO]` identifica el
  campo; `«valor» debe decir «esperado»` separa valor hallado y esperado;
  `FALTA: «valor»` produce hallado `No aparece en el borrador` y esperado
  `valor`; `no coincide con ninguna fuente` conserva el valor hallado y usa
  ese mensaje como esperado. Las observaciones `[PARRAFO]` se convierten en
  campo `PARRAFO`, con el porcentaje conservado, hallado `No aparece o fue
  alterado` y esperado el fragmento de fuente que el núcleo devuelve; su
  ubicación puede quedar como `No ubicada` cuando la alteración impide hallar
  el texto.
- Después de parsear, la capa de aplicación ubica el valor hallado en el texto
  original del borrador: calcula número de línea y un fragmento corto de esa
  línea, usando comparación normalizada para tolerar mayúsculas y tildes sin
  cambiar el texto mostrado. Si no lo encuentra, devuelve ubicación nula y un
  mensaje claro. Esto mantiene la ubicación como presentación, no como lógica
  del núcleo.
- **Alternativas descartadas**: cambiar `revisar()` para devolver diccionarios
  o tuplas (altera la API y la medición del núcleo), usar el fragmento de
  contexto que ya trae el string como ubicación (es texto normalizado y no
  contiene número de línea), o inferir campos por orden de la lista (frágil
  ante observaciones faltantes y párrafos).
- **Límite explícito**: el parser se prueba contra los cuatro formatos de
  regla actuales y falla de forma segura si aparece una cadena no reconocida;
  no se inventa una interpretación de negocio. Una salida futura del núcleo
  con formato nuevo requiere actualizar este adaptador y sus pruebas.

### Adaptación de ortografía y palabras aceptadas

- **Decisión**: cargar el diccionario y lemas mediante los adaptadores ya
  fijados (`adaptadores.diccionario`), reutilizar `lista_casa()` y llamar a
  `nucleo.ortografia.revisar(texto, diccionario, lemas, lista, propios)`.
  `propios` es el conjunto de palabras que forman los nombres del catálogo
  (`{palabra for nombre in cat["NOMBRE"] for palabra in nombre.split()}`),
  igual que la vía determinista actual. Cada tupla `(palabra, motivo,
  sugerencia)` se transforma directamente en una observación con palabra
  hallada, motivo, sugerencia (o `Sin sugerencia` para `"?"`) y ubicación
  calculada en el borrador.
- **Alternativas descartadas**: llamar a la firma antigua del shim
  `ortografia.revisar`, incorporar términos de la capa de léxico, permitir
  que el usuario marque términos desde F5, o consultar un modelo/servicio
  externo. No hay cambio de dependencia ni import de `experimental/`.

### Interfaz y seguridad

- **Decisión**: añadir una acción POST protegida por CSRF por borrador listo,
  con una ruta interna bajo `/expedientes/`. La autorización reutiliza
  `usuario_puede_ver_expediente`; la vista no revela si un expediente ajeno
  existe. El resultado se renderiza sin guardarlo, sin crear archivos y sin
  mostrar hashes, rutas ni texto completo.
- La pantalla usa plantillas Django/AdminLTE ya existentes, mensajes en
  español, `role="status"` para estados exitosos y `role="alert"` para
  advertencias. Agrupa `Regla` y `Ortografía`, muestra el recuento, campo,
  hallado, esperado, motivo cuando corresponda y ubicación. El estado de
  cálculo se comunica durante la petición; si la duración real supera un
  segundo, la implementación debe mostrar el indicador aprobado en el
  contrato sin simular un porcentaje.
- **Alternativas descartadas**: persistir resultados (es F6), crear una API
  JSON o SPA (fuera del monolito y del alcance), o revelar el texto completo
  para depurar (contradice privacidad).

## [NEEDS CLARIFICATION]

- No se encontró una decisión de negocio bloqueante en la especificación
  aprobada. Queda como límite técnico documentado si la notaría requiere una
  ubicación de párrafo alterado cuando no existe coincidencia literal: el
  núcleo actual solo devuelve el porcentaje y un prefijo de la fuente; F5
  mostrará `No ubicada` en ese caso. Si la notaría exige otra presentación,
  deberá aclararse antes de implementar y sin modificar el núcleo por cuenta
  propia.

## Errores o contradicciones detectadas en `spec.md`

- La sección **Input** todavía dice que F5 ejecuta regla, léxico y ortografía,
  aunque la aclaración, FR-012 y el roadmap excluyen léxico. Es una
  contradicción editorial que no se corrige aquí porque `spec.md` fue aprobado
  y la instrucción de esta etapa prohíbe reescribirlo.
- `spec.md` pide campo, hallado, esperado y ubicación también para observaciones
  de párrafo, pero el núcleo solo devuelve porcentaje y un prefijo de fuente.
  Esta planificación resuelve el contrato con valores explícitos y `No
  ubicada` cuando no hay hallazgo; el límite queda reportado para revisión de
  negocio.
