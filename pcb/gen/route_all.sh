#!/bin/bash
# full pipeline: placement -> DSN (GND left to pours) -> Freerouting -> import -> stitch
set -e
G=$(dirname $(readlink -f $0)); P=$1; W=/tmp/rt
python3 $G/make_fplib.py $P/homefade.pretty >/dev/null
python3 $G/make_pcb.py $P >/dev/null
mkdir -p $W && cp -r $P/homefade.pretty $P/fp-lib-table $P/homefade-fader.kicad_pcb $W/
python3 $G/stitch.py $W/homefade-fader.kicad_pcb --escape-only
python3 - <<'PY'
import pcbnew, re
b=pcbnew.LoadBoard('/tmp/rt/homefade-fader.kicad_pcb'); pcbnew.ExportSpecctraDSN(b,'/tmp/hf.dsn')
s=open('/tmp/hf.dsn').read(); i=s.index('(net GND'); d=0
for j in range(i,len(s)):
    d+= s[j]=='('; d-= s[j]==')'
    if d==0: break
s=s[:i]+s[j+1:]; s=re.sub(r'(\(class [^\n]*?)\bGND\b',r'\1',s); open('/tmp/hf_nognd.dsn','w').write(s)
PY
/usr/lib/jvm/java-25-openjdk-amd64/bin/java -jar /opt/fr/fr.jar -de /tmp/hf_nognd.dsn -do /tmp/hf2.ses -mp 60 > /tmp/fr2.log 2>&1
grep -E "Optimization stage completed" /tmp/fr2.log | grep -oE "final score: [^,]*\)" || true
python3 $G/import_ses.py $W/homefade-fader.kicad_pcb /tmp/hf2.ses $W/homefade-fader.kicad_pcb
python3 $G/finish.py $W/homefade-fader.kicad_pcb
python3 $G/stitch.py $W/homefade-fader.kicad_pcb
python3 $G/finish.py $W/homefade-fader.kicad_pcb --gnd
python3 $G/finish.py $W/homefade-fader.kicad_pcb --join
python3 $G/cleanup.py $W/homefade-fader.kicad_pcb
