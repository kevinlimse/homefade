import sys, pcbnew
pcb = sys.argv[1]; b = pcbnew.LoadBoard(pcb)
M = {"U1": "ESSOP-10_3.9x4.9mm_P1.0mm_EP", "J1": "USB_C_Receptacle_HRO_TYPE-C-31-M-12",
     "SW1": "SW_TS-1187A", "SW2": "SW_TS-1187A", "U4": "ESP32-S3-MINI-1"}
for f in b.GetFootprints():
    ref = f.GetReference()
    if ref in M:
        ms = f.Models()
        if ref == "U4" and ms.size():
            m = ms[0]
        else:
            ms.clear(); m = pcbnew.FP_3DMODEL(); 
        m.m_Filename = "${KIPRJMOD}/homefade.3dshapes/" + M[ref] + ".step"
        if ref != "U4" or not ms.size():
            ms.push_back(m)
        else:
            ms[0] = m
    if ref == "FD1":
        f.Models().clear()
b.Save(pcb)
for f in b.GetFootprints():
    for m in f.Models():
        if f.GetReference() in M: print(f.GetReference(), m.m_Filename, m.m_Offset.x, m.m_Offset.y, m.m_Offset.z, m.m_Rotation.z)
