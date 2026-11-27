"""Add GND stitching vias wherever they fit, refill, drop vias that touch no GND copper on one layer."""
import sys, pcbnew
pcb = sys.argv[1]
b = pcbnew.LoadBoard(pcb)
mm = pcbnew.FromMM
bb = b.GetBoardEdgesBoundingBox()
inner = pcbnew.BOX2I(bb.GetPosition(), bb.GetSize()); inner.Inflate(-mm(1.3))
gnd = b.GetNetsByName()["GND"]
CLR = mm(0.25)
keep = [z for z in b.Zones() if z.GetIsRuleArea()]
others = [t for t in b.GetTracks()] + [p for p in b.GetPads()]
def ok(v, skip=None):
    pos = v.GetPosition()
    for z in keep:
        if z.Outline().Contains(pos):
            return False
    if not inner.Contains(pos):
        return False
    vs = v.GetEffectiveShape(pcbnew.F_Cu)
    for it in others:
        if it is skip or (skip is not None and it.Type() == pcbnew.PCB_PAD_T and it.GetParent() == skip.GetParent() and it.GetNetCode() == gnd.GetNetCode()):
            continue
        if it.GetNetCode() == gnd.GetNetCode() and it.Type() != pcbnew.PCB_PAD_T:
            continue
        for L in (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):  # In1 is the GND plane
            if it.IsOnLayer(L) and vs.Collide(it.GetEffectiveShape(L), CLR + (0 if it.GetNetCode() != gnd.GetNetCode() else mm(0.2))):
                return False
    # also holes (THT pads / NPTH)
    return True
added = []
def mkvia(x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(int(x), int(y))); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
    v.SetNet(gnd); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    return v
import math
# 1) escape via for every GND SMD pad, right next to it, with a short track
for pad in [p for p in b.GetPads() if p.GetNetCode() == gnd.GetNetCode() and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]:
    c = pad.GetPosition(); placed = False
    for r in (0.9, 1.1, 1.3, 1.5, 1.8):
        for a in range(0, 360, 30):
            v = mkvia(c.x + mm(r) * math.cos(math.radians(a)), c.y + mm(r) * math.sin(math.radians(a)))
            vp = v.GetPosition()
            if min([math.hypot(vp.x - o.GetPosition().x, vp.y - o.GetPosition().y) for o in others if o.Type() == pcbnew.PCB_VIA_T] or [1e12]) < mm(0.9):
                continue
            if not ok(v, pad):
                continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(c); t.SetEnd(v.GetPosition()); t.SetWidth(mm(0.3))
            t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd)
            sh = t.GetEffectiveShape(pcbnew.F_Cu); bad = False
            for it in others:
                if it.GetNetCode() != gnd.GetNetCode() and it.IsOnLayer(pcbnew.F_Cu) and sh.Collide(it.GetEffectiveShape(pcbnew.F_Cu), mm(0.2)):
                    bad = True; break
            if bad:
                continue
            v.SetLocked(True); t.SetLocked(True)
            b.Add(v); b.Add(t); others += [v, t]; placed = True; break
        if placed:
            break
if '--escape-only' in sys.argv:
    b.Save(pcb); print('escape vias placed'); sys.exit(0)
# 2) grid stitching, coarse then fine
bb2 = b.GetBoardEdgesBoundingBox()
for step, off in ((mm(2.0), mm(1.0)), (mm(0.8), mm(1.4))):
    x = bb2.GetLeft() + off
    while x < bb2.GetRight():
        y = bb2.GetTop() + off
        while y < bb2.GetBottom():
            v = mkvia(x, y)
            near = min([math.hypot(x - a.GetPosition().x, y - a.GetPosition().y) for a in others if a.Type() == pcbnew.PCB_VIA_T] or [1e12])
            if near >= (mm(1.5) if step < mm(1.6) else mm(1.2)) and ok(v):
                b.Add(v); others.append(v); added.append(v)
            y += step
        x += step
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    fz = {L: [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer() == L] for L in (pcbnew.F_Cu, pcbnew.B_Cu)}
    for v in list(added):
        if not all(any(z.GetFilledPolysList(L).Contains(v.GetPosition()) for z in fz[L]) for L in fz):
            b.Remove(v); added.remove(v); others.remove(v)
# 3) any F.Cu / B.Cu fill island without a via gets one (fine search inside the island)
for it_ in range(2):
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    fz = {L: [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer() == L] for L in (pcbnew.F_Cu, pcbnew.B_Cu)}
    vias = [o for o in b.GetTracks() if o.Type() == pcbnew.PCB_VIA_T and o.GetNetCode() == gnd.GetNetCode()]
    thts = [p for p in b.GetPads() if p.GetNetCode() == gnd.GetNetCode() and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    fixed = 0
    for L, other in ((pcbnew.F_Cu, pcbnew.B_Cu), (pcbnew.B_Cu, pcbnew.F_Cu)):
        for z in fz[L]:
            fp_ = z.GetFilledPolysList(L)
            for k in range(fp_.OutlineCount()):
                one = pcbnew.SHAPE_POLY_SET(); one.AddOutline(fp_.Outline(k))
                for h in range(fp_.HoleCount(k)):
                    one.AddHole(fp_.Hole(k, h))
                if any(one.Contains(v.GetPosition()) for v in vias) or any(one.Contains(p.GetPosition()) for p in thts):
                    continue
                bbx = one.BBox(); found = False
                x = bbx.GetLeft()
                while x < bbx.GetRight() and not found:
                    y = bbx.GetTop()
                    while y < bbx.GetBottom() and not found:
                        v = mkvia(x, y); vp = v.GetPosition()
                        if one.Contains(vp) and any(zz.GetFilledPolysList(other).Contains(vp) for zz in fz[other]) and ok(v) and \
                           min([math.hypot(vp.x - o.GetPosition().x, vp.y - o.GetPosition().y) for o in vias] or [1e12]) > mm(0.9):
                            # via must sit fully inside the island
                            c = pcbnew.SHAPE_POLY_SET(); 
                            if all(one.Contains(pcbnew.VECTOR2I(int(vp.x + mm(0.35) * math.cos(t)), int(vp.y + mm(0.35) * math.sin(t)))) for t in [i * math.pi / 4 for i in range(8)]):
                                b.Add(v); vias.append(v); others.append(v); found = True; fixed += 1
                        y += mm(0.1)
                    x += mm(0.1)
    print('island vias', fixed)
b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
b.Save(pcb)
print("stitch vias", len(added))
