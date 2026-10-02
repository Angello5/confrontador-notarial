"""Vista previa y configuración de marca, con datos exclusivamente ficticios."""

from django.test import RequestFactory, override_settings


def test_zonas_de_carga_tienen_identificadores_distintos():
    from expedientes.forms import DocumentoUploadForm

    formularios = [
        DocumentoUploadForm(expected_role=rol)
        for rol in ("CLIENTE", "MINUTA", "BORRADOR")
    ]
    ids = [form["archivos"].id_for_label for form in formularios]
    assert len(set(ids)) == 3
    assert all(form["archivos"].html_name == "archivos" for form in formularios)


def test_fragmento_incluye_error_al_final_de_un_parrafo_largo():
    from expedientes.services import ubicar_valor

    texto = "Cláusula ficticia sin datos. " * 20 + "DNI 90000002. Cierre."
    ubicacion = ubicar_valor(texto, "90000002")
    assert ubicacion["linea"] == 1
    assert "90000002" in ubicacion["fragmento"]
    assert len(ubicacion["fragmento"]) <= 160
    assert ubicacion["fragmento"][ubicacion["inicio"] : ubicacion["fin"]] == "90000002"


def test_ubicacion_no_confunde_un_numero_con_otro_mas_largo():
    from expedientes.services import ubicar_valor

    ubicacion = ubicar_valor("190000002\nDNI 90000002", "90000002")
    assert ubicacion["linea"] == 2


def test_resaltado_conserva_tildes_y_espacios_del_documento():
    from expedientes.services import ubicar_valor

    ubicacion = ubicar_valor("La cláusula   útil de prueba.", "CLAUSULA UTIL")
    assert (
        ubicacion["fragmento"][ubicacion["inicio"] : ubicacion["fin"]].strip()
        == "cláusula   útil"
    )


@override_settings(
    ERP_NOMBRE="Notaría Ficticia",
    ERP_LOGO="/static/marca/logo.png",
    ERP_DIRECCION="Sede ficticia",
)
def test_contexto_expone_logo_y_direccion_configurados():
    from core.context_processors import marca

    contexto = marca(RequestFactory().get("/"))
    assert contexto["erp_logo"] == "/static/marca/logo.png"
    assert contexto["erp_direccion"] == "Sede ficticia"
    assert contexto["erp_iniciales"] == "NF"
