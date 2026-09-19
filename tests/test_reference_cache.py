def test_cache_medicion_local_usa_directorio_temporal(monkeypatch, tmp_path):
    from adaptadores import extraccion
    from tests.reference_cache import cache_temporal

    cache = tmp_path / "cache"
    cache_temporal(monkeypatch, cache)
    assert extraccion.CACHE == cache
    assert (
        extraccion._cacheado(b"documento ficticio", lambda: "TEXTO FICTICIO")
        == "TEXTO FICTICIO"
    )
    assert len(list(cache.glob("*.json"))) == 1


def test_cache_ocr_recalcula_al_cambiar_use_cls(monkeypatch, tmp_path):
    from adaptadores import extraccion
    from tests.reference_cache import cache_temporal

    cache_temporal(monkeypatch, tmp_path)
    llamadas = []

    def calcular():
        llamadas.append(True)
        return len(llamadas)

    assert extraccion._cacheado(b"documento ficticio", calcular) == 1
    monkeypatch.setattr(extraccion, "_OCR_USE_CLS", True)
    assert extraccion._cacheado(b"documento ficticio", calcular) == 2
    assert len(llamadas) == 2
