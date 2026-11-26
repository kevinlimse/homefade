import re, sexpdata
from sexpdata import Symbol as S
def load(path):
    return sexpdata.loads(open(path).read())
def find_sym(tree, name):
    for x in tree[1:]:
        if isinstance(x,list) and x and x[0]==S('symbol') and x[1]==name: return x
def pins(sym, tree=None):
    out=[]
    def walk(n):
        if isinstance(n,list) and n:
            if n[0]==S('pin'):
                at=[e for e in n if isinstance(e,list) and e[0]==S('at')][0]
                nm=[e for e in n if isinstance(e,list) and e[0]==S('name')][0][1]
                num=[e for e in n if isinstance(e,list) and e[0]==S('number')][0][1]
                ln=[e for e in n if isinstance(e,list) and e[0]==S('length')][0][1]
                out.append((num,nm,at[1],at[2],at[3] if len(at)>3 else 0,ln, str(n[1])))
            for c in n: walk(c)
    walk(sym)
    ext=[e for e in sym if isinstance(e,list) and e[0]==S('extends')]
    if ext and tree is not None:
        out+=pins(find_sym(tree,ext[0][1]),tree)
    return out
