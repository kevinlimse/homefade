# homefade handover

Packed 2026-11-26. Copy this whole folder to a new machine and you have everything.

## Goal

A wall-mounted **motorized fader for Home Assistant**. It controls light brightness / colour temperature with **live two-way sync**: move the fader and HA follows; change the light in HA and the fader moves itself. Slim enough that **2–3 sit side by side at 18 mm pitch**.

## Chosen parts

| Part | Choice | Notes |
|---|---|---|
| Fader | **Alps RS60N11M9A0F**, 60 mm travel, 10k B, touch-sense, 10 V motor | AliExpress ~**S$18 incl. shipping** (listing 1005006443508464). Avoid "FOR ALPS"/"Not ALPS" clones. Datasheet: https://tech.alpsalpine.com/e/products/detail/RS60N11M9A0F/ |
| MCU | **ESP32-S3-MINI-1-N8** | Wi-Fi, native USB, capacitive touch for the fader's touch track |
| Motor driver | **TB6612FNG** (both bridges paralleled) | |
| Power | **CH224A** USB-C PD sink, requests **9 V** | TPS563201 buck to 3.3 V |
| PCB | 18.0 × 120 mm, 4-layer, one board per fader, v1.1 with 10-LED side-firing position bar (GPIO17) | ~US$5.70/board in LCSC parts |

## What's in this folder

- `pcb/` – full KiCad project (`homefade-fader.kicad_pro/sch/pcb`), schematic PDF, `README.md` (design detail, GPIO map, firmware tuning), `gen/` generator scripts (`gen/design.py` is the source of truth).
  - `pcb/fab/homefade-fader-gerbers-JLCPCB.zip` – Gerbers ready to upload. `BOM-JLCPCB.csv`, `CPL-JLCPCB.csv`, `BOM.md` for assembly.
  - `pcb/esphome/homefade-fader.yaml` – ESPHome firmware.
  - `pcb/freecad/` – PCBA and assembly STEP exports + macro.
- `cad/blade-fader-cad/` – copy of `Documents\fader-cad\` from the Blade: `alps_rs60n11m9_fader.FCStd/.step`, `homefade_fader_assembly.FCStd`, `homefade-fader-pcba.step`, `homefade-fader-assembly.step` (combined), `homefade_assembly.FCMacro`.
- `cad/fader-model/` – fader model generator (`.py`), STEP and preview.
- `freecad-macros/alps_rs60n11m9_fader.FCMacro` – copy to the FreeCAD macro folder (`%APPDATA%\FreeCAD\v1-1\Macro\`) on a new machine.

## Status

- PCB fully routed, KiCad DRC: 0 unconnected, no electrical errors. Gerbers/BOM/CPL generated.
- FreeCAD fader model + PCBA assembly done.
- ESPHome YAML passes `esphome config` but has **not been compiled or flashed**.
- **Nothing ordered yet** (fader or PCBs).

## Open items

1. Verify **U1 (CH224A ESSOP-10)** and **L1 (FXL0630)** footprints in the JLCPCB preview; check CPL rotations.
2. **Measure motor clearance on a real fader** (under-body heights in the model are estimated; parts under the motor are ≤ 2.5 mm).
3. **Widen the thin 0.15 mm ground trace** joining the GND island near the 9 V input caps (C2/C3/U5/J2).
4. **Compile ESPHome** (`esphome compile pcb/esphome/homefade-fader.yaml`) locally, then tune per `pcb/README.md`.
5. Order fader(s) and boards (confirm first).

## Switching machines

Install KiCad 7+, FreeCAD 1.1, ESPHome. Copy this folder, copy the macro into FreeCAD's macro folder, open `pcb/homefade-fader.kicad_pro`. The same package lives on Google Drive in **"home fade"** (as `homefade-handover.zip` + this file).
