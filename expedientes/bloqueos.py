"""Exclusión entre workers; PostgreSQL libera el lock si muere la conexión."""

import hashlib
from contextlib import contextmanager

from django.db import connection


@contextmanager
def exclusivo(tipo, identidad):
    clave = int.from_bytes(
        hashlib.sha256(f"notaria:{tipo}:{identidad}".encode()).digest()[:8],
        "big",
        signed=True,
    )
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [clave])
        adquirido = cursor.fetchone()[0]
    try:
        yield adquirido
    finally:
        if adquirido:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [clave])
