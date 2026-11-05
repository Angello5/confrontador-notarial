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

  // F73: un rango solo se aplica con las dos fechas y en orden.
  function rangoValido(desde, hasta) {
    return Boolean(desde && hasta && desde <= hasta);
  }

  function parametros({ periodo, filtro, desde, hasta, persona }) {
    const valores = new URLSearchParams({ periodo });
    if (filtro && (filtro !== 'rango' || rangoValido(desde, hasta))) {
      valores.set('filtro', filtro);
      if (filtro === 'rango') {
        valores.set('desde', desde);
        valores.set('hasta', hasta);
      }
    }
    if (persona) valores.set('usuario', persona);
    return valores.toString();
  }

  function restarDias(iso, dias) {
    const fecha = new Date(`${iso}T12:00:00`);
    fecha.setDate(fecha.getDate() - dias);
    const dos = n => String(n).padStart(2, '0');
    return `${fecha.getFullYear()}-${dos(fecha.getMonth() + 1)}-${dos(fecha.getDate())}`;
  }

  function fechaCorta(iso) {
    const [anio, mes, dia] = (iso || '').split('-');
    return dia ? `${dia}/${mes}/${anio}` : '';
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
      pedido: 0,
      filtro: null,
      persona: '',
      desde: '',
      hasta: '',
      filtros: [
        { id: 'hoy', texto: 'Hoy' },
        { id: 'ayer', texto: 'Ayer' },
        { id: 'semana', texto: 'Esta semana' },
        { id: 'mes', texto: 'Este mes' },
        { id: 'rango', texto: 'Rango de fechas…' },
      ],

      get rangoIncompleto() {
        return this.filtro === 'rango' && !rangoValido(this.desde, this.hasta);
      },

      // Lo que muestra «Mostrando» sale de lo que el servidor aplicó de verdad.
      get textoFiltro() {
        const elegido = this.filtros.find(f => f.id === this.datos.filtro);
        if (!elegido) return '';
        return elegido.id === 'rango'
          ? `${fechaCorta(this.datos.desde)} – ${fechaCorta(this.datos.hasta)}`
          : elegido.texto;
      },

      get hayFiltros() {
        return Boolean(this.datos.filtro || this.datos.persona);
      },

      elegirFiltro(id) {
        this.filtro = this.filtro === id && id !== 'rango' ? null : id;
        if (this.filtro === 'rango' && !this.desde) {
          this.hasta = this.datos.hoy;
          this.desde = restarDias(this.datos.hoy, 14);
        }
        this.actualizar();
      },

      quitarFiltro() {
        this.filtro = null;
        this.actualizar();
      },

      quitarPersona() {
        this.persona = '';
        this.actualizar();
      },

      limpiar() {
        this.filtro = null;
        this.persona = '';
        this.actualizar();
      },

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
        // F73: al cambiar filtros seguidos, solo manda la última respuesta.
        const pedido = (this.pedido = this.pedido + 1);
        const consulta = parametros(this);
        try {
          const respuesta = await fetch(`/inicio/datos/?${consulta}`, {
            headers: { Accept: 'application/json' },
            credentials: 'same-origin',
          });
          if (!respuesta.ok) throw new Error(String(respuesta.status));
          const datos = await respuesta.json();
          if (pedido !== this.pedido) return;
          // Al cambiar de periodo cambia el número de barras: crecen desde cero.
          if (datos.actividad.length !== this.altos.length) this.altos = datos.actividad.map(() => 0);
          this.datos = datos;
          this.error = false;
          this.animar(datos);
        } catch (error) {
          if (pedido === this.pedido) this.error = true; // Se conservan los datos ya mostrados.
        } finally {
          if (pedido === this.pedido) {
            this.cargando = false;
            this.programar();
          }
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

  const api = { interpolar, periodoValido, periodoGuardado, rangoValido, parametros, restarDias, fechaCorta, inicioAdmin };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else raiz.inicioAdmin = inicioAdmin;
})(typeof window !== 'undefined' ? window : globalThis);
