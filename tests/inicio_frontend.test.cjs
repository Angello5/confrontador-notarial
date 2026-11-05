const test = require('node:test');
const assert = require('node:assert/strict');
const inicio = require('../static/js/inicio-admin.js');

test('interpolar parte del origen, no se pasa del destino y termina exacto', () => {
  assert.equal(inicio.interpolar(10, 30, 0), 10);
  assert.equal(inicio.interpolar(10, 30, 1), 30);
  const medio = inicio.interpolar(10, 30, 0.5);
  assert.ok(medio > 20 && medio < 30, 'la curva frena al final');
  assert.equal(inicio.interpolar(30, 10, 1), 10);
  assert.equal(inicio.interpolar(0, 5, 2), 5, 'fuera de rango se queda en el destino');
});

test('el periodo solo admite semana o mes', () => {
  assert.equal(inicio.periodoValido('mes'), 'mes');
  assert.equal(inicio.periodoValido('semana'), 'semana');
  assert.equal(inicio.periodoValido('año'), 'semana');
  assert.equal(inicio.periodoValido(null), 'semana');
});

test('el periodo guardado sobrevive a un almacenamiento que falla', () => {
  const roto = { getItem() { throw new Error('bloqueado'); } };
  assert.equal(inicio.periodoGuardado(roto), 'semana');
  assert.equal(inicio.periodoGuardado({ getItem: () => 'mes' }), 'mes');
  assert.equal(inicio.periodoGuardado(undefined), 'semana');
});

test('F73: los parámetros solo llevan filtros completos', () => {
  assert.equal(inicio.parametros({ periodo: 'semana' }), 'periodo=semana');
  assert.equal(inicio.parametros({ periodo: 'mes', filtro: 'hoy', persona: '7' }), 'periodo=mes&filtro=hoy&usuario=7');
  assert.equal(inicio.parametros({ periodo: 'semana', filtro: 'rango', desde: '2026-10-01', hasta: '2026-10-02' }), 'periodo=semana&filtro=rango&desde=2026-10-01&hasta=2026-10-02');
  assert.equal(inicio.parametros({ periodo: 'semana', filtro: 'rango', desde: '2026-10-02', hasta: '2026-10-01' }), 'periodo=semana');
  assert.equal(inicio.parametros({ periodo: 'semana', filtro: 'rango', desde: '', hasta: '2026-10-01' }), 'periodo=semana');
});

test('F73: fechas del rango', () => {
  assert.equal(inicio.restarDias('2026-11-03', 14), '2026-10-20');
  assert.equal(inicio.fechaCorta('2026-11-03'), '03/11/2026');
  assert.equal(inicio.fechaCorta(''), '');
});

function panel(datos = {}) {
  const app = inicio.inicioAdmin({ actividad: [], hoy: '2026-11-03', filtro: null, persona: '', desde: '', hasta: '', ...datos });
  app.actualizar = () => { app.pedidos = (app.pedidos || 0) + 1; };
  return app;
}

test('F73: pulsar de nuevo un periodo lo quita y un rango propone dos semanas', () => {
  const app = panel();
  app.elegirFiltro('hoy');
  assert.equal(app.filtro, 'hoy');
  app.elegirFiltro('hoy');
  assert.equal(app.filtro, null);
  app.elegirFiltro('rango');
  assert.deepEqual([app.desde, app.hasta], ['2026-10-20', '2026-11-03']);
  assert.equal(app.rangoIncompleto, false);
  app.desde = '2026-12-01';
  assert.equal(app.rangoIncompleto, true);
  app.persona = '7';
  app.limpiar();
  assert.deepEqual([app.filtro, app.persona], [null, '']);
  assert.equal(app.pedidos, 4);
});

test('F73: «Mostrando» dice lo que el servidor aplicó', () => {
  assert.equal(panel({ filtro: 'semana' }).textoFiltro, 'Esta semana');
  assert.equal(panel({ filtro: 'rango', desde: '2026-10-20', hasta: '2026-11-03' }).textoFiltro, '20/10/2026 – 03/11/2026');
  assert.equal(panel().hayFiltros, false);
  assert.equal(panel({ persona: 'Ficticia' }).hayFiltros, true);
});
