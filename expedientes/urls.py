from django.urls import path

from . import views

urlpatterns = [
    path("", views.expediente_lista, name="expediente_lista"),
    path("<int:pk>/", views.expediente_detalle, name="expediente_detalle"),
    path("<int:pk>/documentos/", views.documento_subir, name="documento_subir"),
    path("<int:pk>/estado/", views.expediente_estado, name="expediente_estado"),
    path(
        "<int:pk>/documentos/<int:doc_id>/eliminar/",
        views.documento_eliminar,
        name="documento_eliminar",
    ),
    path(
        "<int:pk>/documentos/<int:doc_id>/confrontar/",
        views.documento_confrontar,
        name="documento_confrontar",
    ),
    path(
        "<int:pk>/confrontaciones/",
        views.expediente_historial,
        name="expediente_historial",
    ),
    path(
        "<int:pk>/confrontaciones/<int:corrida_id>/",
        views.corrida_detalle,
        name="corrida_detalle",
    ),
]
