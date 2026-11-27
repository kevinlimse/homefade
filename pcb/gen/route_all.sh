#!/bin/bash
# full pipeline: placement -> LED-row pre-route -> DSN (GND left to the In1 plane + pours)
# -> Freerouting -> import -> finishing router -> stitch vias -> cleanup
set -e
G=$(dirname $(readlink -f $0)); P=$1; W=${W:-/tmp/rt}
# SKIPGEN=1: reuse the placed board in $P (lets several router runs go in parallel)
if [ -z "$SKIPGEN" ]; then
python3 $G/make_fplib.py $P/homefade.pretty >/dev/null
python3 $G/make_pcb.py $P >/dev/null
python3 $G/ledbar_route.py $P/homefade-fader.kicad_pcb
fi
mkdir -p $W && cp -r $P/homefade.pretty $P/fp-lib-table $P/homefade-fader.kicad_pcb $W/
python3 $G/stitch.py $W/homefade-fader.kicad_pcb --escape-only
W=$W python3 - <<'PY'
import pcbnew, re, os
W=os.environ['W']
b=pcbnew.LoadBoard(W+'/homefade-fader.kicad_pcb'); pcbnew.ExportSpecctraDSN(b,W+'/hf.dsn')
s=open(W+'/hf.dsn').read(); i=s.index('(net GND'); d=0
for j in range(i,len(s)):
    d+= s[j]=='('; d-= s[j]==')'
    if d==0: break
s=s[:i]+s[j+1:]; s=re.sub(r'(\(class [^\n]*?)\bGND\b',r'\1',s); open(W+'/hf_nognd.dsn','w').write(s)
PY
/usr/lib/jvm/java-25-openjdk-amd64/bin/java -jar /opt/fr/fr.jar -de $W/hf_nognd.dsn -do $W/hf2.ses -mp ${MP:-60} > $W/fr2.log 2>&1
grep -E "Optimization stage completed" $W/fr2.log | grep -oE "final score: [^,]*\)" || true
python3 $G/import_ses.py $W/homefade-fader.kicad_pcb $W/hf2.ses $W/homefade-fader.kicad_pcb
python3 $G/finish.py $W/homefade-fader.kicad_pcb
python3 $G/stitch.py $W/homefade-fader.kicad_pcb
for i in 1 2 3; do python3 $G/cleanup.py $W/homefade-fader.kicad_pcb; done
