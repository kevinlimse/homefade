"""Tiny grid router: connect pads that Freerouting left unrouted (non-GND).
For each unconnected pad, Dijkstra on a 0.1 mm 2-layer grid to any copper of the same net."""
import sys, heapq, math, re, subprocess
import numpy as np
import pcbnew
from PIL import Image, ImageDraw

pcb = sys.argv[1]
b = pcbnew.LoadBoard(pcb)
mm = pcbnew.FromMM
RES = 0.1  # mm per cell
TW, CLR, VIA = 0.2, 0.19, 0.6
GOAL = None
bb = b.GetBoardEdgesBoundingBox()
X0, Y0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
W = int(pcbnew.ToMM(bb.GetWidth()) / RES) + 1
H = int(pcbnew.ToMM(bb.GetHeight()) / RES) + 1
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]


def cell(p):
    return (int(round((pcbnew.ToMM(p.x) - X0) / RES)), int(round((pcbnew.ToMM(p.y) - Y0) / RES)))


def draw_poly(img, ps):
    d = ImageDraw.Draw(img)
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [((pcbnew.ToMM(o.CPoint(k).x) - X0) / RES, (pcbnew.ToMM(o.CPoint(k).y) - Y0) / RES) for k in range(o.PointCount())]
        if len(pts) > 2:
            d.polygon(pts, fill=1)


def items():
    for t in b.GetTracks():
        yield t
    for p in b.GetPads():
        yield p


def unconnected_pads():
    pcbnew.WriteDRCReport(b, pcb + '.fin.rpt', pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(pcb + '.fin.rpt').read()
    out = []
    for blk in txt.split('[unconnected_items]')[1:]:
        lines = blk.split('\n')[1:5]
        for l in lines:
            m = re.search(r'@\(([\d.]+) mm, ([\d.]+) mm\): (?:PTH )?[Pp]ad (\S+) \[([^\]]+)\] of (\S+)', l)
            if m and m.group(4) != 'GND':
                out.append((m.group(5), m.group(3), m.group(4)))
    return out


def route(ref, padnum, netname, item=None):
    net = b.GetNetsByName()[netname]
    fp = b.FindFootprintByReference(ref) if item is None else None
    pad = item if item is not None else [p for p in fp.Pads() if p.GetNumber() == padnum][0]
    hw = TW / 2
    blkL = {L: np.zeros((H, W), bool) for L in LAYERS}
    glL = {L: np.zeros((H, W), bool) for L in LAYERS}
    yy, xx = np.mgrid[0:H, 0:W]
    def mark(arr, it, L, infl):
        if it.Type() in (pcbnew.PCB_TRACE_T, pcbnew.PCB_ARC_T):
            ax, ay = (pcbnew.ToMM(it.GetStart().x) - X0) / RES, (pcbnew.ToMM(it.GetStart().y) - Y0) / RES
            bx, by = (pcbnew.ToMM(it.GetEnd().x) - X0) / RES, (pcbnew.ToMM(it.GetEnd().y) - Y0) / RES
            r = (pcbnew.ToMM(it.GetWidth()) / 2 + infl) / RES
        elif it.Type() == pcbnew.PCB_VIA_T:
            ax = bx = (pcbnew.ToMM(it.GetPosition().x) - X0) / RES; ay = by = (pcbnew.ToMM(it.GetPosition().y) - Y0) / RES
            r = (pcbnew.ToMM(it.GetWidth()) / 2 + infl) / RES
        else:  # pad: bounding box (+ clearance)
            bb_ = it.GetBoundingBox()
            x0 = int(math.floor((pcbnew.ToMM(bb_.GetLeft()) - infl - X0) / RES)); x1 = int(math.ceil((pcbnew.ToMM(bb_.GetRight()) + infl - X0) / RES))
            y0 = int(math.floor((pcbnew.ToMM(bb_.GetTop()) - infl - Y0) / RES)); y1 = int(math.ceil((pcbnew.ToMM(bb_.GetBottom()) + infl - Y0) / RES))
            arr[max(y0, 0):max(y1 + 1, 0), max(x0, 0):max(x1 + 1, 0)] = True
            return
        x0, x1 = int(min(ax, bx) - r - 1), int(max(ax, bx) + r + 2); y0, y1 = int(min(ay, by) - r - 1), int(max(ay, by) + r + 2)
        x0, y0 = max(x0, 0), max(y0, 0)
        X = xx[y0:y1, x0:x1]; Y = yy[y0:y1, x0:x1]
        dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1) if L2 > 0 else 0
        d2 = (X - (ax + t * dx)) ** 2 + (Y - (ay + t * dy)) ** 2
        arr[y0:y1, x0:x1] |= d2 <= r * r
    # items in the start pad's own cluster (BFS over connectivity)
    same = [it for it in items() if it.GetNetCode() == net.GetNetCode()]
    par = list(range(len(same)))
    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    def pts(it):
        if it.Type() == pcbnew.PCB_TRACE_T: return [it.GetStart(), it.GetEnd()]
        return [it.GetPosition()]
    for i, A in enumerate(same):
        for j in range(i + 1, len(same)):
            B = same[j]
            if not any(A.IsOnLayer(L) and B.IsOnLayer(L) for L in LAYERS): continue
            hit = False
            for p in pts(A):
                if B.Type() == pcbnew.PCB_PAD_T and B.HitTest(p): hit = True
                elif B.Type() != pcbnew.PCB_PAD_T and any(abs(p.x - q.x) < 50 and abs(p.y - q.y) < 50 for q in pts(B)): hit = True
                elif B.Type() == pcbnew.PCB_VIA_T and B.HitTest(p): hit = True
            for p in pts(B):
                if A.Type() in (pcbnew.PCB_PAD_T, pcbnew.PCB_VIA_T) and A.HitTest(p): hit = True
            if hit: par[f(i)] = f(j)
    root = [f(i) for i, it in enumerate(same) if (item is not None and it.m_Uuid.AsString() == item.m_Uuid.AsString()) or (item is None and it.Type() == pcbnew.PCB_PAD_T and it.GetParent().GetReference() == ref and it.GetNumber() == padnum)]
    own = set(same[i].m_Uuid.AsString() for i in range(len(same)) if f(i) in root)
    print('  own cluster items', len(own))
    for it in items():
        for L in LAYERS:
            if not it.IsOnLayer(L):
                continue
            if it.GetNetCode() == net.GetNetCode():
                if it.m_Uuid.AsString() in own:
                    continue
                if GOAL is not None and it.m_Uuid.AsString() not in GOAL:
                    continue
                if True:
                    mark(glL[L], it, L, 0)
            else:
                mark(blkL[L], it, L, CLR + hw)
    for z in b.Zones():
        if z.GetIsRuleArea():
            zb = z.GetBoundingBox()
            for L in LAYERS:
                blkL[L][int((pcbnew.ToMM(zb.GetTop()) - Y0) / RES):, int((pcbnew.ToMM(zb.GetLeft()) - X0) / RES) - 3:] = True
    blk = np.stack([blkL[L] for L in LAYERS])
    gl = np.stack([glL[L] for L in LAYERS])
    e = int((0.3 + hw) / RES) + 1
    blk[:, :e, :] = blk[:, -e:, :] = True
    blk[:, :, :e] = blk[:, :, -e:] = True
    # via blocked where either layer is blocked for a via-sized footprint
    vr = int(math.ceil((VIA / 2 - hw) / RES)) + 1
    vb = blk[0] | blk[1]
    from scipy.ndimage import binary_dilation
    vb = binary_dilation(vb, iterations=vr)
    sx, sy = cell(pad.GetPosition())
    start_layers = [i for i, L in enumerate(LAYERS) if pad.IsOnLayer(L)]
    # free the pad's own area as start region
    dist = {}
    pq = []
    for li in start_layers:
        blk[li, sy, sx] = False
        heapq.heappush(pq, (0, li, sx, sy)); dist[(li, sx, sy)] = 0
    prev = {}
    dirs = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    padbox = pad.GetBoundingBox()
    end = None
    while pq:
        d, li, x, y = heapq.heappop(pq)
        if d > dist.get((li, x, y), 1e18):
            continue
        if gl[li, y, x]:
            end = (li, x, y); break
        for dx, dy, c in dirs:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            inpad = li in start_layers and padbox.Contains(pcbnew.VECTOR2I(mm(X0 + nx * RES), mm(Y0 + ny * RES)))
            if blk[li, ny, nx] and not inpad:
                continue
            nd = d + c + (0.3 if li == 0 else 0.5)  # prefer top a bit less congested? small bias
            if nd < dist.get((li, nx, ny), 1e18):
                dist[(li, nx, ny)] = nd; prev[(li, nx, ny)] = (li, x, y); heapq.heappush(pq, (nd, li, nx, ny))
        if not vb[y, x] and not padbox.Contains(pcbnew.VECTOR2I(mm(X0 + x * RES), mm(Y0 + y * RES))):
            ol = 1 - li; nd = d + 40
            if nd < dist.get((ol, x, y), 1e18):
                dist[(ol, x, y)] = nd; prev[(ol, x, y)] = (li, x, y); heapq.heappush(pq, (nd, ol, x, y))
    if end is None:
        print('FAILED', ref, padnum, netname); return False
    path = [end]
    while path[-1] in prev:
        path.append(prev[path[-1]])
    path.reverse()
    # emit: split by layer, simplify collinear
    def P(c):
        return pcbnew.VECTOR2I(mm(X0 + c[1] * RES), mm(Y0 + c[2] * RES))
    segs = []
    cur = [path[0]]
    for a in path[1:]:
        if a[0] != cur[-1][0]:
            segs.append(cur); cur = [a]
            v = pcbnew.PCB_VIA(b); v.SetPosition(P(a)); v.SetWidth(mm(VIA)); v.SetDrill(mm(0.3))
            v.SetNet(net); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v)
        else:
            cur.append(a)
    segs.append(cur)
    n = 0
    for s in segs:
        pts = [s[0]]
        for i in range(1, len(s) - 1):
            d1 = (s[i][1] - pts[-1][1], s[i][2] - pts[-1][2]); d2 = (s[i + 1][1] - s[i][1], s[i + 1][2] - s[i][2])
            if d1[0] * d2[1] - d1[1] * d2[0] != 0:
                pts.append(s[i])
        pts.append(s[-1])
        for a, c in zip(pts, pts[1:]):
            if a[1:] == c[1:]:
                continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(P(a)); t.SetEnd(P(c)); t.SetWidth(mm(TW))
            t.SetLayer(LAYERS[a[0]]); t.SetNet(net); b.Add(t); n += 1
    # connect pad centre to first grid point
    t = pcbnew.PCB_TRACK(b); t.SetStart(pad.GetPosition()); t.SetEnd(P(path[0])); t.SetWidth(mm(TW))
    t.SetLayer(LAYERS[path[0][0]]); t.SetNet(net); b.Add(t)
    print('routed', ref, padnum, netname, 'segments', n, 'len', len(path) * RES, 'mm')
    return True


def gnd_island_pads():
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    g = b.GetNetsByName()['GND'].GetNetCode()
    vias = [o for o in b.GetTracks() if o.Type() == pcbnew.PCB_VIA_T and o.GetNetCode() == g]
    pads = [p for p in b.GetPads() if p.GetNetCode() == g]
    out = []
    for z in b.Zones():
        if z.GetIsRuleArea(): continue
        L = z.GetLayer(); fp = z.GetFilledPolysList(L)
        for k in range(fp.OutlineCount()):
            one = pcbnew.SHAPE_POLY_SET(); one.AddOutline(fp.Outline(k))
            if any(one.Contains(v.GetPosition()) for v in vias): continue
            if any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and one.Contains(p.GetPosition()) for p in pads): continue
            pp = [p for p in pads if p.IsOnLayer(L) and one.Contains(p.GetPosition())]
            if pp:
                out.append((pp[0].GetParent().GetReference(), pp[0].GetNumber(), 'GND'))
    return out

def gnd_components():
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    g = b.GetNetsByName()['GND'].GetNetCode()
    links = [o for o in b.GetTracks() if o.Type() == pcbnew.PCB_VIA_T and o.GetNetCode() == g] + \
            [p for p in b.GetPads() if p.GetNetCode() == g and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    isl = []
    for z in b.Zones():
        if z.GetIsRuleArea(): continue
        L = z.GetLayer(); fp = z.GetFilledPolysList(L)
        for k in range(fp.OutlineCount()):
            one = pcbnew.SHAPE_POLY_SET(); one.AddOutline(fp.Outline(k)); isl.append(one)
    par = list(range(len(isl)))
    def f(i):
        while par[i] != i: i = par[i]
        return i
    where = {}
    for o in links:
        ins = [i for i, p in enumerate(isl) if p.Contains(o.GetPosition())]
        for a in ins[1:]: par[f(a)] = f(ins[0])
        if ins: where[o.m_Uuid.AsString()] = (o, ins[0])
    comps = {}
    for k, (o, i) in where.items(): comps.setdefault(f(i), []).append(o)
    areas = {c: sum(isl[i].Area() for i in range(len(isl)) if f(i) == c) for c in comps}
    main = max(areas, key=areas.get)
    return comps, main

if '--join' in sys.argv:
    TW, CLR = 0.15, 0.19
    comps, main = gnd_components()
    GOAL = set(o.m_Uuid.AsString() for o in comps[main])
    for c, objs in comps.items():
        if c == main: continue
        print('joining island with', len(objs), 'links')
        for o in objs:
            if route('-', '-', 'GND', item=o):
                break
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(pcb); sys.exit(0)

if '--gnd' in sys.argv:
    TW, CLR = 0.15, 0.19
    for u in gnd_island_pads():
        route(*u); b.BuildConnectivity()
    b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(pcb); sys.exit(0)

done = set()
for _ in range(4):
    todo = [u for u in unconnected_pads() if u not in done]
    if not todo:
        break
    for u in todo:
        done.add(u)
        route(*u)
        b.BuildConnectivity()
b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(pcb)
