const { test } = require('node:test');
const assert = require('node:assert/strict');
const { crearCarga } = require('../static/js/carga-expediente.js');

const crear = () => crearCarga({ documentos: [], borradores: [], base: '/expedientes/1/', maximo: 25, extensiones: ['txt'] });

test('CSRF se obtiene de la raíz aunque el evento venga del selector de archivos', () => {
  const app = crear();
  app.$el = { querySelector: () => null };
  app.$root = { querySelector: () => ({ value: 'csrf-ficticio' }) };
  assert.equal(app.csrf(), 'csrf-ficticio');
});

test('sesión vencida no confirma ni oculta una eliminación', async () => {
  const app = crear();
  app.documentos = [{ id: 1 }];
  app.csrf = () => 'ficticio';
  globalThis.confirm = () => true;
  const anterior = globalThis.fetch;
  globalThis.fetch = async () => ({ ok: true, json: async () => { throw new Error('HTML'); } });
  app.actualizar = async () => {};
  try {
    await app.quitar(1);
    assert.equal(app.documentos.length, 1);
    assert.match(app.mensaje, /No se pudo eliminar/);
  } finally { globalThis.fetch = anterior; delete globalThis.confirm; }
});

test('selecciones sucesivas conservan archivos de todos los roles', () => {
  const app = crear();
  app.procesarCola = () => {};
  app.adjuntar([{ name: 'minuta.txt', size: 2 }], 'MINUTA');
  app.adjuntar([{ name: 'borrador.txt', size: 2 }], 'BORRADOR');
  assert.equal(app.transferencias.length, 2);
  assert.equal(app.transferencias[1].rol, 'BORRADOR');
});

test('validación individual no impide adjuntar los válidos', () => {
  const app = crear();
  app.procesarCola = () => {};
  app.adjuntar([{ name: 'grande.txt', size: 30 }, { name: 'ok.txt', size: 2 }], 'MINUTA');
  assert.equal(app.transferencias[0].estado, 'ERROR');
  assert.equal(app.transferencias[1].estado, 'PENDIENTE');
});

test('confrontar espera las transferencias sin publicar aún', async () => {
  const app = crear();
  app.procesarCola = () => {};
  app.adjuntar([{ name: 'minuta.txt', size: 2 }], 'MINUTA');
  app.enviarSolicitud = () => assert.fail('No confrontar durante transferencia');
  await app.confrontar(7);
  assert.equal(app.intencion, 7);
});

test('error de transferencia impide confrontación incompleta', async () => {
  const app = crear();
  app.transferencias = [{ estado: 'ERROR' }];
  app.enviarSolicitud = () => assert.fail('No ignorar errores');
  await app.confrontar(7);
  assert.match(app.mensaje, /carga/i);
});

test('mezclar estados conserva nombres ya recibidos y refleja eliminaciones', () => {
  const app = crear();
  app.documentos = [{id: 1, nombre: 'ficticio.txt', estado: 'PENDIENTE'}, {id: 2}];
  app.recibirEstado({documentos: [{id: 1, estado: 'LISTO'}], borradores: []});
  assert.deepEqual(app.documentos, [{id: 1, nombre: 'ficticio.txt', estado: 'LISTO'}]);
});

test('un resultado solicitado abre la revisión, pero una carga pendiente lo pospone', () => {
  const app = crear();
  app.resultadoEsperado = 7;
  const anterior = globalThis.location;
  const visitas = [];
  globalThis.location = { assign: url => visitas.push(url) };
  app.transferencias = [{ estado: 'SUBIENDO' }];
  try {
    app.recibirEstado({ documentos: [], borradores: [{ id: 7, resultado_listo: true }] });
    assert.equal(visitas.length, 0);
    app.transferencias = [];
    app.recibirEstado({ documentos: [], borradores: [{ id: 7, resultado_listo: true }] });
    assert.deepEqual(visitas, ['/expedientes/1/documentos/7/resultado/']);
  } finally { globalThis.location = anterior; }
});

test('resumen, estado y paso del riel se derivan de los documentos', () => {
  const app = crear();
  assert.equal(app.estado, 'VACIO');
  assert.equal(app.pasoActual, 1);
  app.documentos = [{ id: 1, rol: 'CLIENTE', estado: 'LISTO' }, { id: 2, rol: 'MINUTA', estado: 'LISTO' }];
  assert.equal(app.pasoActual, 2);
  app.documentos.push({ id: 3, rol: 'BORRADOR', estado: 'PROCESANDO' });
  assert.equal(app.estado, 'PROCESANDO');
  assert.equal(app.pasoActual, 3);
  assert.deepEqual(app.resumen, { total: 3, pendientes: 0, procesando: 1, listos: 2, errores: 0 });
  app.documentos[2].estado = 'LISTO';
  assert.equal(app.estado, 'LISTO');
  assert.equal(app.pasoActual, 4);
  app.documentos[0].estado = 'ERROR';
  assert.equal(app.estado, 'ERROR');
});

test('faltantes y confrontación en curso usan los roles y la solicitud', () => {
  const app = crearCarga({ documentos: [], borradores: [], base: '/expedientes/1/', maximo: 25, extensiones: ['txt'], roles: [['CLIENTE', 'Documentos del cliente'], ['MINUTA', 'Minuta'], ['BORRADOR', 'Proyecto (borrador)']] });
  assert.equal(app.faltan, 'Faltan: Documentos del cliente, Minuta, Proyecto (borrador).');
  app.documentos = [{ id: 1, rol: 'CLIENTE', estado: 'LISTO' }, { id: 2, rol: 'MINUTA', estado: 'LISTO' }];
  assert.equal(app.faltan, 'Falta: Proyecto (borrador).');
  app.confrontaciones = [{ id: 3, solicitada: true }];
  assert.equal(app.enCurso(3), true);
  app.confrontaciones = [{ id: 3, solicitada: false, etapa: 'LISTO' }];
  assert.equal(app.enCurso(3), false);
  app.intencion = 3;
  assert.equal(app.enCurso(3), true);
});
