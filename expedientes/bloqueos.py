"""Exclusión entre workers; SQL Server libera el lock si muere la conexión."""

import hashlib
from contextlib import contextmanager

from django.db import connection


@contextmanager
def exclusivo(tipo, identidad):
    recurso = (
        "notaria:"
        + hashlib.sha256(f"notaria:{tipo}:{identidad}".encode()).hexdigest()[:16]
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "SET NOCOUNT ON; DECLARE @r int; EXEC @r = sp_getapplock "
            "@Resource = %s, @LockMode = 'Exclusive', @LockOwner = 'Session', "
            "@LockTimeout = 0; SELECT @r",
            [recurso],
        )
        adquirido = cursor.fetchone()[0] >= 0
    try:
        yield adquirido
    finally:
        if adquirido:
            with connection.cursor() as cursor:
                cursor.execute(
                    "EXEC sp_releaseapplock @Resource = %s, @LockOwner = 'Session'",
                    [recurso],
                )
