"""Check minimo: el borrador malo debe salir observado y el resultado limpio.

  python3 test_verificar.py
"""
from pathlib import Path

from extraer import recolectar
from verificar import catalogo, revisar

BASE = Path(__file__).parent

if __name__ == "__main__":
    fuentes = recolectar([str(BASE / "Cliente")])
    cat = catalogo(fuentes)
    assert cat["DNI"] == {"25427742", "25470260", "25849272", "40324003"}, cat["DNI"]
    assert cat["PARTIDA"] == {"70703688"}, cat["PARTIDA"]
    assert len(cat["NOMBRE"]) == 4, cat["NOMBRE"]  # sin basura del sello de agua

    def obs(p):
        return revisar(cat, next(iter(recolectar([str(p)]).values())), 88)

    malo = obs(BASE / "Proyecto(borrador)" / "1785794688639_71168_malo2.docx")
    bueno = obs(BASE / "Resultado" / "72156.docx")
    assert len(malo) >= 6, malo
    assert bueno == [], bueno  # sin falsos positivos
    # el borrador correcto SI corresponde a sus fuentes; una plantilla ajena no
    from verificar import diagnostico
    from extraer import leer
    borrador = next(iter(recolectar([str(BASE / "Proyecto(borrador)")]).values()))
    assert diagnostico(fuentes, borrador) is None, diagnostico(fuentes, borrador)
    ajeno = leer(BASE / "mutuo-71213" / "Plantilla" / "MUTUO IMAGEN.doc")
    assert "no corresponde" in (diagnostico(fuentes, ajeno) or ""), diagnostico(fuentes, ajeno)
    # una plantilla ajena MEZCLADA entre las fuentes no debe hundir a la minuta
    assert diagnostico(fuentes | {"plantilla.doc": ajeno}, borrador) is None

    print(f"OK — borrador: {len(malo)} observaciones, resultado: 0, plantilla ajena bloqueada")
