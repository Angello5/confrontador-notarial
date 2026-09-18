from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "El usuario o la clave no son correctos.",
        "inactive": "El usuario o la clave no son correctos.",
    }


class InitialPasswordChangeForm(PasswordChangeForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.force_password_change = False
        if commit:
            user.save()
        return user
