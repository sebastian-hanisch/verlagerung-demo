"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import vrl_constants as C
from vrl_evaluation import Analysis, compare, pct, vtext

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "„": '"', "“": '"', "²": "2", "∞": "unendlich"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: Analysis) -> bytes:
    s = a.settings
    c = compare(a)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Verlagerung und Randlösungen"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _s(f"{s.n} Personen, {s.m} Aufgaben, Familie: {C.FAMILIES[s.family]}, Seed {s.seed}; Regelkapazität {a.p.inst.cap_r} h, Überstunden {a.p.inst.cap_z} h, Zuschlag {s.g} %. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    if c["kpi_opt"] is None:
        pdf.multi_cell(0, 5, _s("Mit diesen Kapazitäten ist kein Plan zulässig."), new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())
    k, t = c["kpi_opt"], c["true_opt"]
    pdf.multi_cell(0, 5, _s(f"Optimum der Kennzahl: KPI {k['kpi']}, wahre Kosten {vtext(k['true'])}, {k['nz']} Aufgaben in Überstunden ({k['zhours']} h)."), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5, _s(f"Wahres Optimum: KPI {t['kpi']}, wahre Kosten {vtext(t['true'])}, {t['nz']} Aufgaben in Überstunden ({t['zhours']} h)."), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5, _s(f"Die Kennzahl sieht {pct(c['gain'])} besser aus; die wahren Kosten sind {pct(c['loss'])} höher."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Bei Gleichstand gilt der kleinste Index der Aufzählung. Quelle: verlagerung-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
