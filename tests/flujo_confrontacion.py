"""Recorrido HTTP → worker → resultado, con datos ficticios de los tests."""


def confrontar_y_ver(client, ruta):
    from expedientes.services import confrontar_automaticamente

    respuesta = client.post(ruta)
    assert respuesta.status_code == 302
    confrontar_automaticamente()
    return client.get(ruta.replace("/confrontar/", "/resultado/"))
