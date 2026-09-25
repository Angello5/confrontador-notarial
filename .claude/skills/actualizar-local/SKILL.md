---
name: actualizar-local
description: Actualiza el ERP que corre en local a lo último de main y lo reinicia. Úsala cuando el usuario confirme que mergeó un PR, o cuando diga "actualiza", "actualiza la página", "ya hice el merge", "levántalo de nuevo" o "reinicia". Trae main, aplica migraciones y relanza el servidor y el worker de extracción, verificando que los dos quedan vivos.
---

# Actualizar el ERP local

Después de mergear un PR, el ERP que corre en `127.0.0.1:8000` sigue con el
código viejo. Esta skill lo pone al día.

## Contexto

- Copia de trabajo: `~/Documents/Github/confrontador-notarial`
- Entorno: `~/.config/confrontador-dev.env` (fuera del repo; sin él Django no
  arranca porque falta la clave secreta)
- Intérprete: `/home/pibe/.venvs/confrontador/bin/python`
- Worker de extracción: `~/pruebas-confrontador/worker.sh`
- Base de datos: contenedor Docker `confrontador-test-pg`

## Pasos

### 1. Parar lo que corre, sin matar tu propia sesión

```bash
ps -eo pid,cmd | grep -E "manage.py runserver|pruebas-confrontador/worker.sh" \
  | grep -v grep | awk '{print $1}' | while read p; do kill "$p" 2>/dev/null; done
```

**Nunca uses `pkill -f "manage.py runserver"`.** El patrón coincide con la
propia línea de comandos del shell que lo ejecuta y mata la sesión: ha pasado
tres veces, con salida 144.

### 2. Asegurar la base de datos

El contenedor no sobrevive a un reinicio de la máquina.

```bash
docker ps --filter name=confrontador --format '{{.Names}}' | grep -q . \
  || docker start confrontador-test-pg
```

### 3. Traer main y migrar

```bash
cd ~/Documents/Github/confrontador-notarial
git pull --ff-only origin main
. ~/.config/confrontador-dev.env
python manage.py migrate
```

Si `git pull` falla porque hay cambios locales, **para y avisa**: no descartes
trabajo sin preguntar.

### 4. Arrancar servidor y worker

```bash
nohup python manage.py runserver 127.0.0.1:8000 > /tmp/runserver.log 2>&1 < /dev/null &
setsid nohup ~/pruebas-confrontador/worker.sh > ~/pruebas-confrontador/worker.log 2>&1 < /dev/null &
```

Sin el worker, los documentos se quedan en «Pendiente» para siempre. Es el
olvido más frecuente.

### 5. Verificar antes de decir que está listo

```bash
sleep 8
curl -s -o /dev/null -w "login HTTP %{http_code}\n" http://127.0.0.1:8000/accounts/login/
head -1 ~/pruebas-confrontador/worker.log
git log --oneline -1
```

El servidor debe responder `200` y el worker debe haber escrito su línea de
arranque. Si el worker no arrancó, comprueba que el script existe: vivía en un
directorio temporal y el sistema lo borró una vez.

## Qué contarle al usuario

- La dirección: **http://127.0.0.1:8000/expedientes/**
- **Qué trae esta actualización**, mirando los commits nuevos del `pull`. No
  basta con decir «actualizado»: dile qué cambia de lo que va a ver.
- Si algún PR relevante sigue **sin mergear**, avísale de qué seguirá viendo
  mal, para que no lo reporte como fallo nuevo.

## Advertencias que ahorran tiempo

- **Los expedientes antiguos no se benefician de los cambios del núcleo.** Su
  texto ya está extraído y guardado. Para probar algo del núcleo hay que
  **subir los documentos otra vez en un expediente nuevo**.
- **Si procesa sospechosamente rápido, es la caché.** La llave cubre los
  modelos de OCR, la versión de rapidocr y el formato de lo que guarda, así
  que se invalida sola. Si aun así hay dudas:
  `rm -f ~/.cache/notaria-ocr/*.json`
- **Los PDF escaneados tardan de verdad**: cada página pasa por OCR. Un
  expediente de 40 páginas son varios minutos. Lento no es colgado.
