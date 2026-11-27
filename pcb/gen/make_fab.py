"""BOM (JLC format + readable), CPL, renders."""
import os, sys, csv, collections
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D

PROJ = sys.argv[1]
OUT = os.path.join(PROJ, "fab")
os.makedirs(OUT, exist_ok=True)
PRICE = {'C116592': .0365, 'C11702': .0006, 'C1525': .0016, 'C165948': .0975, 'C167219': .0827, 'C2286': .0036,
         'C25076': .0006, 'C25741': .0005, 'C25744': .0005, 'C25779': .001, 'C25917': .0006, 'C2913206': 3.1756,
         'C318884': .0102, 'C45783': .053, 'C59461': .0077, 'C7519': .0747, 'C83063': .0075, 'C88224': .6706,
         'C96446': .0174, 'C42459160': .445,
         'C5378721': .07, 'C167826': .06}  # last two: approximate (LCSC low-qty tier not read)

groups = collections.OrderedDict()
for c in D.C:
    if not c["fp"] or c["dnp"] or not c["lcsc"]:
        continue
    k = (c["value"], c["fp"].split(":")[1], c["lcsc"])
    groups.setdefault(k, []).append(c["ref"])

with open(os.path.join(OUT, "BOM-JLCPCB.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for (val, fp, lcsc), refs in groups.items():
        w.writerow([val, ",".join(refs), fp, lcsc])

total = 0
lines = ["| Qty | Refs | Value | Footprint | LCSC | Unit $ (1+) |", "|---|---|---|---|---|---|"]
for (val, fp, lcsc), refs in groups.items():
    p = PRICE.get(lcsc, 0)
    total += p * len(refs)
    lines.append(f"| {len(refs)} | {', '.join(refs)} | {val} | {fp} | [{lcsc}](https://www.lcsc.com/product-detail/{lcsc}.html) | {p:.4f} |")
lines.append(f"\n**Parts per board (LCSC 1+ pricing, Nov 2026): ~US${total:.2f}**, plus the fader itself.")
hand = [c for c in D.C if c["fp"] and (c["dnp"] or not c["lcsc"])]
lines.append("\nNot assembled by JLC (you solder): " + "; ".join(f"{c['ref']} {c['value']}" for c in hand))
open(os.path.join(OUT, "BOM.md"), "w").write("\n".join(lines) + "\n")

# CPL
b = pcbnew.LoadBoard(os.path.join(PROJ, "homefade-fader.kicad_pcb"))
ox, oy = 50 + D.BOARD_X0, 100 + D.BOARD_HW  # bottom-left corner of the board
with open(os.path.join(OUT, "CPL-JLCPCB.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    byref = {c["ref"]: c for c in D.C}
    for fp in sorted(b.GetFootprints(), key=lambda x: x.GetReference()):
        c = byref.get(fp.GetReference())
        if not c or c["dnp"] or not c["lcsc"]:
            continue
        p = fp.GetPosition()
        x = pcbnew.ToMM(p.x) - ox
        y = oy - pcbnew.ToMM(p.y)
        w.writerow([fp.GetReference(), f"{x:.3f}mm", f"{y:.3f}mm", "Top", f"{fp.GetOrientationDegrees() % 360:.0f}"])
print("BOM groups", len(groups), "parts/board $%.2f" % total)
