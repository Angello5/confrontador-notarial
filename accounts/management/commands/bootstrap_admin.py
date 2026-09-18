from builtins import input
from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Crea el primer Administrador con cambio de clave obligatorio."

    def handle(self, *args, **options):
        username = input("Nombre de usuario: ").strip()
        if not username:
            raise CommandError("Debe indicar un nombre de usuario.")
        password = getpass("Clave temporal: ")
        confirmation = getpass("Repita la clave temporal: ")
        if password != confirmation:
            raise CommandError("Las claves no coinciden.")

        user_model = get_user_model()
        user = user_model(username=username, is_staff=True, force_password_change=True)
        try:
            user_model._meta.get_field("username").clean(username, user)
            validate_password(password, user)
        except ValidationError as error:
            raise CommandError(
                "La cuenta o la clave temporal no cumplen los requisitos."
            ) from error

        with transaction.atomic():
            role = Group.objects.select_for_update().get(name="Administrador")
            if user_model.objects.filter(
                is_active=True, groups__name="Administrador"
            ).exists():
                raise CommandError("Ya existe un Administrador activo.")
            if user_model.objects.filter(username=username).exists():
                raise CommandError("Ese nombre de usuario ya existe.")
            user.set_password(password)
            user.save()
            user.groups.add(role)

        self.stdout.write("Se creó el Administrador inicial.")
