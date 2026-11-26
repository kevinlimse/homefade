import os, sys, subprocess, pcbnew
PROJ=sys.argv[1]; pcb=os.path.join(PROJ,'homefade-fader.kicad_pcb')
b=pcbnew.LoadBoard(pcb)
dsn='/tmp/hf.dsn'; ses='/tmp/hf.ses'
assert pcbnew.ExportSpecctraDSN(b,dsn)
r=subprocess.run(['java','-jar','/opt/fr/fr.jar','-de',dsn,'-do',ses,'-mp','30','-host','KiCad'],capture_output=True,text=True,timeout=900)
print(r.stdout[-1500:], r.stderr[-1500:])
assert pcbnew.ImportSpecctraSES(b,ses)
f=pcbnew.ZONE_FILLER(b); f.Fill(b.Zones())
b.Save(pcb)
print('tracks',len(b.GetTracks()))
