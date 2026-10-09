from pathlib import Path

from django import forms

from adaptadores import extraccion

from .models import Documento, Expediente
from .services import validar_archivo


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if not data:
            if self.required:
                raise forms.ValidationError(self.error_messages["required"])
            return []
        return data if isinstance(data, list) else [data]


CODIGO_OCUPADO = "Ya existe un kardex activo con ese número. Ingrese otro número."


class ExpedienteForm(forms.ModelForm):
    codigo = forms.CharField(
        max_length=100, error_messages={"required": "Ingrese el número de kardex."}
    )

    class Meta:
        model = Expediente
        fields = ("codigo",)
        labels = {"codigo": "Número de kardex"}
        help_texts = {"codigo": "Escriba el número de kardex."}

    def clean_codigo(self):
        codigo = self.cleaned_data["codigo"].strip()
        if not codigo:
            raise forms.ValidationError("Ingrese el número de kardex.")
        if (
            Expediente.objects.filter(
                codigo=codigo, tipo=self.instance.tipo, archivado_el__isnull=True
            )
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(CODIGO_OCUPADO)
        return codigo


class DocumentoUploadForm(forms.Form):
    rol = forms.ChoiceField(
        choices=Documento.ROLES,
        label="Rol del documento",
        help_text="Indica la zona del kardex donde se registrarán los archivos.",
        error_messages={
            "required": "Seleccione el rol del documento.",
            "invalid_choice": "Seleccione un rol válido.",
        },
    )
    archivos = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={"multiple": True}),
        label="Archivos",
        help_text="Puede seleccionar varios archivos.",
        error_messages={
            "required": "Seleccione un archivo.",
            "empty": "El archivo está vacío.",
        },
    )

    def __init__(self, *args, expected_role=None, roles=Documento.ROLES, **kwargs):
        if expected_role in dict(Documento.ROLES):
            kwargs.setdefault("auto_id", f"id_{expected_role.lower()}_%s")
        super().__init__(*args, **kwargs)
        # F43: el kardex vehicular no acepta minuta.
        self.fields["rol"].choices = roles
        self.expected_role = expected_role
        self.errores_archivos = []
        if expected_role in dict(Documento.ROLES):
            self.fields["rol"].initial = expected_role
            self.fields["rol"].widget = forms.HiddenInput()

    def clean_rol(self):
        rol = self.cleaned_data["rol"]
        if self.expected_role is not None and rol != self.expected_role:
            raise forms.ValidationError(
                "El rol del archivo no es válido para esta zona."
            )
        return rol

    def clean_archivos(self):
        archivos = self.files.getlist(self.add_prefix("archivos"))
        if not archivos:
            raise forms.ValidationError("Seleccione un archivo.")
        validos = []
        for archivo in archivos:
            try:
                validar_archivo(archivo)
            except (OSError, ValueError) as exc:
                self.errores_archivos.append((Path(archivo.name).name, str(exc)))
            else:
                validos.append(archivo)
        if not validos:
            raise forms.ValidationError("Ningún archivo pudo registrarse.")
        return validos


def formatos_admitidos():
    return ", ".join(
        sorted(extension.upper().lstrip(".") for extension in extraccion.DOCS)
    )
