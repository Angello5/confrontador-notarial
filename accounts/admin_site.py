from django.contrib.admin import AdminSite
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse


def resumen_cuentas(lista):
    """F49: recuadros Todas/Activas/Inactivas que abren la lista ya filtrada."""
    from .models import User

    cuentas = User.objects.aggregate(
        activas=Count("pk", filter=Q(is_active=True)),
        inactivas=Count("pk", filter=Q(is_active=False)),
    )
    return [
        {
            "etiqueta": "Todas",
            "valor": cuentas["activas"] + cuentas["inactivas"],
            "enlace": lista,
            "apoyo": "Registradas en el sistema",
        },
        {
            "etiqueta": "Activas",
            "valor": cuentas["activas"],
            "enlace": f"{lista}?is_active__exact=1",
            "tono": "verde",
            "apoyo": "Con acceso al ERP",
        },
        {
            "etiqueta": "Inactivas",
            "valor": cuentas["inactivas"],
            "enlace": f"{lista}?is_active__exact=0",
            "tono": "gris",
            "apoyo": "Sin acceso al ERP",
        },
    ]


class ERPAdminSite(AdminSite):
    site_header = "Administración"
    site_title = "Administración"
    index_title = "Gestión de cuentas"
    # F49: un solo modelo; las migas de pan bastan para navegar.
    enable_nav_sidebar = False

    def has_permission(self, request):
        user = request.user
        return (
            super().has_permission(request)
            and user.groups.filter(name="Administrador").exists()
        )

    def _lista_usuarios(self):
        return redirect(
            reverse("admin:accounts_user_changelist", current_app=self.name)
        )

    # El admin tiene un solo modelo: el inicio y la página de la aplicación
    # llevan directo a la lista de usuarios, que reúne el resumen y la gestión.
    def index(self, request, extra_context=None):
        return self._lista_usuarios()

    def app_index(self, request, app_label, extra_context=None):
        return self._lista_usuarios()
