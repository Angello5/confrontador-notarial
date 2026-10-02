/*
 * F29 · Reporte ejecutivo de observaciones en Word (.docx), generado en el
 * navegador sin dependencias: arma el XML de WordprocessingML y lo empaqueta
 * en un ZIP sin compresión. Solo usa los datos ya renderizados en la página.
 *
 *   const blob = ReporteDocx.generar({ meta, observaciones, correcciones, personas, incluir, logo });
 *
 * meta: { codigo, borrador, corrida, usuario, fecha, notaria }
 * observaciones: [{ capa: IDENTIDAD|REGLA|LINGUISTICO, sev, titulo, campo, hallado, esperado, linea, persona, procedencia, fragmento }]
 * correcciones: [{ erroneo, correcto, fuente, apariciones }]
 * personas: [{ nombre, documento, civil, domicilio, conyuge, procedencia }]
 * incluir: { IDENTIDAD, REGLA, LINGUISTICO, CORRECCIONES, EXTRACCION }
 * logo: { bytes: Uint8Array, tipo: 'png'|'jpeg', ancho, alto } | null
 */
(function (raiz) {
  'use strict';

  // ── Paleta y medidas (twips: 1 cm = 567; medios puntos para tamaños) ──
  const C = {
    navy: '0F2765', ink: '00112C', slate: '4B5D8C', subtle: '8793B2', borde: 'C3C9D9', linea: 'EDEFF8', suave: 'F6F7FC',
    verde: '44D880', verdeTexto: '01835D',
    ALTA: { fg: '8B1C28', bg: 'FDECEE' }, MEDIA: { fg: '5C4200', bg: 'FFF6DB' }, BAJA: { fg: '0F2765', bg: 'EDEFF8' },
  };
  const ANCHO = 9638; // A4 (11906) menos 2 cm por lado
  const FUENTE = 'Calibri';
  const SEV_TEXTO = { ALTA: 'Alta', MEDIA: 'Media', BAJA: 'Baja' };

  // ── Utilidades XML ──
  const esc = (t) => String(t == null ? '' : t)
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

  function run(texto, o = {}) {
    const pr = [];
    if (o.font) pr.push(`<w:rFonts w:ascii="${o.font}" w:hAnsi="${o.font}" w:cs="${o.font}"/>`);
    if (o.b) pr.push('<w:b/><w:bCs/>');
    if (o.i) pr.push('<w:i/>');
    if (o.caps) pr.push('<w:caps/>');
    if (o.strike) pr.push('<w:strike/>');
    if (o.color) pr.push(`<w:color w:val="${o.color}"/>`);
    if (o.spacing) pr.push(`<w:spacing w:val="${o.spacing}"/>`);
    if (o.sz) pr.push(`<w:sz w:val="${o.sz}"/><w:szCs w:val="${o.sz}"/>`);
    if (o.fondo) pr.push(`<w:shd w:val="clear" w:color="auto" w:fill="${o.fondo}"/>`);
    const partes = String(texto == null ? '' : texto).split('\n')
      .map((l) => `<w:t xml:space="preserve">${esc(l)}</w:t>`).join('<w:br/>');
    return `<w:r>${pr.length ? `<w:rPr>${pr.join('')}</w:rPr>` : ''}${partes}</w:r>`;
  }

  function parrafo(runs, o = {}) {
    const pr = [];
    if (o.estilo) pr.push(`<w:pStyle w:val="${o.estilo}"/>`);
    if (o.keepNext) pr.push('<w:keepNext/>');
    if (o.borde) pr.push(`<w:pBdr><w:bottom w:val="single" w:sz="${o.borde.sz || 12}" w:space="${o.borde.espacio || 6}" w:color="${o.borde.color}"/></w:pBdr>`);
    if (o.tabs) pr.push(`<w:tabs>${o.tabs.map((t) => `<w:tab w:val="${t.tipo}" w:pos="${t.pos}"/>`).join('')}</w:tabs>`);
    pr.push(`<w:spacing w:before="${o.antes ?? 0}" w:after="${o.despues ?? 120}"${o.interlineado ? ` w:line="${o.interlineado}" w:lineRule="auto"` : ''}/>`);
    if (o.sangria) pr.push(`<w:ind w:left="${o.sangria}" w:hanging="${o.colgante || 0}"/>`);
    if (o.alin) pr.push(`<w:jc w:val="${o.alin}"/>`);
    return `<w:p><w:pPr>${pr.join('')}</w:pPr>${Array.isArray(runs) ? runs.join('') : runs || ''}</w:p>`;
  }

  // Celda: contenido = párrafos ya armados (o texto simple).
  function celda(contenido, o = {}) {
    const pr = [`<w:tcW w:w="${o.ancho}" w:type="dxa"/>`];
    if (o.fondo) pr.push(`<w:shd w:val="clear" w:color="auto" w:fill="${o.fondo}"/>`);
    if (o.span) pr.push(`<w:gridSpan w:val="${o.span}"/>`);
    pr.push(`<w:vAlign w:val="${o.valign || 'top'}"/>`);
    if (o.margen) pr.push(`<w:tcMar><w:top w:w="${o.margen}" w:type="dxa"/><w:bottom w:w="${o.margen}" w:type="dxa"/></w:tcMar>`);
    const cuerpo = typeof contenido === 'string' ? parrafo(run(contenido, o.run || {}), { despues: 0 }) : contenido.join('');
    return `<w:tc><w:tcPr>${pr.join('')}</w:tcPr>${cuerpo || parrafo('', { despues: 0 })}</w:tc>`;
  }

  function tabla(anchos, filas, o = {}) {
    const bordes = o.sinBordes
      ? `<w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/><w:insideH w:val="nil"/>${o.lineasV ? `<w:insideV w:val="single" w:sz="${o.lineasV}" w:color="FFFFFF"/>` : '<w:insideV w:val="nil"/>'}</w:tblBorders>`
      : `<w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="single" w:sz="6" w:color="${C.borde}"/><w:right w:val="nil"/><w:insideH w:val="single" w:sz="4" w:color="${C.borde}"/><w:insideV w:val="nil"/></w:tblBorders>`;
    const pr = `<w:tblPr><w:tblW w:w="${ANCHO}" w:type="dxa"/><w:tblLayout w:type="fixed"/>${bordes}<w:tblCellMar><w:top w:w="${o.margenV ?? 70}" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:bottom w:w="${o.margenV ?? 70}" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>`;
    const grid = `<w:tblGrid>${anchos.map((a) => `<w:gridCol w:w="${a}"/>`).join('')}</w:tblGrid>`;
    const filasXml = filas.map((f) => `<w:tr><w:trPr><w:cantSplit/>${f.encabezado ? '<w:tblHeader/>' : ''}</w:trPr>${f.celdas.join('')}</w:tr>`).join('');
    // Párrafo de aire tras la tabla: Word pega el título siguiente si no lo hay.
    return `<w:tbl>${pr}${grid}${filasXml}</w:tbl>${parrafo(run('', { sz: 8 }), { despues: o.aire ?? 160 })}`;
  }

  // Tabla de datos con encabezado navy repetido en cada página y bandas suaves.
  function tablaDatos(columnas, filas) {
    const anchos = columnas.map((c) => c.ancho);
    const encabezado = {
      encabezado: true,
      celdas: columnas.map((c) => celda([parrafo(run(c.titulo, { b: true, color: 'FFFFFF', sz: 16, caps: true, spacing: 10 }), { despues: 0 })], { ancho: c.ancho, fondo: C.navy, valign: 'center' })),
    };
    const cuerpo = filas.map((f, i) => ({
      celdas: f.map((contenido, j) => celda(contenido, { ancho: anchos[j], fondo: i % 2 ? C.suave : undefined })),
    }));
    return tabla(anchos, [encabezado, ...cuerpo]);
  }

  const texto = (t, o = {}) => [parrafo(run(t || '—', { sz: 18, ...o }), { despues: 0 })];

  function chipSeveridad(sev) {
    const c = C[sev] || C.BAJA;
    return [parrafo(run(` ${SEV_TEXTO[sev] || sev} `, { b: true, sz: 16, color: c.fg, fondo: c.bg, caps: true }), { despues: 0 })];
  }

  // Fragmento del borrador con el valor hallado resaltado.
  function ubicacion(o) {
    const lineas = [];
    if (o.linea) lineas.push(run(`Línea ${o.linea}`, { b: true, sz: 16, color: C.slate }));
    if (o.fragmento) {
      const frag = o.fragmento;
      const i = o.hallado ? frag.toUpperCase().indexOf(String(o.hallado).toUpperCase()) : -1;
      const sep = lineas.length ? [run('\n', { sz: 16 })] : [];
      if (i >= 0) {
        lineas.push(...sep, run(frag.slice(0, i), { sz: 16, color: C.slate }),
          run(frag.slice(i, i + o.hallado.length), { sz: 16, b: true, color: C.ALTA.fg, fondo: C.ALTA.bg }),
          run(frag.slice(i + o.hallado.length), { sz: 16, color: C.slate }));
      } else {
        lineas.push(...sep, run(frag, { sz: 16, color: C.slate }));
      }
    }
    if (!lineas.length) lineas.push(run('No ubicada en el borrador', { sz: 16, i: true, color: C.subtle }));
    return [parrafo(lineas, { despues: 0 })];
  }

  const titulo2 = (t) => parrafo(run(t), { estilo: 'Heading1', keepNext: true });
  // keepNext: la nota viaja con la primera fila de la tabla que la sigue.
  const nota = (t, conTabla) => parrafo(run(t, { sz: 17, i: true, color: C.slate }), { despues: 160, keepNext: !!conTabla });

  // ── Cuerpo del documento ──
  function documento(d, conLogo) {
    const m = d.meta;
    const obs = d.observaciones || [];
    const por = (capa) => obs.filter((o) => o.capa === capa);
    const cuenta = (sev) => obs.filter((o) => o.sev === sev).length;
    const total = obs.length;
    const partes = [];

    // Portada breve
    partes.push(parrafo(run('Reporte de observaciones', { b: true, sz: 52, color: C.navy }), { despues: 40 }));
    partes.push(parrafo([run(`Expediente ${m.codigo}`, { sz: 26, color: C.slate }), run('  ·  Confrontación del borrador', { sz: 26, color: C.subtle })],
      { despues: 240, borde: { color: C.verde, sz: 18, espacio: 8 } }));

    // Ficha del reporte
    const ficha = [['Notaría', m.notaria], ['Expediente', m.codigo], ['Borrador confrontado', m.borrador],
      ['Corrida', m.corrida ? `N.° ${m.corrida}` : '—'], ['Emitido por', m.usuario], ['Fecha de emisión', m.fecha]];
    partes.push(tabla([2600, ANCHO - 2600], ficha.map(([k, v]) => ({
      celdas: [
        celda([parrafo(run(k, { b: true, sz: 16, caps: true, color: C.slate, spacing: 10 }), { despues: 0 })], { ancho: 2600 }),
        celda([parrafo(run(v || '—', { sz: 20, color: C.ink }), { despues: 0 })], { ancho: ANCHO - 2600 }),
      ],
    })), { sinBordes: true, margenV: 40 }));

    // Resumen ejecutivo
    partes.push(titulo2('Resumen ejecutivo'));
    const alta = cuenta('ALTA'), media = cuenta('MEDIA'), baja = cuenta('BAJA');
    const ncorr = (d.correcciones || []).length;
    const frase = total
      ? `La confrontación del borrador «${m.borrador}» contra la minuta y los documentos del cliente encontró ${total} observaci${total === 1 ? 'ón' : 'ones'}: ${alta} de severidad alta, ${media} media y ${baja} baja.${ncorr ? ` Se proponen ${ncorr} correcci${ncorr === 1 ? 'ón' : 'ones'} automática${ncorr === 1 ? '' : 's'} a partir de las fuentes.` : ''}`
      : `La confrontación del borrador «${m.borrador}» no encontró observaciones en los datos detectados.`;
    partes.push(parrafo(run(frase, { sz: 21 }), { despues: 200, interlineado: 276 }));
    if ((d.calidad || []).length) {
      partes.push(titulo2('Calidad de lectura'));
      partes.push(parrafo(run('Una lectura incompleta puede ocultar discrepancias. Revise las páginas indicadas o cargue una copia más clara.', { sz: 21 }), { despues: 120 }));
      d.calidad.forEach((aviso) => partes.push(parrafo(run(aviso, { sz: 20 }), { despues: 100 })));
    }

    const kpi = [['Severidad alta', alta, C.ALTA], ['Severidad media', media, C.MEDIA], ['Severidad baja', baja, C.BAJA],
      ['Correcciones propuestas', ncorr, { fg: C.verdeTexto, bg: 'E5FAED' }]];
    const anchoKpi = Math.floor(ANCHO / 4);
    partes.push(tabla(kpi.map(() => anchoKpi), [{
      celdas: kpi.map(([etq, n, c]) => celda([
        parrafo(run(String(n), { b: true, sz: 44, color: c.fg }), { despues: 0, alin: 'center' }),
        parrafo(run(etq, { b: true, sz: 15, caps: true, color: c.fg, spacing: 10 }), { despues: 0, alin: 'center' }),
      ], { ancho: anchoKpi, fondo: c.bg, valign: 'center', margen: 160 })),
    }], { sinBordes: true, lineasV: 24 }));

    const prioritarias = obs.filter((o) => o.sev === 'ALTA');
    if (prioritarias.length) {
      partes.push(parrafo(run('Atención prioritaria antes de la firma', { b: true, sz: 22, color: C.navy }), { antes: 280, despues: 100, keepNext: true }));
      prioritarias.slice(0, 8).forEach((o) => {
        partes.push(parrafo([
          run('■  ', { sz: 14, color: C.ALTA.fg }),
          run(`${o.titulo}: `, { b: true, sz: 20 }),
          run(o.hallado || '—', { sz: 20, color: C.ALTA.fg, strike: true }),
          run('  →  ', { sz: 20, color: C.subtle }),
          run(o.esperado || '—', { sz: 20, b: true, color: C.verdeTexto }),
          run(o.linea ? `   (línea ${o.linea})` : '', { sz: 18, color: C.slate }),
        ], { sangria: 360, colgante: 360, despues: 60 }));
      });
      if (prioritarias.length > 8) partes.push(nota(`Y ${prioritarias.length - 8} más en el detalle.`));
    }
    partes.push(parrafo(run(total
      ? 'Recomendación: corrija primero las observaciones de severidad alta (nombres, documentos de identidad, partidas y montos) y vuelva a confrontar el borrador antes de la firma.'
      : 'Recomendación: el borrador puede continuar su trámite.', { sz: 19, color: C.slate }), { antes: 160, despues: 120 }));

    // Detalle por capa
    const sev = (o) => chipSeveridad(o.sev);
    if (d.incluir.IDENTIDAD) {
      partes.push(titulo2('Observaciones de identidad'));
      const filas = por('IDENTIDAD');
      if (filas.length) {
        partes.push(nota('Documentos de identidad del borrador que pertenecen a otra persona o no tienen titular en las fuentes.', true));
        partes.push(tablaDatos(
          [{ titulo: 'Sev.', ancho: 900 }, { titulo: 'Persona', ancho: 2100 }, { titulo: 'Hallado', ancho: 1450 }, { titulo: 'Esperado', ancho: 1450 }, { titulo: 'Procedencia y ubicación', ancho: ANCHO - 5900 }],
          filas.map((o) => [sev(o), texto(o.persona || o.titulo, { b: true }), texto(o.hallado, { color: C.ALTA.fg }), texto(o.esperado, { color: C.verdeTexto, b: true }),
            [parrafo(run(o.procedencia || 'Fuente no ubicada', { sz: 16, color: C.ink }), { despues: 40 }), ...ubicacion(o)]])));
      } else partes.push(nota('Sin observaciones de identidad.'));
    }
    if (d.incluir.REGLA) {
      partes.push(titulo2('Observaciones de regla'));
      const filas = por('REGLA');
      if (filas.length) {
        partes.push(nota('Datos del borrador que no coinciden con las fuentes: nombres, documentos, partidas, montos, estado civil y párrafos de la minuta.', true));
        partes.push(tablaDatos(
          [{ titulo: 'Sev.', ancho: 900 }, { titulo: 'Campo', ancho: 1700 }, { titulo: 'Hallado', ancho: 1650 }, { titulo: 'Esperado', ancho: 1650 }, { titulo: 'Ubicación en el borrador', ancho: ANCHO - 5900 }],
          filas.map((o) => [sev(o),
            [parrafo(run(o.titulo, { b: true, sz: 18 }), { despues: 0 }), ...(o.procedencia ? [parrafo(run(o.procedencia, { sz: 15, color: C.slate }), { despues: 0 })] : [])],
            texto(o.hallado, { color: C.ALTA.fg }), texto(o.esperado, { color: C.verdeTexto, b: true }), ubicacion(o)])));
      } else partes.push(nota('Sin observaciones de regla.'));
    }
    if (d.incluir.LINGUISTICO) {
      partes.push(titulo2('Observaciones lingüísticas'));
      const filas = por('LINGUISTICO');
      if (filas.length) {
        partes.push(nota('Solo informan: no corrigen el documento ni deciden sobre nombres, documentos, montos ni domicilios.', true));
        partes.push(tablaDatos(
          [{ titulo: 'Texto', ancho: 2100 }, { titulo: 'Motivo', ancho: 1900 }, { titulo: 'Sugerencia', ancho: 1900 }, { titulo: 'Ubicación en el borrador', ancho: ANCHO - 5900 }],
          filas.map((o) => [texto(o.hallado, { b: true }), texto(o.campo, { color: C.slate }), texto(o.esperado || 'Sin sugerencia', { color: C.verdeTexto, b: !!o.esperado }), ubicacion(o)])));
      } else partes.push(nota('Sin observaciones lingüísticas.'));
    }
    if (d.incluir.CORRECCIONES) {
      partes.push(titulo2('Correcciones propuestas'));
      const filas = d.correcciones || [];
      if (filas.length) {
        partes.push(nota('Reemplazos que el sistema puede aplicar en un documento corregido nuevo; el borrador original no cambia.', true));
        partes.push(tablaDatos(
          [{ titulo: 'Valor erróneo', ancho: 2500 }, { titulo: 'Valor correcto', ancho: 2500 }, { titulo: 'Documento fuente', ancho: 3238 }, { titulo: 'Apariciones', ancho: 1400 }],
          filas.map((c) => [texto(c.erroneo, { color: C.ALTA.fg }), texto(c.correcto, { color: C.verdeTexto, b: true }), texto(c.fuente, { color: C.slate }), texto(c.apariciones)])));
      } else partes.push(nota('No hay correcciones propuestas.'));
    }
    if (d.incluir.EXTRACCION) {
      partes.push(titulo2('Personas extraídas y procedencia'));
      const filas = d.personas || [];
      if (filas.length) {
        partes.push(tablaDatos(
          [{ titulo: 'Nombre', ancho: 2300 }, { titulo: 'Documento', ancho: 1300 }, { titulo: 'Estado civil', ancho: 1300 }, { titulo: 'Domicilio', ancho: 2500 }, { titulo: 'Procedencia', ancho: ANCHO - 7400 }],
          filas.map((p) => [texto(p.nombre, { b: true }), texto(p.documento), texto(p.civil), texto(p.domicilio), texto(p.procedencia, { color: C.slate, sz: 16 })])));
      } else partes.push(nota('Ninguna ficha RENIEC o biométrica en el legajo.'));
    }

    partes.push(parrafo(run('Reporte generado por el confrontador notarial a partir de la minuta, los documentos del cliente y el borrador cargados en el expediente. Las decisiones de corrección corresponden al personal de la notaría.',
      { sz: 15, i: true, color: C.subtle }), { antes: 360, despues: 0, borde: { color: C.linea, sz: 6, espacio: 1 } }));

    const sect = `<w:sectPr><w:headerReference w:type="default" r:id="rIdHeader"/><w:footerReference w:type="default" r:id="rIdFooter"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1531" w:right="1134" w:bottom="1247" w:left="1134" w:header="567" w:footer="567" w:gutter="0"/></w:sectPr>`;
    return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><w:body>${partes.join('')}${sect}</w:body></w:document>`;
  }

  function encabezado(d, logo) {
    let marca;
    if (logo) {
      const alto = 300000; // ≈ 0,83 cm en EMU
      const ancho = Math.round(alto * logo.ancho / logo.alto);
      marca = `<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="${ancho}" cy="${alto}"/><wp:docPr id="1" name="Logo"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="logo.${logo.tipo}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rIdLogo"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="${ancho}" cy="${alto}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>`;
    } else {
      marca = run(d.meta.notaria || '', { b: true, sz: 22, color: C.navy });
    }
    const p = parrafo([marca, run('\t'), run(`Reporte de observaciones · ${d.meta.codigo}`, { sz: 16, color: C.slate })],
      { despues: 0, tabs: [{ tipo: 'right', pos: ANCHO }], borde: { color: C.navy, sz: 6, espacio: 6 } });
    return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">${p}</w:hdr>`;
  }

  function pie(d) {
    const campo = (instr) => `<w:fldSimple w:instr=" ${instr} "><w:r><w:rPr><w:b/><w:sz w:val="16"/><w:color w:val="${C.navy}"/></w:rPr><w:t>1</w:t></w:r></w:fldSimple>`;
    const p = parrafo([run(`${d.meta.notaria || ''} · Documento interno y confidencial`, { sz: 16, color: C.subtle }), run('\t'),
      run('Página ', { sz: 16, color: C.subtle }), campo('PAGE'), run(' de ', { sz: 16, color: C.subtle }), campo('NUMPAGES')],
    { despues: 0, tabs: [{ tipo: 'right', pos: ANCHO }] });
    return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">${p}</w:ftr>`;
  }

  const ESTILOS = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="${FUENTE}" w:hAnsi="${FUENTE}" w:eastAsia="${FUENTE}" w:cs="${FUENTE}"/><w:color w:val="${C.ink}"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="es-PE"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="420" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:bCs/><w:color w:val="${C.navy}"/><w:sz w:val="30"/><w:szCs w:val="30"/></w:rPr></w:style>
<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/><w:tblPr><w:tblInd w:w="0" w:type="dxa"/><w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>
</w:styles>`;

  const AJUSTES = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:defaultTabStop w:val="708"/><w:characterSpacingControl w:val="doNotCompress"/><w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat></w:settings>`;

  // ── ZIP sin compresión (método 0) ──
  const TABLA_CRC = (() => {
    const t = new Uint32Array(256);
    for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; }
    return t;
  })();
  function crc32(bytes) {
    let c = 0xFFFFFFFF;
    for (let i = 0; i < bytes.length; i++) c = TABLA_CRC[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
    return (c ^ 0xFFFFFFFF) >>> 0;
  }
  function zip(archivos) {
    const enc = new TextEncoder();
    const locales = [], centrales = [];
    let desplazamiento = 0;
    const ahora = new Date();
    const hora = (ahora.getHours() << 11) | (ahora.getMinutes() << 5) | (ahora.getSeconds() >> 1);
    const dia = ((ahora.getFullYear() - 1980) << 9) | ((ahora.getMonth() + 1) << 5) | ahora.getDate();
    for (const [nombre, contenido] of archivos) {
      const datos = typeof contenido === 'string' ? enc.encode(contenido) : contenido;
      const n = enc.encode(nombre), crc = crc32(datos);
      const loc = new DataView(new ArrayBuffer(30));
      loc.setUint32(0, 0x04034b50, true); loc.setUint16(4, 20, true); loc.setUint16(6, 0x0800, true); loc.setUint16(8, 0, true);
      loc.setUint16(10, hora, true); loc.setUint16(12, dia, true); loc.setUint32(14, crc, true);
      loc.setUint32(18, datos.length, true); loc.setUint32(22, datos.length, true); loc.setUint16(26, n.length, true); loc.setUint16(28, 0, true);
      locales.push(new Uint8Array(loc.buffer), n, datos);
      const cen = new DataView(new ArrayBuffer(46));
      cen.setUint32(0, 0x02014b50, true); cen.setUint16(4, 20, true); cen.setUint16(6, 20, true); cen.setUint16(8, 0x0800, true); cen.setUint16(10, 0, true);
      cen.setUint16(12, hora, true); cen.setUint16(14, dia, true); cen.setUint32(16, crc, true);
      cen.setUint32(20, datos.length, true); cen.setUint32(24, datos.length, true); cen.setUint16(28, n.length, true);
      cen.setUint32(42, desplazamiento, true);
      centrales.push(new Uint8Array(cen.buffer), n);
      desplazamiento += 30 + n.length + datos.length;
    }
    const tamCentral = centrales.reduce((s, b) => s + b.length, 0);
    const fin = new DataView(new ArrayBuffer(22));
    fin.setUint32(0, 0x06054b50, true); fin.setUint16(8, archivos.length, true); fin.setUint16(10, archivos.length, true);
    fin.setUint32(12, tamCentral, true); fin.setUint32(16, desplazamiento, true);
    const partes = [...locales, ...centrales, new Uint8Array(fin.buffer)];
    const total = partes.reduce((s, b) => s + b.length, 0);
    const salida = new Uint8Array(total);
    let o = 0;
    for (const p of partes) { salida.set(p, o); o += p.length; }
    return salida;
  }

  function generar(d) {
    const logo = d.logo && d.logo.bytes && d.logo.ancho ? d.logo : null;
    const tipoImg = logo ? (logo.tipo === 'jpeg' ? 'jpeg' : 'png') : null;
    const rels = (extra) => `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">${extra}</Relationships>`;
    const archivos = [
      ['[Content_Types].xml', `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>${logo ? `<Default Extension="${tipoImg === 'jpeg' ? 'jpeg' : 'png'}" ContentType="image/${tipoImg}"/>` : ''}<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/><Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/><Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>`],
      ['_rels/.rels', rels('<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>')],
      ['docProps/core.xml', `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>${esc(`Reporte de observaciones · ${d.meta.codigo}`)}</dc:title><dc:creator>${esc(d.meta.usuario)}</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">${new Date().toISOString().slice(0, 19)}Z</dcterms:created></cp:coreProperties>`],
      ['word/document.xml', documento(d, !!logo)],
      ['word/styles.xml', ESTILOS],
      ['word/settings.xml', AJUSTES],
      ['word/header1.xml', encabezado(d, logo)],
      ['word/footer1.xml', pie(d)],
      ['word/_rels/document.xml.rels', rels('<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rIdSettings" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/><Relationship Id="rIdHeader" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/><Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>')],
      ['word/_rels/header1.xml.rels', rels(logo ? `<Relationship Id="rIdLogo" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/logo.${tipoImg}"/>` : '')],
    ];
    if (logo) archivos.push([`word/media/logo.${tipoImg}`, logo.bytes]);
    const bytes = zip(archivos);
    return typeof Blob !== 'undefined'
      ? new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      : bytes;
  }

  // Lee el logo (PNG o JPEG) y sus dimensiones; si falla, el reporte usa el nombre.
  async function cargarLogo(url) {
    if (!url) return null;
    try {
      const resp = await fetch(url);
      if (!resp.ok) return null;
      const bytes = new Uint8Array(await resp.arrayBuffer());
      const esPng = bytes[0] === 0x89 && bytes[1] === 0x50;
      const esJpeg = bytes[0] === 0xFF && bytes[1] === 0xD8;
      if (!esPng && !esJpeg) return null;
      const img = await createImageBitmap(new Blob([bytes]));
      return { bytes, tipo: esPng ? 'png' : 'jpeg', ancho: img.width, alto: img.height };
    } catch (e) {
      return null;
    }
  }

  const api = { generar, cargarLogo };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else raiz.ReporteDocx = api;
})(typeof window !== 'undefined' ? window : globalThis);
