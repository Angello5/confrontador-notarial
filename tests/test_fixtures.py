"""Los fixtures se regeneran sin depender de documentos ni del reloj."""

from hashlib import sha256

from scripts.generar_fixtures import generar


def test_generacion_reproducible(tmp_path):
    generar(tmp_path)
    antes = {
        p.relative_to(tmp_path): sha256(p.read_bytes()).hexdigest()
        for p in tmp_path.rglob("*")
        if p.is_file()
    }
    generar(tmp_path)
    despues = {
        p.relative_to(tmp_path): sha256(p.read_bytes()).hexdigest()
        for p in tmp_path.rglob("*")
        if p.is_file()
    }
    assert len(antes) == 11
    assert antes == despues
