from pathlib import Path


def cache_temporal(monkeypatch, cache):
    from adaptadores import extraccion

    monkeypatch.setattr(extraccion, "CACHE", Path(cache))
