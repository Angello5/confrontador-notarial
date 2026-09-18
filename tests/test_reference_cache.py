def test_cache_medicion_local_usa_directorio_temporal(monkeypatch, tmp_path):
    from adaptadores import extraccion
    from reference_cache import cache_temporal

    cache = tmp_path / "cache"
    cache_temporal(monkeypatch, cache)
    assert extraccion.CACHE == cache
    assert (
        extraccion._cacheado(b"documento ficticio", lambda: "TEXTO FICTICIO")
        == "TEXTO FICTICIO"
    )
    assert len(list(cache.glob("*.json"))) == 1
