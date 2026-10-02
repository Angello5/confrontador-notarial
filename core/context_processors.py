from django.conf import settings


def marca(request):
    nombre = settings.ERP_NOMBRE.strip()
    return {
        "erp_nombre": nombre,
        "erp_logo": settings.ERP_LOGO,
        "erp_direccion": settings.ERP_DIRECCION,
        "erp_iniciales": "".join(p[0] for p in nombre.split()[:2]).upper(),
    }
