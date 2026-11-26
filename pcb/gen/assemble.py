import sys, cadquery as cq
from OCP.STEPCAFControl import STEPCAFControl_Reader
pcba_p, fader_p, out = sys.argv[1:4]
pcba = cq.importers.importStep(pcba_p)
fader = cq.importers.importStep(fader_p)
Z = -26.0 - 1.6   # PCB bottom; PCB top = seating plane (26 mm below the mounting surface)
pcba = pcba.translate((0, 0, Z))
bb = pcba.val().BoundingBox(); print("PCBA bbox", [round(v, 2) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)])
fb = fader.val().BoundingBox(); print("fader bbox", [round(v, 2) for v in (fb.xmin, fb.xmax, fb.ymin, fb.ymax, fb.zmin, fb.zmax)])
# interference check: every PCBA solid vs every fader solid
fs = fader.solids().vals(); ps = pcba.solids().vals()
print("solids", len(fs), len(ps))
hits = []
for i, p in enumerate(ps):
    pb = p.BoundingBox()
    for f in fs:
        if pb.xmax < f.BoundingBox().xmin or pb.xmin > f.BoundingBox().xmax or pb.zmax < f.BoundingBox().zmin: continue
        try:
            v = p.intersect(f).Volume()
        except Exception:
            v = 0
        if v > 0.01:
            hits.append((i, round(v, 2), [round(x, 1) for x in (pb.xmin, pb.xmax, pb.ymin, pb.ymax, pb.zmin, pb.zmax)]))
print("interferences", hits)
asm = cq.Assembly(name="homefade_fader_assembly")
asm.add(fader, name="Alps_RS60N11M9A0F")
asm.add(pcba, name="homefade_PCBA")
asm.save(out)
print("saved", out)
# clearance report per fader zone
zones = {"terminal block 6-20.5": (6, 20.5, -26.0), "rail 20.5-60": (20.5, 60, -8.0), "motor 66.5-92": (66.5, 92, -21.0), "pulley 92-104.5": (92, 104.5, -20.0)}
for n, (x0, x1, under) in zones.items():
    tops = [s.BoundingBox().zmax for s in ps if s.BoundingBox().xmax > x0 and s.BoundingBox().xmin < x1 and s.BoundingBox().zmax > -26.0 + 0.05]
    print(f"{n}: tallest part {max(tops) + 26.0 if tops else 0:.2f} mm above PCB, space {under + 26.0:.1f} mm [EST]")
