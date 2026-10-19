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
