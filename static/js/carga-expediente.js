/* F34: transferencias continuas; el OCR y la comparación viven en el servidor. */
(function (raiz) {
  'use strict';
  function crearCarga(config) {
    return {
      documentos: config.documentos || [], confrontaciones: config.borradores || [],
      transferencias: [], mensaje: '', intencion: null, enviandoSolicitud: false,
      ocupada: false, secuencia: 0, temporizador: null, consultando: false,
      revision: 0, resultadoEsperado: (config.borradores || []).find(b => b.solicitada)?.id ?? null,
      etiquetas: { PENDIENTE: 'En cola', PROCESANDO: 'Leyendo', LISTO: 'Preparado', ERROR: 'Necesita atención' },
      etapas: { PREPARANDO: 'Preparando documentos', PREPARADO: 'Documentos preparados', EN_COLA: 'Confrontación solicitada', CONFRONTANDO: 'Confrontando…', LISTO: 'Resultado disponible', CANCELADA: 'Confrontación cancelada', CAMBIADA: 'Documentos actualizados', ERROR: 'Necesita atención' },
      eliminar: null, sobre: '',
      textos: { VACIO: 'Sin documentos', PROCESANDO: 'Procesando', LISTO: 'Listo', ERROR: 'Con error' },
      tonos: { VACIO: 'neutro', PROCESANDO: '', LISTO: 'exito', ERROR: 'peligro' },
      iconos: { VACIO: '#i-info', PROCESANDO: '#i-loader', LISTO: '#i-circle-check', ERROR: '#i-circle-alert' },
      get resumen() {
        const contar = estado => this.documentos.filter(d => d.estado === estado).length;
        return { total: this.documentos.length, pendientes: contar('PENDIENTE'), procesando: contar('PROCESANDO'), listos: contar('LISTO'), errores: contar('ERROR') };
      },
      get estado() {
        const r = this.resumen;
        if (!r.total) return 'VACIO';
        if (r.errores) return 'ERROR';
        return r.pendientes || r.procesando ? 'PROCESANDO' : 'LISTO';
      },
      // Riel: 1 fuentes, 2 borrador, 3 procesamiento, 4 resultado.
      get pasoActual() {
        // F43: el kardex vehicular no tiene zona de minuta.
        const conMinuta = (config.roles || []).some(([rol]) => rol === 'MINUTA');
        if (!this.delRol('CLIENTE').length || (conMinuta && !this.delRol('MINUTA').length)) return 1;
        if (!this.delRol('BORRADOR').length) return 2;
        return this.estado === 'LISTO' ? 4 : 3;
      },
      get faltan() {
        const faltantes = (config.roles || []).filter(([rol]) => !this.delRol(rol).length).map(([, etiqueta]) => etiqueta);
        if (!faltantes.length) return '';
        return (faltantes.length === 1 ? 'Falta: ' : 'Faltan: ') + faltantes.join(', ') + '.';
      },
      enCurso(id) {
        const c = this.estadoDe(id);
        return Boolean(c.solicitada || c.etapa === 'CONFRONTANDO' || this.intencion === id);
      },
      get pendientes() { return this.transferencias.some(t => ['PENDIENTE', 'SUBIENDO'].includes(t.estado)); },
      get fallidas() { return this.transferencias.some(t => t.estado === 'ERROR'); },
      delRol(rol) { return this.documentos.filter(d => d.rol === rol); },
      cargasDelRol(rol) { return this.transferencias.filter(t => t.rol === rol && t.estado !== 'LISTO'); },
      estadoDe(id) { return this.confrontaciones.find(c => c.id === id) || {}; },
      url(id, accion) { return config.base + 'documentos/' + id + '/' + accion + '/'; },
      csrf() { return this.$root.querySelector('[name=csrfmiddlewaretoken]').value; },
      iniciar() { this.actualizar(); },
      destroy() { clearTimeout(this.temporizador); },
      alSalir(event) { if (this.pendientes) { event.preventDefault(); event.returnValue = ''; } },
      seleccionar(event, rol) { this.adjuntar(Array.from(event.target.files || []), rol); event.target.value = ''; },
      adjuntar(archivos, rol) {
        this.revision++;
        for (const archivo of archivos) {
          const extension = archivo.name.split('.').pop().toLowerCase();
          let error = '';
          if (!archivo.size) error = 'El archivo está vacío.';
          else if (archivo.size > config.maximo) error = 'El archivo supera el tamaño máximo permitido.';
          else if (!config.extensiones.includes(extension)) error = 'Formato de archivo no admitido.';
          this.transferencias.push({ id: ++this.secuencia, archivo, nombre: archivo.name, rol, estado: error ? 'ERROR' : 'PENDIENTE', error, progreso: 0, xhr: null });
        }
        this.procesarCola();
      },
      async procesarCola() {
        if (this.ocupada) return;
        this.ocupada = true;
        try {
          let tarea;
          while ((tarea = this.transferencias.find(t => t.estado === 'PENDIENTE'))) {
            try { await this.subir(tarea); }
            catch (_) { tarea.estado = 'ERROR'; tarea.error = 'No se pudo iniciar la carga. Recargue la página y vuelva a intentarlo.'; }
          }
        } finally { this.ocupada = false; }
        if (this.intencion !== null) {
          const id = this.intencion;
          this.intencion = null;
          await this.confrontar(id);
        }
      },
      subir(tarea) {
        tarea.estado = 'SUBIENDO';
        return new Promise(resolve => {
          const xhr = new XMLHttpRequest();
          tarea.xhr = xhr;
          xhr.open('POST', config.base + 'documentos/');
          xhr.setRequestHeader('Accept', 'application/json');
          xhr.setRequestHeader('X-CSRFToken', this.csrf());
          xhr.timeout = 120000;
          xhr.upload.onprogress = e => { if (e.lengthComputable) tarea.progreso = Math.floor(e.loaded / e.total * 100); };
          const terminar = () => { tarea.xhr = null; this.actualizar(); resolve(); };
          xhr.onload = () => {
            try {
              const datos = JSON.parse(xhr.responseText);
              if (![200, 400].includes(xhr.status)) throw new Error();
              for (const documento of datos.recibidos || []) {
                if (!this.documentos.some(d => d.id === documento.id)) this.documentos.push(documento);
              }
              this.revision++;
              tarea.error = (datos.errores || []).map(e => e.mensaje).join(' ');
              tarea.estado = tarea.error || !(datos.recibidos || []).length ? 'ERROR' : 'LISTO';
              if (tarea.estado === 'LISTO') tarea.archivo = null;
            } catch (_) {
              tarea.estado = 'ERROR';
              tarea.error = 'No se pudo confirmar la recepción. Revise su sesión y la lista antes de reintentar.';
            }
            terminar();
          };
          xhr.onerror = xhr.ontimeout = () => { tarea.estado = 'ERROR'; tarea.error = 'Conexión interrumpida. Revise la lista y reintente la carga.'; terminar(); };
          xhr.onabort = () => { tarea.estado = 'CANCELADA'; tarea.error = 'Transferencia cancelada. Si ya se recibió, aparecerá en la lista.'; terminar(); };
          const datos = new FormData();
          datos.append('rol', tarea.rol);
          datos.append('archivos', tarea.archivo);
          xhr.send(datos);
        });
      },
      cancelarCarga(tarea) {
        this.intencion = null;
        if (tarea.xhr) tarea.xhr.abort();
        else { tarea.estado = 'CANCELADA'; tarea.archivo = null; }
      },
      reintentar(tarea) { if (!tarea.archivo) return; tarea.estado = 'PENDIENTE'; tarea.error = ''; tarea.progreso = 0; this.procesarCola(); },
      descartar(tarea) { this.transferencias = this.transferencias.filter(t => t.id !== tarea.id); },
      recibirEstado(datos) {
        this.documentos = datos.documentos.map(d => ({ ...this.documentos.find(a => a.id === d.id), ...d }));
        this.confrontaciones = datos.borradores;
        const esperado = this.estadoDe(this.resultadoEsperado);
        if (['CANCELADA', 'CAMBIADA', 'ERROR'].includes(esperado.etapa)) this.resultadoEsperado = null;
        if (this.resultadoEsperado !== null && esperado.resultado_listo && !this.pendientes && !this.fallidas) {
          const id = this.resultadoEsperado;
          this.resultadoEsperado = null;
          raiz.location.assign(this.url(id, 'resultado'));
        }
      },
      async actualizar() {
        if (this.consultando) return;
        this.consultando = true;
        const revision = this.revision;
        clearTimeout(this.temporizador);
        try {
          const respuesta = await fetch(config.base + 'estado/', { headers: { Accept: 'application/json' }, cache: 'no-store' });
          if (!respuesta.ok) throw new Error();
          const datos = await respuesta.json();
          if (revision === this.revision) this.recibirEstado(datos);
        } catch (_) { this.mensaje = 'No se pudo actualizar el estado. Revise su conexión o vuelva a iniciar sesión.'; }
        finally {
          this.consultando = false;
          // También descubre cambios hechos en otra sesión; nunca solapa peticiones.
          this.temporizador = setTimeout(() => this.actualizar(), 2000);
        }
      },
      async mutar(url) {
        const respuesta = await fetch(url, { method: 'POST', headers: { Accept: 'application/json', 'X-CSRFToken': this.csrf() } });
        const datos = await respuesta.json();
        if (!respuesta.ok) throw new Error(datos.mensaje || 'No se pudo completar la acción.');
        return datos;
      },
      async confrontar(id) {
        if (this.enviandoSolicitud) return;
        if (this.fallidas) { this.mensaje = 'Hay errores de carga. Reintente o retire los archivos fallidos antes de confrontar.'; return; }
        if (this.pendientes) { this.intencion = id; this.mensaje = 'Confrontaremos cuando termine la carga seleccionada. Puede seguir adjuntando.'; return; }
        await this.enviarSolicitud(id);
      },
      async enviarSolicitud(id) {
        this.enviandoSolicitud = true;
        try {
          const estado = await this.mutar(this.url(id, 'confrontar'));
          this.resultadoEsperado = id;
          this.mensaje = estado.resultado_listo ? 'Resultado preparado, sin repetir el análisis.' : 'Confrontación solicitada. Puede salir y volver después.';
          await this.actualizar();
        } catch (error) { this.mensaje = error.message || 'No se pudo solicitar. Revise su sesión.'; }
        finally { this.enviandoSolicitud = false; }
      },
      async cancelar(id) {
        this.intencion = null;
        this.resultadoEsperado = null;
        try { await this.mutar(this.url(id, 'cancelar-confrontacion')); this.mensaje = 'Confrontación cancelada. La lectura adelantada se conserva.'; await this.actualizar(); }
        catch (_) { this.mensaje = 'No se pudo cancelar. Revise su conexión y vuelva a intentarlo.'; }
      },
      async quitar(id) {
        if (!raiz.confirm('¿Confirma eliminar este documento?')) return;
        try {
          const respuesta = await fetch(this.url(id, 'eliminar'), { method: 'POST', headers: { Accept: 'application/json', 'X-CSRFToken': this.csrf(), 'Content-Type': 'application/x-www-form-urlencoded' }, body: 'confirmado=1' });
          const datos = await respuesta.json();
          if (!respuesta.ok || datos.eliminado !== true) throw new Error();
          this.revision++;
          this.documentos = this.documentos.filter(d => d.id !== id);
          this.mensaje = 'Documento eliminado.';
          await this.actualizar();
        } catch (_) { this.mensaje = 'No se pudo eliminar el documento. Intente nuevamente.'; }
      },
    };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { crearCarga };
  else raiz.crearCarga = crearCarga;
})(typeof window !== 'undefined' ? window : globalThis);
