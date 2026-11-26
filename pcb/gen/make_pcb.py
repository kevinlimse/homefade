"""Build homefade-fader.kicad_pcb from design.py (placement + nets + outline + zones)."""
import os, sys
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D

PROJ = sys.argv[1]
OX, OY = 50.0, 100.0  # page offset
mm = pcbnew.FromMM
P = lambda x, y: pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))
STD = "/usr/share/kicad/footprints"

board = pcbnew.BOARD()
ds = board.GetDesignSettings()
ds.SetCopperLayerCount(2)
ds.m_TrackMinWidth = mm(0.15)
ds.m_MinClearance = mm(0.15)
ds.m_ViasMinSize = mm(0.5)
ds.m_MinThroughDrill = mm(0.3)
ds.m_CopperEdgeClearance = mm(0.3)
ds.m_HoleClearance = mm(0.25)

nets = {}


def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n
    return nets[name]


# net classes
nc_default = ds.m_NetSettings.m_DefaultNetClass
nc_default.SetClearance(mm(0.18)); nc_default.SetTrackWidth(mm(0.2))
nc_default.SetViaDiameter(mm(0.6)); nc_default.SetViaDrill(mm(0.3))
pwr = pcbnew.NETCLASS("Power")
pwr.SetClearance(mm(0.18)); pwr.SetTrackWidth(mm(0.6))
pwr.SetViaDiameter(mm(0.8)); pwr.SetViaDrill(mm(0.4))
ds.m_NetSettings.m_NetClasses["Power"] = pwr
POWER_NETS = ("VBUS", "MOTOR_A", "MOTOR_B", "SW", "+3V3", "GND")

# outline
x0, x1, hw = D.BOARD_X0, D.BOARD_X1, D.BOARD_HW
r = 1.0
segs = [((x0 + r, -hw), (x1 - r, -hw)), ((x1, -hw + r), (x1, hw - r)),
        ((x1 - r, hw), (x0 + r, hw)), ((x0, hw - r), (x0, -hw + r))]
for a, b in segs:
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(*a)); s.SetEnd(P(*b)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
    board.Add(s)
for cx, cy, sx, sy in ((x0 + r, -hw + r, x0 + r, -hw), (x1 - r, -hw + r, x1, -hw + r),
                       (x1 - r, hw - r, x1 - r, hw), (x0 + r, hw - r, x0, hw - r)):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetCenter(P(cx, cy)); s.SetStart(P(sx, sy)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(-90, pcbnew.DEGREES_T))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)

fps = {}
for c in D.C:
    if not c["fp"]:
        continue
    lib, name = c["fp"].split(":")
    path = os.path.join(PROJ, "homefade.pretty") if lib == D.LIB else os.path.join(STD, lib + ".pretty")
    f = pcbnew.FootprintLoad(path, name)
    assert f is not None, c["fp"]
    f.SetFPID(pcbnew.LIB_ID(lib, name))
    f.SetReference(c["ref"]); f.SetValue(c["value"])
    x, y, rot = c["pos"]
    if rot is None:
        rot = 0
    f.SetPosition(P(x, y))
    f.SetOrientationDegrees(rot)
    if c["dnp"]:
        f.SetAttributes(f.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM)
    board.Add(f)
    for pad in f.Pads():
        pn = pad.GetNumber()
        if pn == "":
            continue
        assert pn in c["pins"], (c["ref"], pn)
        nn = c["pins"][pn]
        if nn:
            pad.SetNet(net(nn))
    f.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.7), mm(0.7)))
    f.Reference().SetTextThickness(mm(0.12))
    fps[c["ref"]] = f

# USB-C: orient so the mouth points to -X and sits flush with the board edge
j1 = fps["J1"]
for rot in (0, 90, 180, 270):
    j1.SetOrientationDegrees(rot)
    bb = j1.GetBoundingBox(False, False)
    sig = [p.GetPosition().x for p in j1.Pads() if p.GetNumber().startswith(("A", "B"))]
    if sum(sig) / len(sig) > j1.GetPosition().x + mm(3):
        break
fab = [g for g in j1.GraphicalItems() if g.GetLayer() == pcbnew.F_Fab and isinstance(g, pcbnew.FP_SHAPE)]
minx = min(min(g.GetStart().x, g.GetEnd().x) for g in fab)
j1.Move(pcbnew.VECTOR2I(mm(OX + x0) - minx - mm(0.6), 0))  # 0.6 mm overhang past edge

# ESP: make sure antenna (+ its keepout) points to +X
u4 = fps["U4"]
ant = [t for t in u4.GraphicalItems() if isinstance(t, pcbnew.FP_TEXT) and "Antenna" in t.GetText()]
if ant and ant[0].GetPosition().x < u4.GetPosition().x:
    u4.SetOrientationDegrees(90)
print("U4 rot", u4.GetOrientationDegrees(), "J1 rot", j1.GetOrientationDegrees())

# antenna keep-out (no copper either layer) from the module's pad edge to the board end
ux = pcbnew.ToMM(u4.GetPosition().x) - OX
ka = pcbnew.ZONE(board)
ka.SetIsRuleArea(True); ka.SetDoNotAllowCopperPour(True); ka.SetDoNotAllowTracks(True)
ka.SetDoNotAllowVias(True); ka.SetDoNotAllowPads(False); ka.SetDoNotAllowFootprints(False)
ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); ka.SetLayerSet(ls)
o = ka.Outline(); o.NewOutline()
for xy in ((ux + 7.8, -hw - 1), (x1 + 1, -hw - 1), (x1 + 1, hw + 1), (ux + 7.8, hw + 1)):
    o.Append(P(*xy))
ka.SetZoneName("ANTENNA_KEEPOUT")
board.Add(ka)

# GND pours both layers
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer); z.SetNet(net("GND"))
    o = z.Outline(); o.NewOutline()
    for xy in ((x0, -hw), (x1, -hw), (x1, hw), (x0, hw)):
        o.Append(P(*xy))
    z.SetLocalClearance(mm(0.25)); z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
    z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.35))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z)

# silk notes
def text(s, x, y, size=0.9, layer=pcbnew.B_SilkS, mirror=True):
    t = pcbnew.PCB_TEXT(board); t.SetText(s); t.SetPosition(P(x, y))
    t.SetLayer(layer); t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(0.15)); t.SetMirrored(mirror); board.Add(t)

text("homefade fader v1.0  ·  Alps RS60N11M9  ·  USB-C PD 9V", 50, -6.5)
text("Fader mounts on the OTHER side", 50, 6.5)
text("1 board = 1 fader. Chain VBUS/GND via J2 for 2-3 boards.", 50, 0, 0.8)

for n in POWER_NETS:
    if n in nets:
        nets[n].SetNetClass(pwr)
board.BuildConnectivity()
out = os.path.join(PROJ, "homefade-fader.kicad_pcb")
board.Save(out)
print("saved", out, "nets", len(nets))
