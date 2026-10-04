# Contrato: vistas del borrador (F32)

Ambas vistas: `@login_required`, `@require_GET`, `_requiere_rol`, `_expediente_visible(pk)` y
`doc_id` con `rol=BORRADOR` dentro del expediente; si no, 404. Las dos responden con
`Cache-Control: no-store` y `X-Content-Type-Options: nosniff`.

`?corrida=<id>` es obligatorio. Debe ser una corrida del expediente con `id_borrador = doc_id`; si
no lo es, 404. Así los recuadros siempre corresponden al resultado que ve el usuario.

## GET `/expedientes/<pk>/documentos/<doc_id>/vista/?corrida=<id>`

`200 application/json`:

```json
{
  "estado": "LISTA",
  "motivo": null,
  "paginas": [{"numero": 1, "proporcion": 1.414}],
  "marcas": {
    "r1": [{"pagina": 1, "x0": 0.12, "y0": 0.40, "x1": 0.31, "y1": 0.42, "aparicion": 0}]
  },
  "no_ubicadas": [{"id": "r4", "motivo": "AUSENTE"}]
}
```

Si `estado` es `PREPARANDO`, el worker todavía no convirtió el borrador: los demás campos van vacíos
y el navegador vuelve a consultar cada 3 s. Si `estado` es `NO_DISPONIBLE`, `paginas` y `marcas`
están vacíos, `no_ubicadas` también, y `motivo` lleva uno de los códigos de abajo. Siempre se responde `200`: no es un error de la
petición. Ningún campo lleva rutas, nombres de archivo ni texto del documento.

| `motivo` | Mensaje en pantalla |
|---|---|
| `FORMATO` | "La vista de páginas aún no está disponible para este formato de borrador. Use la lista de observaciones." |
| `SIN_ORIGINAL` | "El archivo del borrador ya no está guardado. Vuelva a cargarlo y a confrontar para ver sus páginas." |
| `VERIFICACION` | "No se pudo verificar que el borrador guardado sea el original. Vuelva a cargarlo." |
| `CONVERSION` | "No se pudo preparar la vista del borrador. Intente de nuevo; si persiste, avise al administrador." |
| `CORRIDA` | "Este resultado es anterior a la vista de páginas. Vuelva a confrontar para verlas." |

| `no_ubicadas.motivo` | Texto en la observación |
|---|---|
| `AUSENTE` | "No ubicada en el borrador: el dato falta en el documento." |
| `NO_EN_PAGINA` | "No ubicada en la página: revise la línea indicada." |

## GET `/expedientes/<pk>/documentos/<doc_id>/vista/<n>/?corrida=<id>`

- `200 image/png`: la página `n` (desde 1), a 110 ppp.
- `404` si `n` está fuera de rango o la vista está `NO_DISPONIBLE`.
- No admite otros parámetros: el tamaño se ajusta en el navegador con CSS.

## Plantilla (contrato con Alpine)

- Cada `li[data-id]` de la lista conserva su `data-id` (`p<n>`, `r<n>` u `o<n>`) y su `data-sev`.
- El visor pinta un `<button class="marca-pagina" data-obs="r1" data-sev="ALTA">` por rectángulo,
  posicionado en `%` sobre la imagen.
- `elegir(id)` desplaza la vista a la primera aparición de la observación. El clic en una marca
  llama a `elegir(data-obs)`.
