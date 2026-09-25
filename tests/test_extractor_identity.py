"""Caracterización sintética de la identidad del extractor de F4."""


def test_cambiar_hash_de_modelo_cambia_identidad(monkeypatch):
    from adaptadores import extraccion

    primera = extraccion.version_extractor()
    modelos = dict(extraccion._OCR_FILES)
    nombre = next(iter(modelos))
    modelos[nombre] = "0" * 64
    monkeypatch.setattr(extraccion, "_OCR_FILES", modelos)

    assert extraccion.version_extractor() != primera


def test_cambiar_detector_cambia_identidad(monkeypatch):
    from adaptadores import extraccion

    anterior = extraccion.version_extractor()
    modelos = dict(extraccion._OCR_FILES)
    assert modelos["ch_PP-OCRv5_mobile_det.onnx"] == (
        "4d97c44a20d30a81aad087d6a396b08f786c4635742afc391f6621f5c6ae78ae"
    )
    modelos["detector-ficticio.onnx"] = modelos.pop("ch_PP-OCRv5_mobile_det.onnx")
    monkeypatch.setattr(extraccion, "_OCR_FILES", modelos)

    assert extraccion.version_extractor() != anterior


def test_cambiar_use_cls_cambia_identidad(monkeypatch):
    from adaptadores import extraccion

    primera = extraccion.version_extractor()
    monkeypatch.setattr(extraccion, "_OCR_USE_CLS", not extraccion._OCR_USE_CLS)

    assert extraccion.version_extractor() != primera
