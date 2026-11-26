"""Remove dangling track stubs / vias left by the router (non-GND), refill."""
import sys, pcbnew
pcb = sys.argv[1]; b = pcbnew.LoadBoard(pcb)
for it in range(5):
    b.BuildConnectivity()
    pcbnew.WriteDRCReport(b, '/tmp/cl.rpt', pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open('/tmp/cl.rpt').read()
    import re
    pos = set()
    for blk in re.split(r'\n(?=\[)', txt):
        if blk.startswith('[track_dangling]') or blk.startswith('[via_dangling]'):
            m = re.search(r'@\(([\d.]+) mm, ([\d.]+) mm\): (Track|Via) \[([^\]]+)\]', blk)
            if m and m.group(4) != 'GND':
                pos.add((float(m.group(1)), float(m.group(2)), m.group(3)))
    if not pos: break
    n = 0
    for t in list(b.GetTracks()):
        p = t.GetPosition() if t.Type() == pcbnew.PCB_VIA_T else t.GetStart()
        for x, y, k in pos:
            if (k == 'Via') == (t.Type() == pcbnew.PCB_VIA_T) and abs(pcbnew.ToMM(p.x) - x) < 0.002 and abs(pcbnew.ToMM(p.y) - y) < 0.002:
                b.Remove(t); n += 1; break
    print('removed', n)
    if n == 0: break
b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(pcb)
