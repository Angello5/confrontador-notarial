from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "El usuario o la clave no son correctos.",
        "inactive": "El usuario o la clave no son correctos.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].label = "Clave"
        self.fields[
            "password"
        ].help_text = "Si olvidó su clave, pida al Administrador una clave temporal."


class InitialPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "Clave actual (temporal)"
        self.fields["new_password1"].label = "Clave nueva"
        self.fields["new_password2"].label = "Confirmar clave nueva"

    def save(self, commit=True):
        self.user.force_password_change = False
        return super().save(commit)
