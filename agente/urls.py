from django.urls import path

from . import views

urlpatterns = [
    path("", views.consulta, name="agente"),
    path("adjuntar/", views.adjuntar, name="agente_adjuntar"),
    path("preguntar/", views.preguntar, name="agente_preguntar"),
]
