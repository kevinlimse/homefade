"""Write homefade-fader.kicad_sch (net-label style) + homefade.kicad_sym from design.py."""
import os, sys, uuid, copy
import sexpdata
from sexpdata import Symbol as S
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D
import symlib

PROJ = sys.argv[1]
U = lambda: str(uuid.uuid4())
SYMDIR = "/usr/share/kicad/symbols"
F = '(effects (font (size 1.27 1.27)))'
FH = '(effects (font (size 1.27 1.27)) hide)'


def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


# ------------------------------------------------------------------ custom symbols
def box_symbol(name, left, right, ref="U", top=None, w=12.7):
    """left/right: list of (num, name, type) ; None = spacer."""
    n = max(len(left), len(right))
    h = (n + 1) * 2.54
    y0 = h / 2
    body = (f'(symbol {q(name + "_0_1")} (rectangle (start {-w/2} {y0}) (end {w/2} {-y0}) '
            f'(stroke (width 0.254) (type default)) (fill (type background))))')
    pins = []
    for side, lst in ((-1, left), (1, right)):
        for i, p in enumerate(lst):
            if p is None:
                continue
            num, pname, typ = p
            y = round(y0 - 2.54 * (i + 1), 2)
            x = side * (w / 2 + 2.54)
            ang = 0 if side < 0 else 180
            pins.append(f'(pin {typ} line (at {x} {y} {ang}) (length 2.54) (name {q(pname)} {F}) (number {q(num)} {F}))')
    return (f'(symbol {q(name)} (in_bom yes) (on_board yes)\n'
            f'  (property "Reference" {q(ref)} (at 0 {y0 + 1.5} 0) {F})\n'
            f'  (property "Value" {q(name)} (at 0 {-y0 - 1.5} 0) {F})\n'
            f'  (property "Footprint" "" (at 0 0 0) {FH})\n  (property "Datasheet" "" (at 0 0 0) {FH})\n'
            f'  {body}\n  (symbol {q(name + "_1_1")} ' + " ".join(pins) + "))")


ch224 = box_symbol("CH224A",
                   [("8", "VBUS", "input"), ("1", "VHV", "power_in"), None, ("7", "CC1", "bidirectional"),
                    ("6", "CC2", "bidirectional"), None, ("4", "DP", "bidirectional"), ("5", "DM", "bidirectional")],
                   [("9", "CFG1", "input"), ("2", "CFG2", "input"), ("3", "CFG3", "input"), None,
                    ("10", "PG", "open_collector"), None, None, ("11", "GND", "power_in")])
fader = box_symbol("RS60N11M9_Fader",
                   [("1", "POT_1", "passive"), ("2", "WIPER", "passive"), ("3", "POT_3", "passive"),
                    None, ("T", "TOUCH", "passive")],
                   [("MA", "MOTOR_A", "passive"), ("MB", "MOTOR_B", "passive"), None,
                    ("L1", "FRAME", "passive"), ("L2", "FRAME", "passive")], ref="FD", w=15.24)
names = {1: "GND", 2: "GND", 3: "3V3", 4: "IO0/BOOT", 45: "EN", 42: "GND", 43: "GND"}
for i, g in enumerate([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]):
    names[4 + i] = f"IO{g}" if g else "IO0/BOOT"
names.update({26: "IO26", 27: "IO47", 28: "IO33", 29: "IO34", 30: "IO48", 31: "IO35", 32: "IO36",
              33: "IO37", 34: "IO38", 35: "IO39", 36: "IO40", 37: "IO41", 38: "IO42", 39: "TXD0",
              40: "RXD0", 41: "IO45", 44: "IO46"})
for n in range(46, 66):
    names[n] = "GND"
left = [(str(n), names[n], "power_in" if names[n] in ("GND", "3V3") else "bidirectional") for n in range(1, 34)]
right = [(str(n), names[n], "power_in" if names[n] in ("GND", "3V3") else "bidirectional") for n in range(34, 66)]
left = [(a, b, "input" if b == "EN" else t) for a, b, t in left]
right = [(a, b, "input" if b == "EN" else t) for a, b, t in right]
esp = box_symbol("ESP32-S3-MINI-1", left, right, w=17.78)
sk = box_symbol("SK6812SIDE-A", [("1", "DIN", "input"), ("2", "VDD", "power_in")],
                [("3", "DOUT", "output"), ("4", "GND", "power_in")], ref="D", w=10.16)
CUSTOM = {"CH224A": ch224, "RS60N11M9_Fader": fader, "ESP32-S3-MINI-1": esp, "SK6812SIDE-A": sk}

with open(os.path.join(PROJ, "homefade.kicad_sym"), "w") as f:
    f.write("(kicad_symbol_lib (version 20220914) (generator homefade_gen)\n")
    for s in CUSTOM.values():
        f.write("  " + s + "\n")
    f.write(")\n")


# ------------------------------------------------------------------ lib symbol cache
def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib == D.LIB:
        s = sexpdata.loads(CUSTOM[name])
    else:
        t = symlib.load(os.path.join(SYMDIR, lib + ".kicad_sym"))
        s = copy.deepcopy(symlib.find_sym(t, name))
        ext = [e for e in s if isinstance(e, list) and e[0] == S("extends")]
        if ext:  # flatten
            parent = copy.deepcopy(symlib.find_sym(t, ext[0][1]))
            pname = ext[0][1]
            props = {e[1]: e for e in s if isinstance(e, list) and e[0] == S("property")}
            out = [S("symbol"), name]
            for e in parent[2:]:
                if isinstance(e, list) and e[0] == S("property") and e[1] in props:
                    out.append(props[e[1]])
                elif isinstance(e, list) and e[0] == S("symbol"):
                    e[1] = e[1].replace(pname, name, 1); out.append(e)
                else:
                    out.append(e)
            s = out
    s[1] = lib_id
    return s


def pin_list(lib_id):
    s = lib_symbol(lib_id)
    return symlib.pins(s)


lib_syms = {}
for c in D.C:
    if c["lib_id"] not in lib_syms:
        lib_syms[c["lib_id"]] = lib_symbol(c["lib_id"])

# ------------------------------------------------------------------ placement on sheet
GROUP_TITLES = {"power": "USB-C input, USB-PD trigger (9 V), ESD", "buck": "3.3 V buck",
                "motor": "Motor driver (TB6612FNG)",
                "fader": "Fader: pot, touch, motor", "mcu": "ESP32-S3 + boot/reset, LED, sense",
                "ledbar": "Position LED bar (10x SK6812SIDE-A, 4.5 V)"}
items = []
ROOT = U()
col_x = {"power": 30, "buck": 120, "motor": 200, "fader": 290, "mcu": 380, "ledbar": 480}
cur_y = {g: 45 for g in col_x}
G = lambda v: round(round(v / 2.54) * 2.54, 2)


def bbox(lib_id):
    ps = pin_list(lib_id)
    ys = [p[3] for p in ps] or [0]
    return min(ys), max(ys)


for g, x in col_x.items():
    items.append(f'(text {q(GROUP_TITLES[g])} (at {x - 10} 32 0) (effects (font (size 2.5 2.5) bold) (justify left)) (uuid {U()}))')

notes = []
for c in D.C:
    g = c["group"]
    lo, hi = bbox(c["lib_id"])
    big = c["lib_id"].startswith(D.LIB + ":ESP")
    x = G(col_x[g] + (25 if big else 20))
    y = G(cur_y[g] + hi + 6)
    cur_y[g] = y - lo + 10
    c["_sch"] = (x, y)
    lcsc = c["lcsc"]
    props = [("Reference", c["ref"], (x + 5, y - hi - 3), False), ("Value", c["value"], (x + 5, y - lo + 3), False),
             ("Footprint", c["fp"] or "", (x, y), True), ("Datasheet", "", (x, y), True),
             ("LCSC", lcsc, (x, y), True)]
    if c["note"]:
        props.append(("Note", c["note"], (x, y), True))
        notes.append((x - 18, y - lo + 6, c["note"]))
    pr = "\n".join(f'  (property {q(k)} {q(v)} (at {px} {py} 0) {FH if hid else F})' for k, v, (px, py), hid in props)
    pins = pin_list(c["lib_id"])
    pinuu = " ".join(f'(pin {q(p[0])} (uuid {U()}))' for p in pins)
    dnp = "yes" if c["dnp"] else "no"
    inbom = "no" if c["ref"].startswith("#FLG") or c["dnp"] else "yes"
    items.append(f'(symbol (lib_id {q(c["lib_id"])}) (at {x} {y} 0) (unit 1) (in_bom {inbom}) (on_board {"no" if c["ref"].startswith("#FLG") else "yes"}) (dnp {dnp}) (uuid {U()})\n{pr}\n  {pinuu}\n'
                 f'  (instances (project "homefade-fader" (path "/{ROOT}" (reference {q(c["ref"])}) (unit 1)))))')
    seen = set()
    for num, name, px, py, ang, ln, typ in pins:
        ex, ey = round(x + px, 2), round(y - py, 2)
        if (ex, ey) in seen:
            continue  # stacked pins share a point
        seen.add((ex, ey))
        nn = c["pins"].get(num)
        if nn is None:
            items.append(f'(no_connect (at {ex} {ey}) (uuid {U()}))')
            continue
        lang = {0: 180, 180: 0, 90: 270, 270: 90}[int(ang)]
        just = "right" if lang == 180 else "left"
        if lang in (90, 270):
            just = "left" if lang == 90 else "right"
        items.append(f'(label {q(nn)} (at {ex} {ey} {lang}) (fields_autoplaced) (effects (font (size 1.0 1.0)) (justify {just} bottom)) (uuid {U()}))')

for x, y, t in notes:
    items.append(f'(text {q("Note: " + t)} (at {x} {y} 0) (effects (font (size 1.0 1.0) italic) (justify left)) (uuid {U()}))')

items.append(f'(text {q("homefade fader controller v1.1 - one board per Alps RS60N11M9A0F fader. Generated from design.py; net labels carry connectivity.")} (at 20 20 0) (effects (font (size 3 3) bold) (justify left)) (uuid {U()}))')

libtxt = "\n".join("    " + sexpdata.dumps(s) for s in lib_syms.values())
sch = (f'(kicad_sch (version 20230121) (generator eeschema)\n  (uuid {ROOT})\n  (paper "A2")\n'
       f'  (title_block (title "homefade fader controller") (rev "1.1") (company "homefade"))\n'
       f'  (lib_symbols\n{libtxt}\n  )\n' + "\n".join("  " + i for i in items) +
       f'\n  (sheet_instances (path "/" (page "1")))\n)\n')
open(os.path.join(PROJ, "homefade-fader.kicad_sch"), "w").write(sch)

# tables + project file
open(os.path.join(PROJ, "sym-lib-table"), "w").write(
    '(sym_lib_table\n  (lib (name "homefade")(type "KiCad")(uri "${KIPRJMOD}/homefade.kicad_sym")(options "")(descr "project symbols"))\n)\n')
open(os.path.join(PROJ, "fp-lib-table"), "w").write(
    '(fp_lib_table\n  (lib (name "homefade")(type "KiCad")(uri "${KIPRJMOD}/homefade.pretty")(options "")(descr "project footprints"))\n)\n')
print("schematic ok", len(D.C), "symbols")
