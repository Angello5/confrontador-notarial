from django.contrib.admin import AdminSite


class ERPAdminSite(AdminSite):
    site_header = "Administración"
    site_title = "Administración"
    index_title = "Gestión de cuentas"

    def has_permission(self, request):
        user = request.user
        return (
            super().has_permission(request)
            and user.groups.filter(name="Administrador").exists()
        )
