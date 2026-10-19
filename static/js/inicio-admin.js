/*
 * F53: Inicio del administrador. Pinta los datos de /inicio/datos/, los
 * vuelve a pedir cada minuto (solo con la pestaña visible) y anima los
 * cambios: las barras crecen desde su valor anterior y las cifras avanzan
 * hasta el nuevo. Con «reducir movimiento» los valores cambian sin animación.
 *
 *   x-data="inicioAdmin(JSON.parse(document.getElementById('datos-inicio').textContent))"
 */
(function (raiz) {
  'use strict';

  const PERIODOS = ['semana', 'mes'];
  const CLAVE = 'confrontador.inicio.periodo';
  const INTERVALO = 60000;
  const DURACION = 600;

  function periodoValido(periodo) {
    return PERIODOS.includes(periodo) ? periodo : 'semana';
  }

  function periodoGuardado(almacen) {
    try {
      return periodoValido(almacen && almacen.getItem(CLAVE));
    } catch (error) {
      return 'semana';
    }
  }

  // Curva de salida: arranca rápido y frena al llegar, sin pasarse.
  function interpolar(desde, hasta, t) {
    if (t >= 1) return hasta;
    const x = Math.max(t, 0);
    return desde + (hasta - desde) * (1 - Math.pow(1 - x, 3));
  }

  function almacen() {
    try {
      return raiz.localStorage;
    } catch (error) {
      return undefined;
    }
  }

  function inicioAdmin(inicial) {
    return {
      datos: inicial,
      periodo: periodoGuardado(almacen()),
      cifra: {},
      altos: inicial.actividad.map(() => 0),
      error: false,
      cargando: false,
      temporizador: null,

      iniciar() {
        this.animar(inicial);
        if (this.periodo !== inicial.periodo) this.actualizar();
        else this.programar();
        document.addEventListener('visibilitychange', () => {
          clearTimeout(this.temporizador);
          if (!document.hidden) this.actualizar();
        });
      },

      reducido() {
        return !!(raiz.matchMedia && raiz.matchMedia('(prefers-reduced-motion: reduce)').matches);
      },

      programar() {
        clearTimeout(this.temporizador);
        if (!document.hidden) this.temporizador = setTimeout(() => this.actualizar(), INTERVALO);
      },

      elegir(periodo) {
        this.periodo = periodoValido(periodo);
        try {
          almacen()?.setItem(CLAVE, this.periodo);
        } catch (error) {
          // Sin almacenamiento solo se pierde la preferencia.
        }
        this.actualizar();
      },

      async actualizar() {
        clearTimeout(this.temporizador);
        this.cargando = true;
        try {
          const respuesta = await fetch(`/inicio/datos/?periodo=${this.periodo}`, {
            headers: { Accept: 'application/json' },
            credentials: 'same-origin',
          });
          if (!respuesta.ok) throw new Error(String(respuesta.status));
          const datos = await respuesta.json();
          // Al cambiar de periodo cambia el número de barras: crecen desde cero.
          if (datos.actividad.length !== this.altos.length) this.altos = datos.actividad.map(() => 0);
          this.datos = datos;
          this.error = false;
          this.animar(datos);
        } catch (error) {
          this.error = true; // Se conservan los datos ya mostrados.
        } finally {
          this.cargando = false;
          this.programar();
        }
      },

      // Cifras que se muestran con animación, por nombre.
      objetivos(datos) {
        const ind = datos.indicadores;
        return {
          total: datos.cifras.total,
          notariales: datos.cifras.notariales,
          vehiculares: datos.cifras.vehiculares,
          alta: ind.gravedad.ALTA,
          media: ind.gravedad.MEDIA,
          baja: ind.gravedad.BAJA,
          documentos: ind.correcciones.documentos,
          aplicadas: ind.correcciones.aplicadas,
        };
      },

      animar(datos) {
        const destinoCifras = this.objetivos(datos);
        const destinoAltos = datos.actividad.map(tramo => tramo.alto);
        const turno = (this.turno = (this.turno || 0) + 1);
        const terminar = () => {
          if (turno !== this.turno) return;
          this.cifra = destinoCifras;
          this.altos = destinoAltos;
        };
        if (this.reducido()) return terminar();
        // Si el navegador pausa los cuadros (pestaña oculta), igual se llega al final.
        setTimeout(terminar, DURACION + 100);
        const origenCifras = { ...this.cifra };
        const origenAltos = [...this.altos];
        const inicio = performance.now();
        const paso = ahora => {
          if (turno !== this.turno) return; // Una animación más nueva manda.
          const t = (ahora - inicio) / DURACION;
          const cifras = {};
          for (const [nombre, destino] of Object.entries(destinoCifras)) {
            cifras[nombre] = Math.round(interpolar(origenCifras[nombre] ?? 0, destino, t));
          }
          this.cifra = cifras;
          this.altos = destinoAltos.map((alto, i) => interpolar(origenAltos[i] ?? 0, alto, t));
          if (t < 1) requestAnimationFrame(paso);
        };
        requestAnimationFrame(paso);
      },
    };
  }

  const api = { interpolar, periodoValido, periodoGuardado, inicioAdmin };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else raiz.inicioAdmin = inicioAdmin;
})(typeof window !== 'undefined' ? window : globalThis);
