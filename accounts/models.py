from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import salted_hmac


class User(AbstractUser):
    force_password_change = models.BooleanField(default=False)
    session_version = models.PositiveIntegerField(default=0)

    def _get_session_auth_hash(self, secret=None):
        key_salt = "django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"
        return salted_hmac(
            key_salt,
            f"{self.password}:{self.session_version}",
            secret=secret,
            algorithm="sha256",
        ).hexdigest()
