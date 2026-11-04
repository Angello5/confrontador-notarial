/*
 * Botón «Mostrar clave» junto a cada campo de contraseña (ingreso, cambio de
 * clave y administración de usuarios). El ícono viaja dentro del script porque
 * el admin de Django no carga el sprite de íconos.
 */
(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";
  var OJO = [
    "M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0",
  ];
  var OJO_TACHADO = [
    "M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49",
    "M14.084 14.158a3 3 0 0 1-4.242-4.242",
    "M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143",
    "m2 2 20 20",
  ];

  function icono(visible) {
    var svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("class", "ico");
    (visible ? OJO_TACHADO : OJO).forEach(function (d) {
      var p = document.createElementNS(NS, "path");
      p.setAttribute("d", d);
      svg.appendChild(p);
    });
    if (!visible) {
      var c = document.createElementNS(NS, "circle");
      c.setAttribute("cx", "12");
      c.setAttribute("cy", "12");
      c.setAttribute("r", "3");
      svg.appendChild(c);
    }
    return svg;
  }

  function preparar(campo) {
    if (campo.dataset.claveVisible) return;
    campo.dataset.claveVisible = "1";
    var envoltura = document.createElement("span");
    envoltura.className = "clave-campo";
    campo.parentNode.insertBefore(envoltura, campo);
    envoltura.appendChild(campo);
    // Espacio para el botón: en línea gana a los estilos de campo del ERP y del admin.
    campo.style.paddingRight = "48px";

    var boton = document.createElement("button");
    boton.type = "button";
    boton.className = "clave-ver";
    function pintar() {
      var visible = campo.type === "text";
      boton.replaceChildren(icono(visible));
      boton.setAttribute("aria-label", visible ? "Ocultar clave" : "Mostrar clave");
      boton.setAttribute("aria-pressed", visible ? "true" : "false");
      boton.title = visible ? "Ocultar clave" : "Mostrar clave";
    }
    boton.addEventListener("click", function () {
      campo.type = campo.type === "password" ? "text" : "password";
      pintar();
      campo.focus();
    });
    // Al enviar, la clave vuelve a ocultarse (no queda a la vista ni en el autocompletado).
    if (campo.form) {
      campo.form.addEventListener("submit", function () {
        campo.type = "password";
      });
    }
    pintar();
    envoltura.appendChild(boton);
  }

  function iniciar() {
    document.querySelectorAll('input[type="password"]').forEach(preparar);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
