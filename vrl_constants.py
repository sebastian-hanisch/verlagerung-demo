"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 1, 3, 3             # Personen
M_MIN, M_MAX, DEFAULT_M = 3, 7, 7             # Aufgaben; alle (2n)^m Pläne werden aufgezählt (bis 6^7 = 279 936)
SEED_MAX, DEFAULT_SEED = 999999, 100009
FAMILIES = ("Kosten unabhängig 1 bis 99", "Personeneffekt")
DEFAULT_FAMILY = 0

FR_MIN, FR_MAX, FR_STEP, DEFAULT_FR = 60, 120, 10, 80          # Regelkapazität: aufgerundet fR * (Summe der mittleren Zeiten) / n, fR in Prozent
FZ_MIN, FZ_MAX, FZ_STEP, DEFAULT_FZ = 0, 100, 25, 50           # Überstundenkapazität: aufgerundet fZ * Regelkapazität, fZ in Prozent
G_MIN, G_MAX, G_STEP, DEFAULT_G = 100, 200, 25, 125            # Zuschlag der Überstunden in Prozent (100: eine Überstunde kostet so viel wie eine Regelstunde)
DELTA_MIN, DELTA_MAX, DELTA_STEP, DEFAULT_DELTA = 0, 20, 5, 10  # alle Zeiten wachsen um delta Prozent (Sprödheit) beziehungsweise Reserve in Prozent
OBJECTIVES = ("kpi", "true")
OBJECTIVE_NAMES = {"kpi": "Kennzahl (nur Regelzeit)", "true": "wahre Kosten (mit Überstunden)"}
DEFAULT_OBJECTIVE = 0

SWEEP_SEEDS = tuple(range(100000, 100020))    # feste Instanzen für alle Sweeps: nie ein einzelner Seed als Befund
SWEEP_N, SWEEP_M = 3, 7                       # Größe der Sweeps (alle 279 936 Pläne)
SWEEP_FAMILIES = (0, 1)
SWEEP_GS = (100, 125, 150, 200)
SWEEP_FZS = (0, 25, 50, 100)
SWEEP_DELTAS = (2, 5, 10, 20)                 # Sprödheit in Prozent
SWEEP_RESERVES = (5, 10, 20)
SWEEP_G = 125                                 # Zuschlag der Rand-, Zahler- und Reserve-Messungen
SWEEP_FR, SWEEP_FZ = 80, 50

COLOR_ALL = "rgba(150,150,150,0.35)"
COLOR_KPI = "#d8a13a"
COLOR_TRUE = "#2F6B65"
COLOR_BAD = "#c0504d"
COLOR_REAL = "#4c78a8"

PRESETS = {
    "Die Kennzahl sieht besser aus": {"n": 3, "m": 7, "family": 0, "seed": 100009, "fr": 80, "fz": 50, "g": 125, "delta": 10, "objective": 0},
    "Ohne Zuschlag: nur Verschiebung": {"n": 3, "m": 7, "family": 0, "seed": 100040, "fr": 80, "fz": 50, "g": 100, "delta": 10, "objective": 0},
    "Wo es keinen Ort gibt, wandert nichts": {"n": 3, "m": 7, "family": 0, "seed": 100100, "fr": 80, "fz": 0, "g": 125, "delta": 10, "objective": 0},
    "Ein großer Ort für die Last": {"n": 3, "m": 7, "family": 0, "seed": 100110, "fr": 80, "fz": 100, "g": 125, "delta": 10, "objective": 0},
    "Alle Personen zahlen": {"n": 3, "m": 7, "family": 1, "seed": 100133, "fr": 80, "fz": 50, "g": 125, "delta": 10, "objective": 0},
    "Der Rand: 5 % mehr Zeit kippt den Plan": {"n": 3, "m": 7, "family": 0, "seed": 100189, "fr": 80, "fz": 50, "g": 125, "delta": 5, "objective": 0},
    "Die Reserve kostet": {"n": 3, "m": 7, "family": 0, "seed": 100318, "fr": 80, "fz": 50, "g": 125, "delta": 20, "objective": 0},
    "Kleinstes Beispiel (1 Person, 3 Aufgaben)": {"n": 1, "m": 3, "family": 0, "seed": 3, "fr": 80, "fz": 50, "g": 125, "delta": 10, "objective": 0},
}
PRESET_HELP = {
    "Die Kennzahl sieht besser aus": "Das Optimum der Kennzahl hat KPI 23 statt 193 (88,1 % weniger als 193), kostet aber wirklich 354,25 statt 210,5 (68,3 % mehr als 210,5); 5 von 7 Aufgaben liegen in Überstunden.",
    "Ohne Zuschlag: nur Verschiebung": "Auch ohne Zuschlag (eine Überstunde kostet wie eine Regelstunde) sinkt die Kennzahl von 55 auf 4 (92,7 % weniger als 55), die wahren Kosten steigen von 139 auf 224 (61,2 % mehr als 139).",
    "Wo es keinen Ort gibt, wandert nichts": "Ohne Überstundenkapazität wandert nichts: beide Optima sind gleich (KPI 222, keine Aufgabe in Überstunden).",
    "Ein großer Ort für die Last": "Bei großer Überstundenkapazität geht fast alles in die unsichtbaren Stunden: KPI 0 statt 96, wahre Kosten 457,5 statt 103,5 (342 % mehr).",
    "Alle Personen zahlen": "Die Überstunden verteilen sich gleich auf alle drei Personen (je 4 Stunden); 92 % der wahren Kosten des Kennzahl-Optimums stecken in ihnen.",
    "Der Rand: 5 % mehr Zeit kippt den Plan": "Bei 5 % mehr Zeit ist das Optimum der Kennzahl unzulässig (zwei Überstundengrenzen sind genau ausgeschöpft), das wahre Optimum noch zulässig.",
    "Die Reserve kostet": "Eine Reserve von 5 oder 10 % kostet hier nichts, eine von 20 % kostet 65,7 % mehr.",
    "Kleinstes Beispiel (1 Person, 3 Aufgaben)": "Acht Pläne, drei zulässig: das Optimum der Kennzahl hat KPI 18 statt 99, kostet aber 130,5 statt 110,25 (18,4 % mehr).",
}
