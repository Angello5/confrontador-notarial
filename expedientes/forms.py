from django import forms

from adaptadores import extraccion

from .models import Documento, Expediente
from .services import validar_archivo


class ExpedienteForm(forms.ModelForm):
    codigo = forms.CharField(
        max_length=100, error_messages={"required": "Ingrese el código del expediente."}
    )

    class Meta:
        model = Expediente
        fields = ("codigo",)
        labels = {"codigo": "Código del expediente"}
        help_texts = {"codigo": "Escriba el código que identifica este expediente."}

    def clean_codigo(self):
        codigo = self.cleaned_data["codigo"].strip()
        if not codigo:
            raise forms.ValidationError("Ingrese el código del expediente.")
        if (
            Expediente.objects.filter(codigo=codigo)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(
                "Ese código ya está registrado. Ingrese otro código."
            )
        return codigo


class DocumentoUploadForm(forms.Form):
    rol = forms.ChoiceField(
        choices=Documento.ROLES,
        label="Rol del documento",
        help_text="La minuta y los documentos del cliente son fuentes; el proyecto es el borrador.",
        error_messages={
            "required": "Seleccione el rol del documento.",
            "invalid_choice": "Seleccione un rol válido.",
        },
    )
    archivo = forms.FileField(
        label="Archivo",
        help_text="Formatos admitidos y tamaño máximo indicados abajo.",
        error_messages={
            "required": "Seleccione un archivo.",
            "empty": "El archivo está vacío.",
        },
    )

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        try:
            validar_archivo(archivo)
        except (OSError, ValueError) as exc:
            detalle = str(exc)
            if "vacío" in detalle:
                mensaje = "El archivo está vacío."
            elif "tamaño" in detalle:
                mensaje = "El archivo supera el tamaño máximo permitido."
            elif "formato" in detalle:
                mensaje = "El formato de archivo no está admitido."
            else:
                mensaje = "Revise el formato, el contenido y el tamaño del archivo."
            raise forms.ValidationError(mensaje)
        return archivo


def formatos_admitidos():
    return ", ".join(
        sorted(extension.upper().lstrip(".") for extension in extraccion.DOCS)
    )
