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

const conDocumentos = (documentos, borradores = []) => {
  const app = crearCarga({ documentos, borradores, base: '/expedientes/1/', maximo: 25, extensiones: ['txt'], roles: [['MINUTA', 'Minuta'], ['CLIENTE', 'Recaudos'], ['BORRADOR', 'Borrador']] });
  return app;
};
const completos = (estado) => [{ id: 1, rol: 'MINUTA', estado: 'LISTO' }, { id: 2, rol: 'CLIENTE', estado, nombre: 'ficticio.pdf' }, { id: 3, rol: 'BORRADOR', estado: 'LISTO', nombre: 'borrador-ficticio.docx' }];

test('F73: qué debe hacer sigue el estado del kardex', () => {
  assert.match(conDocumentos([]).queHacer, /Faltan: Minuta, Recaudos, Borrador\./);
  assert.match(conDocumentos(completos('PROCESANDO')).queHacer, /No tiene que hacer nada/);
  assert.match(conDocumentos(completos('LISTO')).queHacer, /Ya puede confrontar/);
  assert.match(conDocumentos(completos('ERROR')).queHacer, /^ficticio\.pdf no se pudo leer/);
});

test('F73: el botón explica por qué no se puede confrontar', () => {
  assert.match(conDocumentos(completos('ERROR')).motivoBoton(3), /documento con error se reemplace/);
  assert.equal(conDocumentos(completos('PENDIENTE')).motivoBoton(3), 'Esperando 1 documento: preparando documentos.');
  assert.equal(conDocumentos(completos('LISTO'), [{ id: 3, mensaje: 'Mensaje del servidor.' }]).motivoBoton(3), 'Mensaje del servidor.');
});

test('F73: etapas y resumen de cada grupo', () => {
  const app = conDocumentos(completos('ERROR'));
  assert.equal(app.detalleEtapa(1), '2 documentos cargados');
  assert.equal(app.detalleEtapa(2), 'borrador-ficticio.docx');
  assert.equal(app.detalleEtapa(3), '2 de 3 preparados · 1 con atención pendiente');
  assert.equal(app.detalleEtapa(4), 'Se habilita cuando todo esté preparado');
  assert.equal(app.resumenGrupo('CLIENTE'), '1 necesita atención');
  assert.equal(app.tonoGrupo('CLIENTE'), 'peligro');
  assert.equal(app.resumenGrupo('MINUTA'), 'Todo preparado');
  assert.equal(conDocumentos([]).resumenGrupo('MINUTA'), 'Obligatorio · sin documentos');
});

const paraReemplazar = (borrar) => {
  const app = conDocumentos(completos('ERROR'));
  app.reemplazar = 2;
  app.adjuntados = [];
  app.borrados = [];
  app.borrar = async (id) => { app.borrados.push(id); return borrar; };
  app.adjuntar = (archivos) => app.adjuntados.push(...archivos);
  return app;
};
const elegidos = (archivos) => ({ target: { files: archivos, value: 'x' } });

test('F73: volver a subir solo elimina si hay un archivo admisible', async () => {
  const bueno = { name: 'copia.txt', size: 2 };
  const app = paraReemplazar(true);
  await app.seleccionar(elegidos([bueno]), 'CLIENTE');
  assert.deepEqual(app.borrados, [2]);
  assert.deepEqual(app.adjuntados, [bueno]);
  assert.equal(app.reemplazar, null);

  const malo = { name: 'copia.exe', size: 2 };
  const rechazado = paraReemplazar(true);
  await rechazado.seleccionar(elegidos([malo]), 'CLIENTE');
  assert.deepEqual(rechazado.borrados, []);
  assert.deepEqual(rechazado.adjuntados, [malo], 'el archivo se lista con su error');

  const vacio = paraReemplazar(true);
  await vacio.seleccionar(elegidos([]), 'CLIENTE');
  assert.deepEqual(vacio.borrados, []);
});

test('F73: si no se pudo eliminar, no se sube el reemplazo', async () => {
  const app = paraReemplazar(false);
  await app.seleccionar(elegidos([{ name: 'copia.txt', size: 2 }]), 'CLIENTE');
  assert.deepEqual(app.borrados, [2]);
  assert.deepEqual(app.adjuntados, []);
});

test('F73: la nota de cada archivo dice su estado', () => {
  const app = conDocumentos([]);
  assert.equal(app.notaDocumento({ estado: 'PENDIENTE' }), 'En espera de lectura');
  assert.equal(app.notaDocumento({ estado: 'LISTO' }), 'Texto extraído');
  assert.equal(app.notaDocumento({ estado: 'PROCESANDO' }), 'Leyendo el texto');
  assert.match(app.notaDocumento({ estado: 'PROCESANDO', procesando_el: '2026-11-03T12:14:00-05:00' }), /^Leyendo el texto desde las \d{2}:\d{2}$/);
  assert.match(app.notaDocumento({ estado: 'ERROR' }), /copia más clara/);
});
