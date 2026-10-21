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

// Execute the actual template controller with a minimal DOM; all data is fictional.
function revision(observations, corrections) {
  const html = fs.readFileSync(path.join(__dirname, '../templates/expedientes/confrontacion.html'), 'utf8');
  const script = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
  const context = vm.createContext({ window: { addEventListener() {} }, document: { querySelectorAll: () => [] } });
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
  assert.deepEqual(state.visibles.map((o) => o.id), ['r1']);
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
