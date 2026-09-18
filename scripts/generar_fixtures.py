"""Genera documentos ficticios desde cero, sin leer expedientes ni usar red.

Ejecutar desde el repositorio: python scripts/generar_fixtures.py
Los formatos binarios legacy se convierten en los tests (etapa 3 en Linux).
"""
from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo

import openpyxl
import pymupdf

DESTINO = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
NOTA = "NOTA DE PRUEBA: CONSTACIA DEL DOCUMENTO (3)"
PERSONAS = ["ALBA ZURBELIA LUMARIA", "BRUNO TELURIO VENTORIA",
            "CLARA FICTELIA SOLARIA", "MARIA NUBELIA RIVORIA"]


def paquete(ruta, partes):
    """ZIP con orden, fecha y permisos fijos, también para normalizar XLSX."""
    with ZipFile(ruta, "w") as z:
        for nombre, contenido in sorted(partes.items()):
            info = ZipInfo(nombre, (2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_STORED
            info.external_attr = 0o600 << 16
            z.writestr(info, contenido)


def parrafo(texto):
    return f'<w:p><w:r><w:t xml:space="preserve">{escape(texto)}</w:t></w:r></w:p>'


def docx(ruta, textos, nota=False, tabla=False):
    cuerpo = "".join(parrafo(t) for t in textos)
    if tabla:
        cuerpo += '<w:tbl><w:tblPr/><w:tblGrid><w:gridCol w:w="3000"/><w:gridCol w:w="3000"/></w:tblGrid>'
        for a, b in [("DNI", "90000004"), ("Partida", "80000001")]:
            cuerpo += f'<w:tr><w:tc>{parrafo(a)}</w:tc><w:tc>{parrafo(b)}</w:tc></w:tr>'
        cuerpo += '</w:tbl><w:p><w:r><w:t>CAMPO</w:t><w:tab/><w:t>VALOR</w:t></w:r></w:p>'
    if nota:
        contenido = f'<w:txbxContent>{parrafo(NOTA)}</w:txbxContent>'
        cuerpo += (
            '<w:p><w:r><mc:AlternateContent><mc:Choice Requires="wps">'
            '<w:drawing><wp:inline><wp:extent cx="4000000" cy="600000"/>'
            '<wp:docPr id="1" name="Nota ficticia"/><a:graphic>'
            '<a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">'
            '<wps:wsp><wps:cNvSpPr txBox="1"/><wps:spPr>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></wps:spPr>'
            f'<wps:txbx>{contenido}</wps:txbx><wps:bodyPr/></wps:wsp>'
            '</a:graphicData></a:graphic></wp:inline></w:drawing></mc:Choice>'
            '<mc:Fallback><w:pict><v:shape id="nota" style="width:300pt;height:50pt">'
            f'<v:textbox>{contenido}</v:textbox></v:shape></w:pict></mc:Fallback>'
            '</mc:AlternateContent></w:r></w:p>'
        )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
           'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
           'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
           'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
           'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
           'xmlns:v="urn:schemas-microsoft-com:vml" mc:Ignorable="wps">'
           f'<w:body>{cuerpo}<w:sectPr/></w:body></w:document>')
    paquete(ruta, {
        '[Content_Types].xml': '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
        '_rels/.rels': '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
        'word/document.xml': xml,
    })


def generar(destino=DESTINO):
    for nombre in ["cliente", "borrador", "resultado", "ajeno", "formatos"]:
        (destino / nombre).mkdir(parents=True, exist_ok=True)
    identidades = [f"{nombre}, DE NACIONALIDAD PERUANA. DNI 9000000{i}."
                   for i, nombre in enumerate(PERSONAS, 1)]
    clausulas = ["PARTIDA ELECTRONICA N° 80000001. MONTO S/ 12,345.67.",
                "OCTAVO DECIMO MEDIO URBANIZACION OCUPACION TIENEN."]
    correcto = identidades + clausulas
    minuta = identidades + [clausulas[0], "OCTAVO DECIMO MEDIO UIRBANIZACION OCUPACIÒN TIENE."]
    malo = [s.replace("90000001", "91000001").replace("90000002", "91000002") for s in identidades]
    malo += ["PARTIDA N° 81000001. MONTO S/ 12,346.67.",
             "OCTAO DECIO MEIO UIRBANIZACION OCUPACIÒN TIENE."]
    docx(destino / "cliente/minuta.docx", minuta)
    docx(destino / "resultado/correcto.docx", correcto)
    docx(destino / "borrador/observado.docx", malo, nota=True)
    docx(destino / "ajeno/plantilla.docx", ["DNI 92000001. DNI 92000002."])
    docx(destino / "formatos/tabla.docx", [], tabla=True)
    (destino / "formatos/texto.txt").write_text("\n".join(correcto) + "\n", encoding="utf-8")
    (destino / "formatos/minuta.rtf").write_text(
        r"{\rtf1\ansi DONACION DE ACCIONES Y DERECHOS\par KARDEX 70001\par}", encoding="ascii")

    with pymupdf.open() as doc:
        pagina = doc.new_page(width=800, height=430)
        for y, etiqueta, valor in [(70, "CUI", "90000004-1"), (140, "NOMBRES", "MARIA"),
                                  (210, "APELLIDO PATERNO", "NUBELIA"),
                                  (280, "APELLIDO MATERNO", "RIVORIA")]:
            pagina.insert_text((30, y), etiqueta, fontsize=21)
            pagina.insert_text((390, y), valor, fontsize=25)
        pagina.insert_text((300, 405), "COPIA FICTICIA", fontsize=25, color=(0.7, 0.7, 0.7),
                            morph=(pymupdf.Point(300, 405), pymupdf.Matrix(25)))
        imagen = pagina.get_pixmap(matrix=pymupdf.Matrix(2, 2))
        imagen.save(destino / "cliente/dni.png")
    with pymupdf.open() as doc:
        pagina = doc.new_page(width=800, height=430)
        pagina.insert_image(pagina.rect, filename=str(destino / "cliente/dni.png"))
        doc.save(destino / "formatos/escaneado.pdf", no_new_id=True)
    with pymupdf.open() as doc:
        pagina = doc.new_page()
        pagina.insert_text((40, 70), "DOCUMENTO FICTICIO PARA PRUEBAS DE EXTRACCION. DNI 90000004.", fontsize=11)
        doc.save(destino / "formatos/texto.pdf", no_new_id=True)

    libro = openpyxl.Workbook()
    libro.properties.created = libro.properties.modified = datetime(2020, 1, 1)
    libro.active.append(["DNI", "90000004"])
    libro.active.append(["Partida", 80000001])
    memoria = BytesIO()
    libro.save(memoria)
    with ZipFile(memoria) as z:
        partes = {n: z.read(n) for n in z.namelist()}
    # openpyxl actualiza modified al guardar; fijarlo después de serializar.
    import re
    partes['docProps/core.xml'] = re.sub(
        rb'(<dcterms:modified[^>]*>).*?(</dcterms:modified>)',
        rb'\g<1>2020-01-01T00:00:00Z\2', partes['docProps/core.xml'])
    paquete(destino / "formatos/datos.xlsx", partes)


if __name__ == "__main__":
    generar()
    print("Fixtures ficticios generados en tests/fixtures/.")
