"""Simple STEP models for parts with no KiCad library model (CadQuery)."""
import sys, cadquery as cq
out = sys.argv[1]
def save(shape, name):
    cq.exporters.export(shape, f"{out}/{name}.step")
# CH224A ESSOP-10: body 3.9 x 4.9 x 1.5, gull leads (simplified as flat tabs)
body = cq.Workplane("XY").box(3.9, 4.9, 1.45, centered=(True, True, False)).translate((0, 0, 0.1))
for i in range(5):
    y = -2.0 + i
    for s in (-1, 1):
        body = body.union(cq.Workplane("XY").box(1.05, 0.42, 0.2, centered=(True, True, False)).translate((s * 2.5, y, 0)))
save(body, "ESSOP-10_3.9x4.9mm_P1.0mm_EP")
# USB-C HRO TYPE-C-31-M-12 shell: 8.94 x 7.3 x 3.16, mouth at +Y (footprint coords) -> model y = -fp y
shell = cq.Workplane("XY").box(8.94, 7.3, 3.16, centered=(True, True, False))
shell = shell.edges("|Y").fillet(1.2)
mouth = cq.Workplane("XY").box(8.0, 5.0, 2.4, centered=(True, False, True)).translate((0, -3.7, 1.58))
save(shell.cut(mouth), "USB_C_Receptacle_HRO_TYPE-C-31-M-12")
# TS-1187A 5.1 x 5.1 x 1.5 tact switch with 4 legs
sw = cq.Workplane("XY").box(5.1, 5.1, 1.0, centered=(True, True, False))
sw = sw.union(cq.Workplane("XY").circle(1.6).extrude(0.5).translate((0, 0, 1.0)))
for x in (-3, 3):
    for y in (-1.875, 1.875):
        sw = sw.union(cq.Workplane("XY").box(1.0, 0.7, 0.2, centered=(True, True, False)).translate((x, y, 0)))
save(sw, "SW_TS-1187A")
print("models ok")
# SK6812SIDE-A side-view RGB LED: 4.0 x 1.6 footprint, 2.0 tall; light exits the +Y face
# (model coords; footprint -Y). White body, clear lens window, 4 terminals at the rear.
led = cq.Workplane("XY").box(4.0, 1.6, 2.0, centered=(True, True, False))
lens = cq.Workplane("XY").box(3.0, 0.3, 1.3, centered=(True, True, False)).translate((0, 0.75, 0.35))
term = None
for i in range(4):
    t = cq.Workplane("XY").box(0.6, 0.75, 0.12, centered=(True, True, False)).translate((-1.725 + 1.15 * i, -0.425, -0.02))
    term = t if term is None else term.union(t)
a = cq.Assembly(name="SK6812SIDE-A")
a.add(led.cut(lens), name="body", color=cq.Color(0.93, 0.93, 0.90))
a.add(lens, name="lens", color=cq.Color(0.85, 0.90, 1.0, 0.6))
a.add(term, name="terminals", color=cq.Color(0.88, 0.88, 0.86))
a.save(f"{out}/LED_SK6812SIDE-A_4.0x1.6mm.step")
print("led model ok")
