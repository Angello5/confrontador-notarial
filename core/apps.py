from django.apps import AppConfig
from django.core.checks import Error, Tags, register


def version_sql_server(app_configs, databases=None, **kwargs):
    """F63: corre con `migrate` y `check --database`; antes de 2016 no hay JSON."""
    from django.db import connections

    return [
        Error(
            "Se necesita SQL Server 2016 o posterior.",
            hint="Actualice SQL Server antes de instalar el ERP.",
            id="core.E001",
        )
        for alias in databases or ()
        if connections[alias].vendor == "microsoft"
        and connections[alias].sql_server_version < 2016
    ]


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        register(Tags.database)(version_sql_server)
