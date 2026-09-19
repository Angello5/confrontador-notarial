# Assets locales de F2

Versiones descargadas de los paquetes npm oficiales. Mantener estos archivos
locales evita dependencias de CDN durante la ejecución.

| Paquete | Versión | Licencia | Archivo local ← ruta del paquete npm (SHA-256) |
|---|---:|---|---|
| AdminLTE (`admin-lte`) | 4.9.1 | MIT | `adminlte/LICENSE` ← `LICENSE` (`9e8b0d4e7ce8c13e67a2373d5094910c263fd95b1e49bdf45dc2a9813be5996b`); `adminlte/adminlte.min.css` ← `dist/css/adminlte.min.css` (`0934e1e6298dd4666440703dd613fdbb1a3c5f1554467923c29464ef4a5682ea`); `adminlte/adminlte.min.js` ← `dist/js/adminlte.min.js` (`922181e2098af61f2c6d8e997b1acccf37bdfa27c9dd0c9e20d15282ae31eddb`) |
| Bootstrap | 5.3.8 | MIT | `bootstrap/LICENSE` ← `LICENSE` (`4620c84ad5ce8602ff65640ed6b7c8b78ebb9e036584f0ebc1ccc88206a4bb51`); `bootstrap/bootstrap.bundle.min.js` ← `dist/js/bootstrap.bundle.min.js` (`e4fd49181388c48ec5040bd3fe66f57c29c8e67fcd8502b3354b96ec7ab47cc7`) |
| Alpine.js (`alpinejs`) | 3.17.3 | MIT | `alpine/alpine.min.js` ← `dist/cdn.min.js` (`4d4b4bab885f9d2d4534099fe2bdc1234a30cf9dc6ee56869fc385f046cebd70`); `alpine/LICENSE.md` ← [`LICENSE.md` en GitHub, tag `v3.17.3`](https://github.com/alpinejs/alpine/blob/v3.17.3/LICENSE.md) (`08b7502da6e7aa1d0bbdc97d220fbf669b9366c61bd0f072238283c89bc4773a`) |

Fuentes: `https://registry.npmjs.org/admin-lte/4.9.1`,
`https://registry.npmjs.org/bootstrap/5.3.8` y
`https://registry.npmjs.org/alpinejs/3.17.3`. Los archivos se tomaron de las
rutas indicadas dentro de sus paquetes npm; cada paquete declara su licencia MIT.

Los comentarios `sourceMappingURL` de AdminLTE y Bootstrap apuntan a archivos
`.map` que no se incluyen; los mapas no son necesarios para ejecutar los assets.
