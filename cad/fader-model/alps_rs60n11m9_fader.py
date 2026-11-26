# -*- coding: utf-8 -*-
"""
Alps RS60N11M9A0F motorized fader (60 mm travel, 10k B, touch-sense, T-bar lever)
Parametric model built from the Alps Alpine product page drawings:
  https://tech.alpsalpine.com/e/products/detail/RS60N11M9A0F/

HOW TO USE IN FREECAD
  Macro > Macros... > (point at this file) > Execute
  or: open the Python console and run
      exec(open(r"<path>/alps_rs60n11m9_fader.py").read())
  It creates a new document "RS60N11M9" with one solid per sub-part
  (frame, rail housing, pot terminal block, motor, motor bracket, pulley
  housing, lever, pins) and exports a STEP next to this file.

COORDINATE SYSTEM
  X = along the travel, 0 at the 3T (left) end, 106.5 at the 1T end
  Y = across the width, 0 on the centreline
  Z = 0 on the MOUNTING SURFACE (top face of the metal frame), +Z toward the knob

DIMENSIONS
  [DS] = read directly from the datasheet drawing (authoritative)
  [EST] = estimated from the drawing/photo proportions (not dimensioned by Alps)
  Use [DS] values for panel cut-outs and PCB footprints. [EST] values are only
  for clearance/visualisation; check them against a real part.
"""

# ---------------------------------------------------------------- parameters
P = dict(
    # overall / frame
    L_total=106.5,          # [DS] 54 + 52.5
    W_frame=18.0,           # [DS]
    x_ref=54.0,             # [DS] datum: 54 from 3T end (centre of travel/holes)
    t_frame=0.8,            # [EST] sheet thickness
    flange_depth=4.0,       # [EST] side flanges of frame below mounting surface
    # panel mounting
    mount_pitch=80.0,       # [DS] 80 +/-0.3, 2-M3
    mount_d=2.5,            # M3 tap drill (thread not modelled)
    # travel / slot
    travel=60.0,            # [DS]
    slot_w=1.8,             # [EST] lever slot width in frame
    lever_pos=30.0,         # 0..60 mm, 0 = 3T end, 60 = 1T end (drawing shows 60)
    # lever (9-T, T-bar), plate lies in XZ plane
    lever_top_z=8.2,        # [DS] 8.2 +/-0.5 above mounting surface
    lever_bar_w=18.5,       # [DS] T-bar width along X
    lever_bar_h=4.0,        # [DS] T-bar height
    lever_t=1.2,            # [DS] 1.2 +0.1 plate thickness
    lever_hole_pitch=14.5,  # [DS] (14.5)
    lever_hole_d=2.0,       # [DS] 2-(dia 2)
    lever_stem_w=8.0,       # [DS] (8)
    # under-body
    seat_z=-26.0,           # [DS] 26 from mounting surface to PCB seating plane
    pin_len=3.5,            # [EST] pin protrusion below seating plane
    rail_w=14.0,            # [EST]
    rail_bottom_z=-8.0,     # [EST]
    # PCB footprint (viewed from mounting side) [DS]
    pot_pin_x=54.0 - 43.65, # pins 1,T,3,2 column
    pot_pin_pitch=3.75,     # 3 x 3.75 = 11.25
    lug_x=54.0 - 43.65 + 7.0,  # 43.65 - 36.65
    lug_y=5.625,            # lugs in line with pins 1 and 2
    lug_d=2.0,              # 2-dia2 holes
    pin_hole_d=1.5,         # 6-dia1.5 holes
    motor_pin_x=54.0 + 9.55,
    motor_pin_dy=4.0,       # A/B 8 apart
    # motor (estimated from photo / side view)
    motor_d=12.0,           # [EST]
    motor_x0=66.0,          # [EST]
    motor_x1=92.0,          # [EST]
    motor_cz=-15.0,         # [EST]
)
P["travel_x0"] = P["x_ref"] - P["travel"] / 2  # 24
P["mount_x"] = (P["x_ref"] - P["mount_pitch"] / 2, P["x_ref"] + P["mount_pitch"] / 2)

# -------------------------------------------------------- geometry back-end
try:
    import FreeCAD as App
    import Part
    BACKEND = "freecad"

    def box(x0, x1, y0, y1, z0, z1):
        return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, App.Vector(x0, y0, z0))

    def cyl(d, p0, p1):
        a = App.Vector(*p0)
        v = App.Vector(*p1) - a
        return Part.makeCylinder(d / 2, v.Length, a, v)

    def cut(a, b):
        return a.cut(b)

    def fuse(a, b):
        return a.fuse(b)
except ImportError:  # CadQuery fallback, used for checking outside FreeCAD
    import cadquery as cq
    BACKEND = "cadquery"

    def box(x0, x1, y0, y1, z0, z1):
        return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))

    def cyl(d, p0, p1):
        a = cq.Vector(*p0)
        v = cq.Vector(*p1) - a
        return cq.Solid.makeCylinder(d / 2, v.Length, a, v)

    def cut(a, b):
        return a.cut(b)

    def fuse(a, b):
        return a.fuse(b)


# ------------------------------------------------------------------ parts
def build(p=P):
    parts = {}
    L, W, t = p["L_total"], p["W_frame"], p["t_frame"]
    hw = W / 2

    # metal frame: top plate + two side flanges, slot, 2x M3 holes, touch/rivet hole
    frame = box(0, L, -hw, hw, -t, 0)
    frame = fuse(frame, box(0, L, -hw, -hw + t, -p["flange_depth"], 0))
    frame = fuse(frame, box(0, L, hw - t, hw, -p["flange_depth"], 0))
    sx0 = p["travel_x0"] - p["lever_t"] / 2 - 0.5
    sx1 = p["travel_x0"] + p["travel"] + p["lever_t"] / 2 + 0.5
    frame = cut(frame, box(sx0, sx1, -p["slot_w"] / 2, p["slot_w"] / 2, -t - 1, 1))
    for mx in p["mount_x"]:
        frame = cut(frame, cyl(p["mount_d"], (mx, 0, -t - 1), (mx, 0, 1)))
    parts["Frame"] = frame

    # resistor / rail housing under the frame
    rw = p["rail_w"] / 2
    parts["RailHousing"] = box(2.0, L - 2.0, -rw, rw, p["rail_bottom_z"], -t)

    # pot terminal block (3T end) down to seating plane
    parts["PotTerminalBlock"] = box(6.0, 20.5, -8.0, 8.0, p["seat_z"], p["rail_bottom_z"])

    # motor bracket with A/B terminals
    parts["MotorBracket"] = box(p["motor_pin_x"] - 3.0, p["motor_x0"], -7.0, 7.0,
                                p["seat_z"], p["rail_bottom_z"])
    # DC motor, axis along X
    parts["Motor"] = cyl(p["motor_d"], (p["motor_x0"], 0, p["motor_cz"]),
                         (p["motor_x1"], 0, p["motor_cz"]))
    # pulley / belt housing at 1T end
    parts["PulleyHousing"] = box(p["motor_x1"], L - 2.0, -8.0, 8.0, -20.0, p["rail_bottom_z"])

    # lever (T-bar), plate in XZ, thickness along Y
    cx = p["travel_x0"] + p["lever_pos"]
    lt = p["lever_t"] / 2
    ztop = p["lever_top_z"]
    zbar = ztop - p["lever_bar_h"]
    lever = box(cx - p["lever_bar_w"] / 2, cx + p["lever_bar_w"] / 2, -lt, lt, zbar, ztop)
    lever = fuse(lever, box(cx - p["lever_stem_w"] / 2, cx + p["lever_stem_w"] / 2,
                            -lt, lt, p["rail_bottom_z"] + 1, zbar))
    hz = zbar + p["lever_bar_h"] / 2
    for s in (-1, 1):
        hx = cx + s * p["lever_hole_pitch"] / 2
        lever = cut(lever, cyl(p["lever_hole_d"], (hx, -1, hz), (hx, 1, hz)))
    parts["Lever"] = lever

    # pins: dia = hole dia - 0.5 for clearance look
    zb = p["seat_z"] - p["pin_len"]
    pins = []
    for i in range(4):  # 1, T, 3, 2
        y = (1.5 - i) * p["pot_pin_pitch"]
        pins.append(cyl(p["pin_hole_d"] - 0.5, (p["pot_pin_x"], y, zb), (p["pot_pin_x"], y, p["seat_z"])))
    for s in (-1, 1):  # lugs
        pins.append(box(p["lug_x"] - 0.25, p["lug_x"] + 0.25, s * p["lug_y"] - 0.75, s * p["lug_y"] + 0.75,
                        zb, p["seat_z"]))
    for s in (1, -1):  # motor A (+Y), B (-Y)
        y = s * p["motor_pin_dy"]
        pins.append(cyl(p["pin_hole_d"] - 0.5, (p["motor_pin_x"], y, zb), (p["motor_pin_x"], y, p["seat_z"])))
    pin_solid = pins[0]
    for pn in pins[1:]:
        pin_solid = fuse(pin_solid, pn)
    parts["Pins"] = pin_solid
    return parts


COLORS = {
    "Frame": (0.80, 0.81, 0.83), "RailHousing": (0.15, 0.15, 0.15),
    "PotTerminalBlock": (0.12, 0.12, 0.12), "MotorBracket": (0.60, 0.61, 0.63),
    "Motor": (0.72, 0.72, 0.74), "PulleyHousing": (0.15, 0.15, 0.15),
    "Lever": (0.80, 0.81, 0.83), "Pins": (0.88, 0.88, 0.86),
}

if __name__ in ("__main__", "alps_rs60n11m9_fader") or BACKEND == "freecad":
    import os
    if "__file__" in globals():
        here = os.path.dirname(os.path.abspath(__file__))
    else:  # pasted into the console / macro editor
        here = os.path.join(os.path.expanduser("~"), "Documents", "fader-cad")
        os.makedirs(here, exist_ok=True)
    parts = build()
    if BACKEND == "freecad":
        doc = App.newDocument("RS60N11M9")
        objs = []
        for name, shp in parts.items():
            o = doc.addObject("Part::Feature", name)
            o.Shape = shp
            objs.append(o)
            if App.GuiUp:
                o.ViewObject.ShapeColor = COLORS[name]
        doc.recompute()
        step = os.path.join(here, "alps_rs60n11m9_fader.step")
        if App.GuiUp:  # ImportGui keeps the colours in the STEP
            import ImportGui
            ImportGui.export(objs, step)
        else:
            Part.export(objs, step)
        doc.saveAs(os.path.join(here, "alps_rs60n11m9_fader.FCStd"))
        if App.GuiUp:
            import FreeCADGui as Gui
            Gui.SendMsgToActiveView("ViewFit")
            Gui.activeDocument().activeView().viewIsometric()
    else:
        asm = cq.Assembly(name="RS60N11M9")
        for name, shp in parts.items():
            asm.add(shp, name=name, color=cq.Color(*COLORS[name]))
        asm.save(os.path.join(here, "alps_rs60n11m9_fader.step"))
        for name, shp in parts.items():
            bb = shp.BoundingBox()
            print(f"{name:16s} valid={shp.isValid()} vol={shp.Volume():8.1f}  "
                  f"x[{bb.xmin:.2f},{bb.xmax:.2f}] y[{bb.ymin:.2f},{bb.ymax:.2f}] z[{bb.zmin:.2f},{bb.zmax:.2f}]")
