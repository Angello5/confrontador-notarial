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

// Execute the actual template controller with a minimal DOM; all data is fictional.
function revision(observations, corrections) {
  const html = fs.readFileSync(path.join(__dirname, '../templates/expedientes/confrontacion.html'), 'utf8');
  const script = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
  const context = { window: { addEventListener() {} }, document: { querySelectorAll: () => [] } };
  vm.runInNewContext(script, context);
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

test('Word download errors leave an actionable message and release the button', async () => {
  const state = revision([], []);
  await state.descargarWord();
  assert.equal(state.generando, false);
  assert.match(state.errorReporte, /No se pudo generar/);
});
