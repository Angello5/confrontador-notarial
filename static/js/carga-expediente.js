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
      eliminar: null, sobre: '', reemplazar: null,
      iconosDocumento: { PENDIENTE: '#i-history', PROCESANDO: '#i-loader', LISTO: '#i-check', ERROR: '#i-circle-alert' },
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
      // F73: la columna de estado del kardex (propuesta 2b).
      get queHacer() {
        const fallidos = this.documentos.filter(d => d.estado === 'ERROR');
        if (fallidos.length === 1) return (fallidos[0].nombre || 'Un documento') + ' no se pudo leer. Elimínelo y vuelva a subir una copia más clara. Los demás siguen leyéndose.';
        if (fallidos.length) return 'Elimine los documentos que no se pudieron leer y vuelva a subir una copia más clara. Los demás siguen leyéndose.';
        if (this.pasoActual < 3) return this.faltan ? this.faltan + ' Adjúntelo para continuar.' : 'Adjunte los documentos para continuar.';
        if (this.estado === 'PROCESANDO') return 'No tiene que hacer nada. Puede seguir adjuntando o salir y volver después.';
        return this.hayResultado ? 'Ya puede ver el resultado de la confrontación.' : 'Ya puede confrontar el borrador.';
      },
      get hayResultado() { return this.confrontaciones.some(c => c.resultado_listo); },
      motivoBoton(id) {
        const r = this.resumen;
        if (r.errores) return 'Se habilita cuando el documento con error se reemplace y todos estén preparados.';
        const esperando = r.pendientes + r.procesando;
        if (esperando) return 'Esperando ' + esperando + (esperando === 1 ? ' documento' : ' documentos') + ': preparando documentos.';
        const c = this.estadoDe(id);
        return c.mensaje || this.etapas[c.etapa] || '';
      },
      detalleEtapa(numero) {
        const r = this.resumen;
        if (numero === 1) {
          const fuentes = r.total - this.delRol('BORRADOR').length;
          return fuentes ? fuentes + (fuentes === 1 ? ' documento cargado' : ' documentos cargados') : 'Sin documentos';
        }
        if (numero === 2) return this.delRol('BORRADOR')[0]?.nombre || 'Sin adjuntar';
        if (numero === 3) {
          if (this.estado === 'LISTO') return 'Todos los documentos leídos';
          if (!r.total) return 'Sin documentos';
          return r.listos + ' de ' + r.total + ' preparados' + (r.errores ? ' · ' + r.errores + ' con atención pendiente' : '');
        }
        if (this.pasoActual !== 4) return 'Se habilita cuando todo esté preparado';
        return this.hayResultado ? 'Pulse Ver resultado' : 'Pulse Confrontar borrador';
      },
      resumenGrupo(rol) {
        const lista = this.delRol(rol);
        if (!lista.length) return 'Obligatorio · sin documentos';
        const errores = lista.filter(d => d.estado === 'ERROR').length;
        if (errores) return errores + (errores === 1 ? ' necesita atención' : ' necesitan atención');
        const listos = lista.filter(d => d.estado === 'LISTO').length;
        return listos === lista.length ? 'Todo preparado' : listos + ' de ' + lista.length + ' preparados';
      },
      tonoGrupo(rol) {
        const lista = this.delRol(rol);
        if (lista.some(d => d.estado === 'ERROR')) return 'peligro';
        return lista.length && lista.every(d => d.estado === 'LISTO') ? 'exito' : '';
      },
      notaDocumento(d) {
        if (d.estado === 'ERROR') return 'No se pudo leer el archivo. Elimínelo y vuelva a subir una copia más clara.';
        if (d.estado === 'LISTO') return 'Texto extraído';
        if (d.estado === 'PENDIENTE') return 'En espera de lectura';
        if (!d.procesando_el) return 'Leyendo el texto';
        const hora = new Date(d.procesando_el).toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', hour12: false });
        return 'Leyendo el texto desde las ' + hora;
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
      async seleccionar(event, rol) {
        const archivos = Array.from(event.target.files || []);
        event.target.value = '';
        const anterior = this.reemplazar;
        this.reemplazar = null;
        // F73: se elimina el ilegible solo si hay con qué reemplazarlo.
        if (anterior !== null && archivos.length && !archivos.some(a => this.errorArchivo(a)) && !(await this.borrar(anterior))) return;
        this.adjuntar(archivos, rol);
      },
      volverASubir(documento, boton) {
        this.reemplazar = documento.id;
        boton.closest('.zona').querySelector('.zona-arrastre input[type=file]').click();
      },
      errorArchivo(archivo) {
        const extension = archivo.name.split('.').pop().toLowerCase();
        if (!archivo.size) return 'El archivo está vacío.';
        if (archivo.size > config.maximo) return 'El archivo supera el tamaño máximo permitido.';
        if (!config.extensiones.includes(extension)) return 'Formato de archivo no admitido.';
        return '';
      },
      adjuntar(archivos, rol) {
        this.revision++;
        for (const archivo of archivos) {
          const error = this.errorArchivo(archivo);
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
        await this.borrar(id);
      },
      async borrar(id) {
        try {
          const respuesta = await fetch(this.url(id, 'eliminar'), { method: 'POST', headers: { Accept: 'application/json', 'X-CSRFToken': this.csrf(), 'Content-Type': 'application/x-www-form-urlencoded' }, body: 'confirmado=1' });
          const datos = await respuesta.json();
          if (!respuesta.ok || datos.eliminado !== true) throw new Error();
          this.revision++;
          this.documentos = this.documentos.filter(d => d.id !== id);
          this.mensaje = 'Documento eliminado.';
          await this.actualizar();
          return true;
        } catch (_) { this.mensaje = 'No se pudo eliminar el documento. Intente nuevamente.'; return false; }
      },
    };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { crearCarga };
  else raiz.crearCarga = crearCarga;
})(typeof window !== 'undefined' ? window : globalThis);
