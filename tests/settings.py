"""Django settings for tests only."""

import os
import tempfile

os.environ["DJANGO_SECRET_KEY"] = "test-only-" + "not-for-deployment"
# F28: los tests prueban el nombre por defecto, nunca el del servidor.
os.environ.pop("ERP_NOMBRE", None)
# Nunca la carpeta real: las pruebas borran originales de kardex con los mismos números.
os.environ["EXPEDIENTES_ORIGINALES_DIR"] = tempfile.mkdtemp(prefix="originales-prueba-")
os.environ["EXPEDIENTES_TEMP_DIR"] = tempfile.mkdtemp(prefix="temporales-prueba-")

from config.settings import *  # noqa: F403
