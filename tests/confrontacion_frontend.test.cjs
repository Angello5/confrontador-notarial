const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

test('Word includes reading warnings without asserting agreement', async () => {
  const report = require('../static/js/reporte-docx.js');
  const blob = report.generar({meta: {codigo:'FICTICIO',borrador:'ficticio.docx'},
    observaciones:[],correcciones:[],personas:[],incluir:{},
    calidad:['cliente-ficticio.pdf: Lectura dudosa en página 2.']});
  const contents = Buffer.from(await blob.arrayBuffer()).toString('utf8');
  assert.match(contents, /Calidad de lectura/);
  assert.match(contents, /Lectura dudosa en página 2/);
  assert.doesNotMatch(contents, /el borrador concuerda con las fuentes/);
});

test('F43: the vehicle-transfer report does not mention a minuta', async () => {
  const report = require('../static/js/reporte-docx.js');
  const observacion = { capa: 'REGLA', sev: 'ALTA', titulo: 'Placa', campo: 'Placa', hallado: 'QWE128', esperado: 'QWE123' };
  const blob = report.generar({meta: {codigo:'VEH-FICTICIO',borrador:'acta.docx',vehicular:true},
    observaciones:[observacion],correcciones:[],personas:[],incluir:{REGLA:true},calidad:[]});
  const contents = Buffer.from(await blob.arrayBuffer()).toString('utf8');
  assert.match(contents, /contra la información de la transferencia/);
  assert.doesNotMatch(contents, /minuta/);
});

test('F55: the vehicle-transfer report says «Transferencia vehicular» / «TV», never kardex', async () => {
  const report = require('../static/js/reporte-docx.js');
  const datos = (vehicular) => ({meta: {codigo:'NUM-FICTICIO',borrador:'ficticio.docx',vehicular},
    observaciones:[],correcciones:[],personas:[],incluir:{},calidad:[]});
  const texto = async (d) => Buffer.from(await report.generar(d).arrayBuffer()).toString('utf8');
  const tv = await texto(datos(true));
  assert.match(tv, /Transferencia vehicular NUM-FICTICIO/);
  assert.match(tv, />TV</);
  assert.match(tv, /cargados en la TV\./);
  assert.doesNotMatch(tv, /kardex/i);
  const notarial = await texto(datos(false));
  assert.match(notarial, /Kardex NUM-FICTICIO/);
  assert.match(notarial, /cargados en el kardex\./);
  assert.doesNotMatch(notarial, /\bTV\b|Transferencia vehicular/);
});

// Execute the actual template controller with a minimal DOM; all data is fictional.
function revision(observations, corrections) {
  const html = fs.readFileSync(path.join(__dirname, '../templates/expedientes/confrontacion.html'), 'utf8');
  const script = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
  const context = vm.createContext({ window: { addEventListener() {} }, document: { querySelectorAll: () => [] }, Blob });
  // F40: el mixin de «Aplicar correcciones» vive en su propio archivo.
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../static/js/aplicar-correcciones.js'), 'utf8'), context);
  vm.runInContext(script, context);
  const state = context.window.revisionConfrontacion();
  const nodes = observations.map(dataset => ({ dataset }));
  state.$refs = { lista: { querySelectorAll: () => nodes, appendChild() {} } };
  state.$el = { querySelectorAll: selector => selector === '[data-correccion]' ? corrections.map(dataset => ({ dataset })) : [] };
  state.$watch = () => {};
  state.iniciar();
  return state;
}

test('a longer identity number cannot select a correction for a substring', () => {
  const state = revision([{ id: 'r1', hallado: '190000002', esperado: '90000001' }], [
    { correccion: 'a', erroneo: '90000002', correcto: '90000001' },
  ]);
  assert.equal(state.corrDe('r1'), null);
});

test('the expected value disambiguates corrections with the same erroneous value', () => {
  const state = revision([{ id: 'r1', hallado: '90000002', esperado: '90000003' }], [
    { correccion: 'a', erroneo: '90000002', correcto: '90000001' },
    { correccion: 'b', erroneo: '90000002', correcto: '90000003' },
  ]);
  assert.equal(state.corrDe('r1').id, 'b');
});

test('exact pairs support whitespace and capitalization normalization', () => {
  const state = revision([{ id: 'r1', hallado: 'ALBA  LUNARIA', esperado: 'ALBA LUMARIA' }], [
    { correccion: 'a', erroneo: 'Alba Lunaria', correcto: 'Alba Lumaria' },
  ]);
  assert.equal(state.corrDe('r1').id, 'a');
  state.alternar('a');
  assert.equal(state.estaMarcadaObs('r1'), false);
});

test('F48: the apply box lists every observation and blocks those without a correction', () => {
  const state = revision([
    { id: 'r1', hallado: '90000002', esperado: '90000001' },
    { id: 'r2', hallado: '90000002', esperado: '90000001' },
    { id: 'p1', hallado: '90000002', esperado: 'Sin documento conocido' },
    { id: 'o1', hallado: 'clausla', esperado: 'cláusula' },
  ], [{ correccion: 'a', erroneo: '90000002', correcto: '90000001' }]);
  const filas = state.filasCorreccion();
  assert.equal(filas.length, state.obs.length);
  assert.equal(filas.filter((f) => !f.corr).map((f) => f.id).join(), 'p1,o1');
  assert.equal(state.contarMarcadas(), 2);
  assert.equal(state.contarBloqueadas(), 2);
  // One proposal fixes both repeated observations: unmarking it unmarks both rows.
  state.alternar('a');
  assert.equal(state.contarMarcadas(), 0);
});

test('F48: a proposal without a matching observation stays in the apply box', () => {
  const state = revision([{ id: 'p1', hallado: '90000003', esperado: 'Sin documento conocido' }], [
    { correccion: 'a', erroneo: 'ALBA LUNARIA', correcto: 'ALBA LUMARIA' },
  ]);
  const filas = state.filasCorreccion();
  assert.equal(filas.length, 2);
  assert.equal(filas[1].corr.id, 'a');
  assert.equal(state.contarMarcadas(), 1);
  assert.equal(state.contarBloqueadas(), 1);
});

test('F56: a single «Todas» list filtered only by severity', () => {
  const state = revision([
    { id: 'p1', capa: 'IDENTIDAD', sev: 'ALTA', linea: '1' },
    { id: 'r1', capa: 'REGLA', sev: 'MEDIA', linea: '2' },
    { id: 'o1', capa: 'LINGUISTICO', sev: 'BAJA', linea: '3' },
  ], []);
  assert.equal(state.capa, undefined);
  assert.equal(state.contar, undefined);
  assert.equal(state.visibles.length, 3);
  state.sev = 'MEDIA';
  assert.equal(state.visibles.map((o) => o.id).join(), 'r1');
  // The severity counters always count the whole list.
  assert.equal(state.contarSev('ALTA'), 1);
  state.ajustarSeleccion();
  assert.equal(state.sel, 'r1');
  state.sev = 'TODAS';
  state.$nextTick = () => {};
  state.paso(1);
  assert.equal(state.sel, 'o1');
  // The report still counts per layer.
  assert.equal(state.contarCapa('IDENTIDAD'), 1);
});

test('Word download errors leave an actionable message and release the button', async () => {
  const state = revision([], []);
  await state.descargarWord();
  assert.equal(state.generando, false);
  assert.match(state.errorReporte, /No se pudo generar/);
});

// F60: fictional notice that is not a correction (spouse with separate property).
const AVISO = {
  id: 'r1', capa: 'IDENTIDAD', sev: 'MEDIA', titulo: 'Cónyuge con bien propio', campo: 'Cónyuge con bien propio',
  hallado: 'ALBA ZURBELIA LUMARIA: Interviene sin su cónyuge por ser bien propio', esperado: '',
  verificar: 'RENIEC indica CASADO. Confirme que el bien es propio; si no lo es, debe intervenir el cónyuge.',
  aviso: 'ALBA ZURBELIA LUMARIA: casado según RENIEC · confirme bien propio',
};

test('F60: the Word report says what to verify for a notice, never «debe decir»', async () => {
  const report = require('../static/js/reporte-docx.js');
  const letras = { ...AVISO, id: 'r2', capa: 'REGLA', sev: 'ALTA', titulo: 'Número en letras',
    hallado: '2,50 (DOS MIL QUINIENTOS CON 00/100 SOLES)',
    verificar: 'La cifra y las letras no valen lo mismo. Corrija la que no corresponda.',
    aviso: 'Cifra y letras no coinciden: 2,50 (DOS MIL QUINIENTOS CON 00/100 SOLES)' };
  const blob = report.generar({meta: {codigo:'FICTICIO',borrador:'ficticio.docx'},
    observaciones:[AVISO, letras],correcciones:[],personas:[],incluir:{IDENTIDAD:true,REGLA:true},calidad:[]});
  const contents = Buffer.from(await blob.arrayBuffer()).toString('utf8');
  assert.match(contents, /Qué verificar: <\/w:t>.*RENIEC indica CASADO\. Confirme que el bien es propio/);
  assert.match(contents, /La cifra y las letras no valen lo mismo/);
  assert.doesNotMatch(contents, /RENIEC: CASADO/);
  // The high-priority summary shows the notice line, not a struck value → expected value.
  assert.match(contents, /Cifra y letras no coinciden: 2,50/);
  assert.doesNotMatch(contents, /<w:strike\/>/);
});

test('F60: the apply box and the exported table show a notice without strike or «debe decir»', async () => {
  const state = revision([AVISO, { id: 'r2', capa: 'REGLA', sev: 'ALTA', hallado: '80000002', esperado: '80000001' }], []);
  const filas = state.filasCorreccion();
  assert.equal(filas[0].aviso, AVISO.aviso);
  assert.equal(filas[0].corr, null);
  let csv = null;
  state.bajar = (blob) => { csv = blob; };
  state.rep.fmt = 'CSV';
  state.descargar();
  const texto = await csv.text();
  assert.match(texto, /"Qué verificar: RENIEC indica CASADO\. Confirme que el bien es propio; si no lo es, debe intervenir el cónyuge\."/);
  assert.match(texto, /"80000002";"80000001"/);
  assert.doesNotMatch(texto, /RENIEC: CASADO/);
});

test('F61: Word includes «Sentido frente a la minuta» only when selected', async () => {
  const report = require('../static/js/reporte-docx.js');
  const sentido = [{ nivel: 'Observación', tipo: 'Contradice la minuta', minuta: 'EL VENDEDOR SE OBLIGA', proyecto: 'EL VENDEDOR NO SE OBLIGA' }];
  const datos = (incluir) => ({meta: {codigo:'FICTICIO',borrador:'ficticio.docx'},
    observaciones:[],correcciones:[],personas:[],sentido,incluir,calidad:[]});
  const texto = async (d) => Buffer.from(await report.generar(d).arrayBuffer()).toString('utf8');
  const con = await texto(datos({SENTIDO:true}));
  assert.match(con, /Sentido frente a la minuta/);
  assert.match(con, /EL VENDEDOR NO SE OBLIGA/);
  assert.doesNotMatch(await texto(datos({})), /Sentido frente a la minuta/);
});
