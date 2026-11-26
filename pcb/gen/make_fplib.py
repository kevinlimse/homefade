"""Write the project footprint library homefade.pretty."""
import os, shutil, sys

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))

# ESP32-S3-MINI-1: official Espressif footprint
shutil.copy(os.path.join(HERE, "..", "lib", "ESP32-S3-MINI-1.kicad_mod"), OUT)

# FXL0630 inductor: Chilisin 0630 land pattern, renamed
src = open("/usr/share/kicad/footprints/Inductor_SMD.pretty/L_Chilisin_BMRx00060630.kicad_mod").read()
src = src.replace('"L_Chilisin_BMRx00060630"', '"L_FXL0630"', 1).replace(
    "(footprint L_Chilisin_BMRx00060630", "(footprint \"L_FXL0630\"", 1)
open(os.path.join(OUT, "L_FXL0630.kicad_mod"), "w").write(src)


def fp(name, body, descr=""):
    return (f'(footprint "{name}" (version 20221018) (generator homefade_gen)\n'
            f'  (layer "F.Cu")\n  (descr "{descr}")\n'
            f'  (fp_text reference "REF**" (at 0 -4) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
            f'  (fp_text value "{name}" (at 0 4) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
            + body + ")\n")


def line(x0, y0, x1, y1, layer, w=0.12):
    return f'  (fp_line (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'


def rect(x0, y0, x1, y1, layer, w=0.12):
    return (line(x0, y0, x1, y0, layer, w) + line(x1, y0, x1, y1, layer, w) +
            line(x1, y1, x0, y1, layer, w) + line(x0, y1, x0, y0, layer, w))


# CH224K ESSOP-10 (3.9 x 4.9 body, 1.0 mm pitch, exposed pad = pin 11/"0")
b = ""
for i in range(5):
    y = -2.0 + i
    b += f'  (pad "{i+1}" smd roundrect (at -2.7 {y:.2f}) (size 1.5 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))\n'
    b += f'  (pad "{10-i}" smd roundrect (at 2.7 {y:.2f}) (size 1.5 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))\n'
b += '  (pad "11" smd rect (at 0 0) (size 2.3 3.0) (layers "F.Cu" "F.Mask"))\n'
b += '  (pad "11" smd rect (at 0 0) (size 1.8 2.4) (layers "F.Paste"))\n'
b += rect(-1.95, -2.45, 1.95, 2.45, "F.Fab", 0.1)
b += rect(-3.7, -2.75, 3.7, 2.75, "F.CrtYd", 0.05)
b += line(-1.95, -2.6, 1.95, -2.6, "F.SilkS") + line(-1.95, 2.6, 1.95, 2.6, "F.SilkS")
b += '  (fp_circle (center -3.3 -2.6) (end -3.2 -2.6) (stroke (width 0.2) (type solid)) (fill solid) (layer "F.SilkS"))\n'
open(os.path.join(OUT, "ESSOP-10_3.9x4.9mm_P1.0mm_EP.kicad_mod"), "w").write(
    fp("ESSOP-10_3.9x4.9mm_P1.0mm_EP", b, "WCH CH224K ESSOP-10; verify EP size against JLC library"))

# Alps RS60N11M9 fader. Origin = 3T end of frame on centreline; +X along travel.
# Pin positions are [DS] from the Alps drawing (via the project's FreeCAD macro).
# KiCad Y = -model Y (viewed from the mounting/knob side = PCB top).
b = ""
pot_x = 54.0 - 43.65
for name, ymodel in (("1", 5.625), ("T", 1.875), ("3", -1.875), ("2", -5.625)):
    b += f'  (pad "{name}" thru_hole circle (at {pot_x:.3f} {-ymodel:.3f}) (size 2.5 2.5) (drill 1.5) (layers "*.Cu" "*.Mask"))\n'
for name, ymodel in (("L1", 5.625), ("L2", -5.625)):
    b += f'  (pad "{name}" thru_hole circle (at {pot_x+7:.3f} {-ymodel:.3f}) (size 3.0 3.0) (drill 2.0) (layers "*.Cu" "*.Mask"))\n'
for name, ymodel in (("MA", 4.0), ("MB", -4.0)):
    b += f'  (pad "{name}" thru_hole circle (at {54+9.55:.3f} {-ymodel:.3f}) (size 2.5 2.5) (drill 1.5) (layers "*.Cu" "*.Mask"))\n'
# frame outline + under-body blocks (fab), courtyard on the solid blocks only
b += rect(0, -9, 106.5, 9, "F.Fab", 0.1)
b += rect(6.0, -8.0, 20.5, 8.0, "F.CrtYd", 0.05)      # pot terminal block [EST]
b += rect(60.0, -7.0, 66.5, 7.0, "F.CrtYd", 0.05)     # motor bracket [EST]
b += rect(6.0, -8.0, 20.5, 8.0, "F.SilkS", 0.12)
b += rect(60.0, -7.0, 66.5, 7.0, "F.SilkS", 0.12)
b += rect(66.5, -6.0, 92.0, 6.0, "Dwgs.User", 0.1)    # motor can, 5 mm above PCB
b += rect(92.0, -8.0, 104.5, 8.0, "Dwgs.User", 0.1)   # pulley housing, 6 mm above
b += f'  (fp_text user "MOTOR ABOVE: parts <2.5mm" (at 79 0) (layer "Dwgs.User") (effects (font (size 1 1) (thickness 0.15))))\n'
for x in (14.0, 94.0):  # M3 frame holes (panel side), for reference
    b += f'  (fp_circle (center {x} 0) (end {x+1.5} 0) (stroke (width 0.1) (type solid)) (fill none) (layer "Dwgs.User"))\n'
b = b.replace('(at 0 -4) (layer "F.SilkS")', '(at 13 -10)')
open(os.path.join(OUT, "Alps_RS60N11M9_Fader.kicad_mod"), "w").write(
    fp("Alps_RS60N11M9_Fader", b, "Alps RS60N11M9A0F 60mm motor fader, PCB side"))
print("ok", os.listdir(OUT))
