"""Check minimo: el borrador malo debe salir observado y el resultado limpio.

  Datos ficticios generados por scripts/generar_fixtures.py.

  python -m pytest test_verificar.py
"""
from pathlib import Path

from extraer import recolectar
from verificar import catalogo, revisar

BASE = Path(__file__).parent / "tests" / "fixtures"

def test_verificacion():
    fuentes = recolectar([str(BASE / "cliente")])
    cat = catalogo(fuentes)
    assert cat["DNI"] == {"90000001", "90000002", "90000003", "90000004"}, cat["DNI"]
    assert cat["PARTIDA"] == {"80000001"}, cat["PARTIDA"]
    assert len(cat["NOMBRE"]) == 4, cat["NOMBRE"]  # sin basura del sello de agua

    def obs(p):
        return revisar(cat, next(iter(recolectar([str(p)]).values())), 88)

    malo = obs(BASE / "borrador" / "observado.docx")
    bueno = obs(BASE / "resultado" / "correcto.docx")
    assert len(malo) >= 6, malo
    assert bueno == [], bueno  # sin falsos positivos
    # el borrador correcto SI corresponde a sus fuentes; una plantilla ajena no
    from verificar import diagnostico
    from extraer import leer
    borrador = next(iter(recolectar([str(BASE / "borrador")]).values()))
    assert diagnostico(fuentes, borrador) is None, diagnostico(fuentes, borrador)
    ajeno = leer(BASE / "ajeno" / "plantilla.docx")
    assert "no corresponde" in (diagnostico(fuentes, ajeno) or ""), diagnostico(fuentes, ajeno)
    # una plantilla ajena MEZCLADA entre las fuentes no debe hundir a la minuta
    assert diagnostico(fuentes | {"plantilla.docx": ajeno}, borrador) is None

    print(f"OK — borrador: {len(malo)} observaciones, resultado: 0, plantilla ajena bloqueada")
