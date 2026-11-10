/*
 * Menú lateral: el botón lo reduce a un riel de iconos o lo abre, y la elección
 * se recuerda en este navegador. Se carga sin `defer` para aplicarla antes de
 * pintar y que el menú no «salte».
 */
(function () {
  "use strict";

  const CLAVE = "menu-lateral-2"; // «iconos» o «abierto»
  const shell = document.currentScript.parentElement;

  function guardada() {
    try {
      return localStorage.getItem(CLAVE);
    } catch {
      return null; // sin almacenamiento (ventana privada): manda el valor por defecto
    }
  }

  function guardar(valor) {
    try {
      localStorage.setItem(CLAVE, valor);
    } catch {
      // sin almacenamiento: el menú cambia igual, solo que no se recuerda
    }
  }

  shell.classList.toggle("shell-fijo", guardada() === "iconos");

  shell.addEventListener("click", (evento) => {
    const boton = evento.target.closest(".lateral-fijar");
    if (!boton) return;
    const reducido = shell.classList.toggle("shell-fijo");
    guardar(reducido ? "iconos" : "abierto");
    boton.blur();
  });
})();
