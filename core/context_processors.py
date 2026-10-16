import hashlib
from functools import cache

from django.conf import settings


# ponytail: se calcula una vez por proceso; tras actualizar hay que reiniciar el
# servidor (la skill local y el despliegue ya lo hacen). ManifestStaticFilesStorage en F8.
@cache
def version_estaticos(raiz):
    """Huella corta de los CSS y JS propios: la URL cambia cuando cambia su contenido."""
    huella = hashlib.sha256()
    for archivo in sorted(raiz.rglob("*")):
        if archivo.suffix in {".css", ".js"}:
            huella.update(archivo.read_bytes())
    return huella.hexdigest()[:10]


def marca(request):
    nombre = settings.ERP_NOMBRE.strip()
    return {
        "erp_nombre": nombre,
        "erp_logo": settings.ERP_LOGO,
        "erp_direccion": settings.ERP_DIRECCION,
        "erp_iniciales": "".join(p[0] for p in nombre.split()[:2]).upper(),
        "static_v": version_estaticos(settings.STATICFILES_DIRS[0]),
    }
