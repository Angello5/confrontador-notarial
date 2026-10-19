from django.urls import path

from .views import home, home_datos

urlpatterns = [
    path("", home, name="home"),
    path("inicio/datos/", home_datos, name="home_datos"),
]
