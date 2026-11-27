"""Pre-route the position LED bar (locked tracks, kept by Freerouting):
VLED rail along the +Y edge under the LEDs, data hops just inboard of the row,
and a GND via in each gap that ties the LED GND pad and the gap capacitor to both pours."""
import os, sys, pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D
b = pcbnew.LoadBoard(sys.argv[1])
mm = pcbnew.FromMM
OX, OY = 50.0, 100.0
P = lambda x, y: pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))
nets = {n: b.FindNet(n) for n in ("VLED", "GND")}
fps = {f.GetReference(): f for f in b.GetFootprints()}


def pad(ref, num):
    p = [q for q in fps[ref].Pads() if q.GetNumber() == num][0].GetPosition()
    return pcbnew.ToMM(p.x) - OX, pcbnew.ToMM(p.y) - OY


def track(pts, net, w):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(x0, y0)); t.SetEnd(P(x1, y1))
        t.SetWidth(mm(w)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net); t.SetLocked(True); b.Add(t)


def via(x, y, net):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetDrill(mm(0.3)); v.SetWidth(mm(0.6))
    v.SetNet(net); v.SetLocked(True); b.Add(v)


RAIL_Y, DATA_Y = 8.55, 6.45
leds = sorted((c for c in D.C if c["fp"] and "SK6812SIDE" in c["fp"]), key=lambda c: -c["pos"][0])
caps = {round(c["pos"][0], 1): c["ref"] for c in D.C if c["group"] == "ledbar" and c["ref"].startswith("C")}
xs = [pad(c["ref"], "2")[0] for c in leds]
track([(min(xs) - 2.2 + 0.575, RAIL_Y), (max(xs) + 1.6, RAIL_Y)], nets["VLED"], 0.3)
for i, c in enumerate(leds):
    r = c["ref"]
    x2, y2 = pad(r, "2"); track([(x2, y2), (x2, RAIL_Y)], nets["VLED"], 0.3)
    x4, y4 = pad(r, "4")
    vx = x4 - 0.8
    via(vx, 7.6, nets["GND"]); track([(x4, y4), (vx, 7.6)], nets["GND"], 0.25)
    if i + 1 < len(leds):
        x3, y3 = pad(r, "3"); x1, y1 = pad(leds[i + 1]["ref"], "1")
        net = [q for q in fps[r].Pads() if q.GetNumber() == "3"][0].GetNet()
        track([(x3, y3), (x3, DATA_Y), (x1, DATA_Y), (x1, y1)], net, 0.2)
    cx = round(x4 - 1.575, 1)
    if cx in caps:
        cr = caps[cx]
        xa, ya = pad(cr, "1"); track([(xa, ya), (xa, RAIL_Y)], nets["VLED"], 0.3)
        xg, yg = pad(cr, "2"); track([(xg, yg), (vx, 7.6)], nets["GND"], 0.25)
    else:
        print("no gap cap at", cx)
b.Save(sys.argv[1])
print("ledbar pre-routed:", len(leds), "LEDs")
