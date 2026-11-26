# homefade fader controller v1.0

One small board per Alps RS60N11M9A0F motor fader. It connects the fader to Home Assistant through ESPHome, with live sync both ways.

## Why one board per fader (and not one board for three)

* **Width = fader width.** The board is **18.0 mm wide**, the same as the fader frame, and hangs directly on the fader's own pins. Faders can sit side by side at an **18 mm pitch** (frames touching). A 3-fader board would fix the spacing forever and still be ≥ 54 mm wide.
* **Flat back.** Every SMD part sits on the side facing the fader, in the space under its body (the fader seats 26 mm below the panel, and most of that is empty). The back of the PCB is flat apart from the soldered fader pins, so total depth is about **26 mm + 1.6 mm PCB + ~1.5 mm of pin tails**.
* **One USB-C feeds several.** Plug USB-C into one board. Wire its **J2 (VBUS/GND)** pads to J2 on the next board(s). Only plug one USB-C into a chained set. A 9 V / 2 A (18 W+) charger is plenty for 3 faders.
* Each fader becomes its own ESPHome device. They're independent, and one bad board doesn't take the others down. An ESP32-S3 costs about $3.

Board: **18.0 × 120.0 mm**, 2 layers, 1.6 mm. Coordinates match the FreeCAD model (X = 0 at the fader's 3T end). The board runs 6 mm past the 3T end for the USB-C and 7.5 mm past the 1T end, so the Wi-Fi antenna isn't under the motor.

## Blocks

| Block | Part | Notes |
|---|---|---|
| Power in | USB-C (HRO TYPE-C-31-M-12) + **CH224A** PD sink | Asks for **9 V** (R3 = 6.8 k). For 12 V, fit 24 k (C25769) and set `max_duty: 0.83`. Never leave R3 open: open = 20 V, which kills the TB6612. Most chargers do 9 V; many (Apple, for example) don't offer 12 V. |
| ESD | USBLC6-2SC6 | On D+/D− |
| 3.3 V | TPS563201 buck, 3.3 µH, 33 k/10 k | 4.5–17 V in |
| Motor | **TB6612FNG**, both bridges in parallel | 15 V max; brake/coast; STBY pulled low while the ESP boots |
| MCU | **ESP32-S3-MINI-1-N8** | Native USB on the same USB-C for flashing and logs (no USB-UART chip). Built-in capacitive touch is used for the fader's touch track. |
| Fader | pot (via 1 k from 3V3 so the wiper tops out at ~3.0 V), RC filter → GPIO1; touch "T" → GPIO2 | Frame lugs to GND |
| Extra | BOOT/RESET buttons, LED (GPIO10), VBUS sense (GPIO9, ÷11), PD power-good (GPIO8) | The firmware won't drive the motor without PD power (for example when it's only on a PC port at 5 V) |

GPIO map: 1 wiper ADC, 2 touch, 4 PWM, 5 IN1, 6 IN2, 7 STBY, 8 PD_PG, 9 VBUS sense, 10 LED, 19/20 USB.

## Files

* `homefade-fader.kicad_pro / .kicad_sch / .kicad_pcb`: KiCad 7+ project. Schematic uses net labels.
* `board-routed.png`: top and bottom copper.
* `fab/homefade-fader-gerbers-JLCPCB.zip`: Gerbers and Excellon drill files, ready to upload (2 layers, 1.6 mm).
* `homefade.pretty`, `homefade.kicad_sym`: project footprints and symbols (fader footprint from the Alps drawing, Espressif's official ESP32-S3-MINI-1 footprint).
* `fab/BOM-JLCPCB.csv`, `fab/CPL-JLCPCB.csv`, `fab/BOM.md`: JLCPCB assembly files. Every part was in stock at LCSC on 2026-11-26.
* `esphome/homefade-fader.yaml`: firmware (validated with `esphome config`, ESPHome 2026.11).
* `gen/`: Python scripts that generate everything from `gen/design.py`. `route_all.sh` re-runs placement → Freerouting → finishing router → stitching.

## Status / before ordering

1. **Routing is done.** Freerouting handled the signals (GND was left to the pours). A small finishing pass then placed GND escape vias, added about 150 stitching vias and routed the last nets. KiCad DRC reports **0 unconnected pads and no clearance, width or hole errors**. What's left is cosmetic (silk over copper, silk near the edge, library-path warnings). Gerbers and drill files are in `fab/homefade-fader-gerbers-JLCPCB.zip`.
   *Worth a glance in KiCad:* the GND area around C2/C3/U5/J2 reaches the main ground through one 0.15 mm trace plus its pour. Widening it, or nudging the USB/CC traces to let the pour through, would help the motor return current. The USB D+/D− pair is long (~75 mm). That's fine for 12 Mbit/s full-speed but isn't a matched pair.
2. Check the JLC footprint preview for **U1 (CH224A ESSOP-10)** and **L1 (FXL0630)**. Both use my land patterns (EP and inductor pad sizes come from typical packages, not the exact datasheets). Also fix rotations in the CPL preview; JLC's 0° often differs from KiCad's.
3. The fader's under-body heights are **[EST]** in the FreeCAD model. Parts under the motor (x 66–92 mm) are ≤ 2.5 mm tall; the model gives ~5 mm of space. Check this against a real fader before ordering.
4. Antenna: keep metal off the board end past the fader (x > 106.5 mm). A metal faceplate 26 mm above will reduce range somewhat.
5. In HA, allow the device to perform Home Assistant actions (ESPHome integration → Configure).

## Firmware tuning (first boot)

1. Watch **Fader raw** in the logs at both ends of travel. Put the values in `adc_bottom` / `adc_top`.
2. Set `esp32_touch: setup_mode: true`, then touch and release the knob. Choose `touch_threshold` between the two values (S3 values *rise* when touched).
3. If the fader runs away from the target, set `motor_invert: "true"`. Raise `min_duty` if it stalls near the target; lower `kp` if it overshoots.
