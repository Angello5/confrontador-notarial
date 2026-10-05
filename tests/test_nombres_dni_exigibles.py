"""F16/F19 con datos ficticios: nombres sin tratamientos y solo se exige lo de las fichas."""

from nucleo.verificar import catalogo, nombres, revisar


def _reniec(documento, nombres_, paterno, materno):
    return (
        f"CUI: {documento} - 5\n"
        f"APELLIDO PATERNO  {paterno}  APELLIDO MATERNO  {materno}\n"
        f"NOMBRES  {nombres_}"
    )


def _de(campo, salidas):
    return [salida for salida in salidas if salida.startswith(f"[{campo}]")]


def test_nombre_sin_tratamiento_ni_forma_de_intervenir():
    for texto in (
        "SEÑORA ANA LUCIA PEREZ ROJAS, DE NACIONALIDAD PERUANA",
        "DOÑA ANA LUCIA PEREZ ROJAS, DE NACIONALIDAD PERUANA",
        "PROCEDE POR DERECHO PROPIO ANA LUCIA PEREZ ROJAS.- DE NACIONALIDAD PERUANA",
        "REPRESENTADA POR EL SEÑOR ANA LUCIA PEREZ ROJAS, DE NACIONALIDAD PERUANA",
    ):
        assert nombres(texto) == ["ANA LUCIA PEREZ ROJAS"], texto


def test_rotulo_nombre_de_un_cuadro_no_es_parte_del_nombre():
    fuentes = {
        "reniec-ficticio.pdf": _reniec("90000021", "ANA LUCIA", "PEREZ", "ROJAS")
    }
    borrador = (
        "ANA LUCIA PEREZ ROJAS, DE NACIONALIDAD PERUANA, CON DNI N° 90000021.\n"
        "NOMBRE ANA LUCIA PEREZ ROJAS\n"
    )
    assert _de("NOMBRE", revisar(catalogo(fuentes), borrador, 90)) == []


def test_nombre_cortado_no_se_exige_ni_duplica_observaciones():
    cat = {
        "NOMBRE": {"LUCIA ISABEL MORALES DE VERA", "ISABEL MORALES DE VERA"},
        "DNI": set(),
        "PARTIDA": set(),
        "MONTO": set(),
    }
    borrador = "LUCIA ISABEL MORALES DE VERA, DE NACIONALIDAD PERUANA."
    assert _de("NOMBRE", revisar(cat, borrador, 90)) == []
    errado = "LUCIA ISABEL MORALEZ DE VERA, DE NACIONALIDAD PERUANA."
    salidas = _de("NOMBRE", revisar(cat, errado, 90))
    assert (
        "[NOMBRE] «LUCIA ISABEL MORALEZ DE VERA» debe decir «LUCIA ISABEL MORALES DE VERA»"
        in salidas
    )
    assert not [s for s in salidas if "«ISABEL MORALES DE VERA»" in s]


def test_solo_se_exige_el_dni_de_las_fichas():
    fuentes = {
        "reniec-ficticio.pdf": _reniec("90000021", "ANA LUCIA", "PEREZ", "ROJAS"),
        "vigencia-ficticia.pdf": (
            "CARLOS MENDOZA RUIZ, IDENTIFICADO CON DNI N° 90000099, APODERADO."
        ),
    }
    minutas = {"minuta-ficticia.txt": "LA MINUTA NO REPITE LOS DOCUMENTOS."}
    con_dni = "ANA LUCIA PEREZ ROJAS, DE NACIONALIDAD PERUANA, CON DNI N° 90000021."
    assert _de("DNI", revisar(catalogo(fuentes), con_dni, 90, minutas=minutas)) == []
    sin_dni = "ANA LUCIA PEREZ ROJAS, DE NACIONALIDAD PERUANA."
    assert _de("DNI", revisar(catalogo(fuentes), sin_dni, 90, minutas=minutas)) == [
        "[DNI] FALTA: «90000021» esta en las fuentes y no aparece en el destino"
    ]
