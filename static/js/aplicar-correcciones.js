/* F40: aplicar correcciones con una ventana de avance y descarga directa.
   Se mezcla en revisionConfrontacion(); usa su estado `modal`. Sin JavaScript,
   el formulario se envía como antes y se muestra la página «Documento corregido».
   El navegador elige la carpeta: la página no puede leerla, así que se indica
   la carpeta de descargas por defecto. */
window.aplicarCorrecciones = function () {
  const FALLA = 'No se pudieron aplicar las correcciones. Intente de nuevo.';
  return {
    aplicando: { fase: null, progreso: 0, archivo: '', descarga: '', error: '', resumen: null },
    async aplicar(form) {
      const a = this.aplicando;
      Object.assign(a, { fase: 'APLICANDO', progreso: 0, archivo: '', descarga: '', error: '', resumen: null });
      this.modal = 'aplicando';
      // El servidor no informa su avance: la barra se acerca al 60 % mientras responde.
      const avance = setInterval(() => { a.progreso += (60 - a.progreso) * 0.08; }, 150);
      try {
        const respuesta = await fetch(form.action, {
          method: 'POST', body: new FormData(form), credentials: 'same-origin',
          headers: { Accept: 'application/json' },
        });
        const datos = await respuesta.json().catch(() => ({}));
        if (!respuesta.ok) throw new Error(datos.error || FALLA);
        Object.assign(a, { fase: 'DESCARGANDO', progreso: 60, archivo: datos.archivo, descarga: datos.descarga, resumen: datos });
        clearInterval(avance);
        await this.descargarCorregido(datos.descarga, datos.archivo);
        Object.assign(a, { fase: 'LISTO', progreso: 100 });
      } catch (error) {
        Object.assign(a, { fase: 'ERROR', error: error.message || FALLA });
      } finally {
        clearInterval(avance);
      }
    },
    async descargarCorregido(url, archivo) {
      const respuesta = await fetch(url, { credentials: 'same-origin' });
      if (!respuesta.ok) throw new Error('El documento corregido se generó, pero no se pudo descargar. Use «Descargar de nuevo».');
      const total = Number(respuesta.headers.get('Content-Length')) || 0;
      const lector = respuesta.body.getReader();
      const partes = [];
      let recibidos = 0;
      for (let parte = await lector.read(); !parte.done; parte = await lector.read()) {
        partes.push(parte.value);
        recibidos += parte.value.length;
        if (total) this.aplicando.progreso = 60 + (40 * recibidos) / total;
      }
      const enlace = document.createElement('a');
      enlace.href = URL.createObjectURL(new Blob(partes, { type: respuesta.headers.get('Content-Type') || 'application/octet-stream' }));
      enlace.download = archivo;
      document.body.appendChild(enlace);
      enlace.click();
      enlace.remove();
      setTimeout(() => URL.revokeObjectURL(enlace.href), 60000);
    },
    // métodos y no getters: el componente mezcla este objeto con «...», que copia
    // el valor de un getter una sola vez
    aplicandoTitulo() {
      return {
        APLICANDO: 'Aplicando correcciones',
        DESCARGANDO: 'Descargando el documento corregido',
        LISTO: 'Documento corregido descargado',
        ERROR: 'No se aplicó ninguna corrección',
      }[this.aplicando.fase] || '';
    },
    aplicandoTerminado() {
      return this.aplicando.fase === 'LISTO' || this.aplicando.fase === 'ERROR';
    },
  };
};
