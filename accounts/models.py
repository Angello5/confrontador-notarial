from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    force_password_change = models.BooleanField(default=False)
    session_version = models.PositiveIntegerField(default=0)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    login_locked_until = models.DateTimeField(null=True, blank=True)
