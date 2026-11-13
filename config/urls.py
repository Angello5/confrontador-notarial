from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("core.urls")),
    path("expedientes/", include("expedientes.urls")),
    path("agente/", include("agente.urls")),
]
