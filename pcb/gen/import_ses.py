"""Import a Freerouting .ses into a KiCad board (headless), fill zones, save."""
import sys, re, sexpdata, pcbnew
from sexpdata import Symbol as S
pcb, ses, out = sys.argv[1:4]
b = pcbnew.LoadBoard(pcb)
for t in list(b.GetTracks()):
    if not t.IsLocked():
        b.Remove(t)
t = sexpdata.loads(open(ses).read())
def find(n, key):
    return [e for e in n if isinstance(e, list) and e and e[0] == S(key)]
routes = find(t, 'routes')[0]
U = 10000.0  # 0.1 um units -> mm
mm = pcbnew.FromMM
layers = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu}
nets = b.GetNetsByName()
nt = nv = 0
for net in find(find(routes, 'network_out')[0], 'net'):
    name = str(net[1]); ni = nets[name]
    for w in find(net, 'wire'):
        p = find(w, 'path')[0]
        layer = layers[str(p[1])]; width = p[2] / U
        pts = p[3:]
        xy = [(pts[i] / U, -pts[i + 1] / U) for i in range(0, len(pts), 2)]
        for a, c in zip(xy, xy[1:]):
            tr = pcbnew.PCB_TRACK(b); tr.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
            tr.SetEnd(pcbnew.VECTOR2I(mm(c[0]), mm(c[1]))); tr.SetWidth(mm(width))
            tr.SetLayer(layer); tr.SetNet(ni); b.Add(tr); nt += 1
    for v in find(net, 'via'):
        m = re.search(r'_(\d+):(\d+)_um', str(v[1]))
        d, dr = (int(m.group(1)) / 1000, int(m.group(2)) / 1000) if m else (0.6, 0.3)
        via = pcbnew.PCB_VIA(b); via.SetPosition(pcbnew.VECTOR2I(mm(v[2] / U), mm(-v[3] / U)))
        via.SetWidth(mm(d)); via.SetDrill(mm(dr)); via.SetNet(ni); via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(via); nv += 1
b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
b.Save(out)
print('tracks', nt, 'vias', nv)
