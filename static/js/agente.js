/* F75: chat del agente. La conversación y los adjuntos viven solo en el navegador;
   el servidor lee cada archivo, devuelve su texto y no guarda nada. */
(function (raiz) {
  'use strict';
  function escapar(t) {
    return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function aHtml(texto) {
    let h = escapar(texto);
    h = h.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    h = h.replace(/(^|[\s(])(https?:\/\/[^\s)<]+)/g, '$1<a href="$2" target="_blank" rel="noopener noreferrer">$2</a>');
    h = h.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    return h.replace(/\n/g, '<br>');
  }
  raiz.agenteChat = function (config) {
    return {
      mensajes: [], pregunta: '', documentos: [], leyendo: 0, aviso: '', cargando: false,
      html: aHtml,
      get total() { return this.documentos.reduce((n, d) => n + d.texto.length, 0); },
      get excede() { return this.total > config.maxContexto; },
      bajar() { this.$nextTick(() => { const c = this.$refs.hilo; c.scrollTop = c.scrollHeight; }); },
      nueva() { if (!this.cargando) { this.mensajes = []; this.pregunta = ''; this.documentos = []; this.aviso = ''; } },
      usar(texto) { this.pregunta = texto; this.enviar(); },
      quitar(i) { this.documentos.splice(i, 1); },
      async adjuntar(evento) {
        const archivos = Array.from(evento.target.files);
        evento.target.value = '';
        this.aviso = '';
        for (const archivo of archivos) {
          if (this.documentos.length + this.leyendo >= config.maximo) { this.aviso = `Máximo ${config.maximo} archivos.`; break; }
          this.leyendo++;
          try {
            const datos = new FormData();
            datos.append('archivo', archivo);
            const r = await fetch(config.urlAdjuntar, { method: 'POST', headers: { 'X-CSRFToken': config.csrf() }, body: datos });
            const d = await r.json().catch(() => ({}));
            if (r.ok) {
              this.documentos.push({ nombre: d.nombre, texto: d.texto, aviso: d.aviso });
              if (d.aviso) this.aviso = `${d.nombre}: ${d.aviso}`;
            }
            else this.aviso = `${archivo.name}: ${d.error || 'no se pudo leer.'}`;
          } catch (e) {
            this.aviso = `${archivo.name}: sin conexión con el servidor.`;
          }
          this.leyendo--;
        }
      },
      async enviar() {
        const texto = this.pregunta.trim();
        if (!texto || this.cargando || this.leyendo) return;
        const historial = this.mensajes.filter(m => !m.error).map(m => ({ rol: m.rol, texto: m.texto }));
        this.mensajes.push({ rol: 'usuario', texto });
        this.pregunta = '';
        this.cargando = true;
        this.bajar();
        try {
          const r = await fetch(config.url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': config.csrf() },
            body: JSON.stringify({ pregunta: texto, documentos: this.documentos, historial }),
          });
          const d = await r.json().catch(() => ({}));
          this.mensajes.push(r.ok ? { rol: 'agente', texto: d.respuesta, aviso: d.aviso }
            : { rol: 'agente', texto: d.error || 'No se pudo consultar al agente.', error: true });
        } catch (e) {
          this.mensajes.push({ rol: 'agente', texto: 'Sin conexión con el servidor.', error: true });
        }
        this.cargando = false;
        this.bajar();
      },
    };
  };
})(window);
