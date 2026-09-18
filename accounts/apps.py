from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        post_migrate.connect(self.grant_account_permissions, sender=self)

    def grant_account_permissions(self, using, **kwargs):
        from django.contrib.auth.models import Group, Permission

        group = Group.objects.using(using).filter(name="Administrador").first()
        if group:
            permissions = Permission.objects.using(using).filter(
                content_type__app_label="accounts",
                codename__in=("add_user", "change_user", "view_user"),
            )
            group.permissions.add(*permissions)
