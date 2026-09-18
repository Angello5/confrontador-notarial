"""Django authentication backend with database-persisted login lockout."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db import transaction
from django.utils import timezone


class LockoutBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user_model = get_user_model()
        username = username or kwargs.get(user_model.USERNAME_FIELD)
        if username is None or password is None:
            return None

        with transaction.atomic():
            user = (
                user_model._default_manager.select_for_update()
                .filter(**{user_model.USERNAME_FIELD: username})
                .first()
            )
            if user is None:
                user_model().set_password(password)
                return None
            now = timezone.now()
            valid_password = user.check_password(password)
            if user.login_locked_until and user.login_locked_until > now:
                return None

            if user.login_locked_until:
                user.failed_login_attempts = 0
                user.login_locked_until = None

            if valid_password and self.user_can_authenticate(user):
                user.failed_login_attempts = 0
                user.login_locked_until = None
                user.save(update_fields=["failed_login_attempts", "login_locked_until"])
                return user

            if self.user_can_authenticate(user):
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.login_locked_until = now + timedelta(minutes=15)
            user.save(update_fields=["failed_login_attempts", "login_locked_until"])
            return None
