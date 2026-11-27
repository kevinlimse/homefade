"""Single source of truth for the homefade fader controller (one board per fader).

Coordinates: X along the fader (0 = 3T end, same as the FreeCAD model),
Y across the board, KiCad orientation (+Y = towards pot pin "2").
"""

LIB = "homefade"

# ref, value, lib_id, footprint, LCSC, pins{pad: net}, (x, y, rot), group, note
C = []


def add(ref, value, lib_id, fp, lcsc, pins, pos, group, note="", dnp=False):
    C.append(dict(ref=ref, value=value, lib_id=lib_id, fp=fp, lcsc=lcsc, pins=pins,
                  pos=pos, group=group, note=note, dnp=dnp))


R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"


def R(ref, val, lcsc, a, b, pos, group, note=""):
    add(ref, val, "Device:R", R0402, lcsc, {"1": a, "2": b}, pos, group, note)


def Cap(ref, val, lcsc, a, b, pos, group, fp=C0402, note=""):
    add(ref, val, "Device:C", fp, lcsc, {"1": a, "2": b}, pos, group, note)


# ---------------------------------------------------------------- USB-C + PD
add("J1", "USB-C (PD in, USB data)", "Connector:USB_C_Receptacle_USB2.0_16P",
    "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", "C165948",
    {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
     "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
     "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP",
     "A7": "USB_DM", "B7": "USB_DM", "A8": None, "B8": None, "S1": "GND"},
    (-2.3, 0, None), "power")
add("U1", "CH224A", f"{LIB}:CH224A", f"{LIB}:ESSOP-10_3.9x4.9mm_P1.0mm_EP",
    "C42459160",
    {"1": "VBUS", "2": None, "3": None, "4": None, "5": None, "6": "CC2",
     "7": "CC1", "8": "VBUS", "9": "PD_CFG1", "10": "PD_PG", "11": "GND"},
    (25.5, 2.9, 90), "power", "USB-PD sink (CH224A, 32 V-tolerant), requests 9 V via R3=6.8k; 24k = 12 V.")
Cap("C1", "1uF", "C83063", "VBUS", "GND", (22.0, 5.0, 90), "power")
R("R3", "6.8k", "C25917", "PD_CFG1", "GND", (29.3, 5.0, 90), "power",
  "9 V request. Use 24k (C25769) for 12 V. NEVER leave open (=20 V).")
add("U5", "USBLC6-2SC6", "Power_Protection:USBLC6-2SC6",
    "Package_TO_SOT_SMD:SOT-23-6", "C7519",
    {"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM", "2": "GND",
     "5": "+3V3"}, (23.5, -5.0, 0), "power")
Cap("C2", "22uF 25V", "C45783", "VBUS", "GND", (35.2, -6.4, 0), "power", C0805)
Cap("C3", "22uF 25V", "C45783", "VBUS", "GND", (35.2, -3.8, 0), "power", C0805)
add("J2", "VBUS/GND chain (DNP)", "Connector_Generic:Conn_01x02",
    "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", "",
    {"1": "VBUS", "2": "GND"}, (28.5, -5.5, 90), "power",
    "Solder pads to share one USB-C supply between 2-3 boards", dnp=True)
add("#FLG01", "PWR_FLAG", "power:PWR_FLAG", None, "", {"1": "VBUS"}, None, "power")
add("#FLG02", "PWR_FLAG", "power:PWR_FLAG", None, "", {"1": "GND"}, None, "power")

# ---------------------------------------------------------------- 3V3 buck
add("U2", "TPS563201", "Regulator_Switching:TPS563200",
    "Package_TO_SOT_SMD:SOT-23-6", "C116592",
    {"1": "GND", "2": "SW", "3": "VBUS", "4": "FB", "5": "BUCK_EN", "6": "BST"},
    (38.5, 3.0, 0), "buck")
R("R15", "100k", "C25741", "VBUS", "BUCK_EN", (38.5, 5.8, 0), "buck")
Cap("C4", "10uF 25V", "C96446", "VBUS", "GND", (35.2, 4.2, 90), "buck", C0603)
Cap("C5", "100nF", "C1525", "VBUS", "GND", (35.2, 1.4, 90), "buck")
Cap("C6", "100nF", "C1525", "BST", "SW", (38.5, -0.2, 0), "buck")
add("L1", "3.3uH 6.5x6.5", "Device:L", f"{LIB}:L_FXL0630", "C167219",
    {"1": "SW", "2": "+3V3"}, (45.0, -4.3, 0), "buck")
R("R5", "33k", "C25779", "+3V3", "FB", (41.4, 5.3, 90), "buck")
R("R6", "10k", "C25744", "FB", "GND", (42.6, 5.3, 90), "buck")
Cap("C7", "22uF", "C59461", "+3V3", "GND", (47.6, 1.6, 90), "buck", C0603)
Cap("C8", "22uF", "C59461", "+3V3", "GND", (49.2, 1.6, 90), "buck", C0603)
add("#FLG04", "PWR_FLAG", "power:PWR_FLAG", None, "", {"1": "+3V3"}, None, "buck")

# ---------------------------------------------------------------- motor driver
add("U3", "TB6612FNG", "Driver_Motor:TB6612FNG",
    "Package_SO:SSOP-24_5.3x8.2mm_P0.65mm", "C88224",
    {"1": "MOTOR_A", "2": "MOTOR_A", "11": "MOTOR_A", "12": "MOTOR_A",
     "5": "MOTOR_B", "6": "MOTOR_B", "7": "MOTOR_B", "8": "MOTOR_B",
     "3": "GND", "4": "GND", "9": "GND", "10": "GND", "18": "GND",
     "13": "VBUS", "14": "VBUS", "24": "VBUS", "20": "+3V3",
     "19": "MOT_STBY", "21": "MOT_IN1", "17": "MOT_IN1",
     "22": "MOT_IN2", "16": "MOT_IN2", "23": "MOT_PWM", "15": "MOT_PWM"},
    (55.0, -1.8, 90), "motor", "Both H-bridges paralleled (A||B) for 2.4 A avg")
Cap("C9", "10uF 25V", "C96446", "VBUS", "GND", (52.0, 5.4, 0), "motor", C0603)
Cap("C10", "100nF", "C1525", "VBUS", "GND", (54.6, 5.4, 0), "motor")
Cap("C11", "100nF", "C1525", "+3V3", "GND", (54.0, -7.4, 0), "motor")
R("R7", "10k", "C25744", "MOT_STBY", "GND", (58.6, 5.4, 0), "motor",
  "Keeps driver in standby while ESP boots")

# ---------------------------------------------------------------- fader
add("FD1", "RS60N11M9A0F", f"{LIB}:RS60N11M9_Fader", f"{LIB}:Alps_RS60N11M9_Fader",
    "", {"1": "POT_HI", "3": "GND", "2": "WIPER", "T": "TOUCH_RAW", "L1": "GND",
         "L2": "GND", "MA": "MOTOR_A", "MB": "MOTOR_B"},
    (0, 0, 0), "fader", "Hand-soldered (through-hole), supplied by you")
R("R8", "1k", "C11702", "+3V3", "POT_HI", (68.0, -6.6, 0), "fader",
  "Keeps wiper max ~3.0 V, inside the ADC's linear range")
R("R9", "1k", "C11702", "WIPER", "FADER_POS", (70.0, -6.6, 0), "fader")
Cap("C12", "100nF", "C1525", "FADER_POS", "GND", (72.0, -6.6, 0), "fader")
R("R10", "100R", "C25076", "TOUCH_RAW", "TOUCH", (68.0, 5.2, 0), "fader",
  "Series ESD resistor on the touch line")

# ---------------------------------------------------------------- MCU
ESP = {str(n): None for n in range(1, 66)}
for n in (1, 2, 42, 43, *range(46, 66)):
    ESP[str(n)] = "GND"
ESP.update({"3": "+3V3", "4": "BOOT", "5": "FADER_POS", "6": "TOUCH",
            "8": "MOT_PWM", "9": "MOT_IN1", "10": "MOT_IN2", "11": "MOT_STBY",
            "12": "PD_PG", "13": "VBUS_SENSE", "14": "LED", "21": "LEDBAR_IO",
            "23": "USB_DM", "24": "USB_DP", "45": "EN"})
add("U4", "ESP32-S3-MINI-1-N8", f"{LIB}:ESP32-S3-MINI-1", f"{LIB}:ESP32-S3-MINI-1",
    "C2913206", ESP, (100.7, 0, 270), "mcu", "Antenna overhangs the fader end")
Cap("C13", "22uF", "C59461", "+3V3", "GND", (90.0, -6.0, 90), "mcu", C0603)
Cap("C14", "100nF", "C1525", "+3V3", "GND", (91.6, -6.0, 90), "mcu")
R("R11", "10k", "C25744", "+3V3", "EN", (79.0, 5.0, 0), "mcu")
Cap("C15", "1uF", "C83063", "EN", "GND", (81.2, 5.0, 0), "mcu")
R("R4", "10k", "C25744", "+3V3", "PD_PG", (74.0, -6.6, 0), "mcu")
R("R12", "100k", "C25741", "VBUS", "VBUS_SENSE", (76.0, -6.6, 0), "mcu")
R("R13", "10k", "C25744", "VBUS_SENSE", "GND", (78.0, -6.6, 0), "mcu")
R("R14", "1k", "C11702", "LED", "LED_A", (84.4, 5.3, 0), "mcu")
add("D1", "Red", "Device:LED", "LED_SMD:LED_0603_1608Metric", "C2286",
    {"1": "GND", "2": "LED_A"}, (86.9, 6.6, 0), "mcu")
add("SW1", "BOOT", "Switch:SW_Push", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", "C318884",
    {"1": "BOOT", "2": "GND"}, (71.0, 1.0, 0), "mcu")
add("SW2", "RESET", "Switch:SW_Push", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", "C318884",
    {"1": "EN", "2": "GND"}, (80.0, 1.0, 0), "mcu")

# ---------------------------------------------------------------- position LED bar
# 10 side-firing RGB LEDs (SK6812SIDE-A) along the +Y board edge, one per 10 % of travel,
# shining sideways out from under the fader. They run from a 4.5 V buck (VLED): at 4.5 V the
# LED's VIH (0.65 x VDD = 2.9 V) is below the ESP's 3.3 V output, so no level shifter is needed.
add("U6", "TPS563201", "Regulator_Switching:TPS563200",
    "Package_TO_SOT_SMD:SOT-23-6", "C116592",
    {"1": "GND", "2": "SW_LED", "3": "VBUS", "4": "FB_LED", "5": "BUCK_EN", "6": "BST_LED"},
    (87.6, -2.6, 180), "buck", "4.5 V for the LED bar")
Cap("C16", "10uF 25V", "C96446", "VBUS", "GND", (86.0, -5.4, 0), "buck", C0603)
Cap("C18", "100nF", "C1525", "BST_LED", "SW_LED", (86.3, 0.1, 0), "buck")
add("L2", "3.3uH 4x4", "Device:L", "Inductor_SMD:L_Changjiang_FNR4020S", "C167826",
    {"1": "SW_LED", "2": "VLED"}, (89.6, 2.3, 90), "buck")
R("R16", "33k", "C25779", "VLED", "FB_LED", (84.9, -1.0, 90), "buck", "33k/6.8k = 4.5 V")
R("R17", "6.8k", "C25917", "FB_LED", "GND", (84.9, -3.1, 90), "buck")
Cap("C19", "22uF 25V", "C45783", "VLED", "GND", (86.3, 2.6, 90), "buck", C0805)
R("R18", "100R", "C25076", "LEDBAR_IO", "LB_D0", (91.9, -1.6, 90), "ledbar",
  "Series resistor on the LED data line (GPIO17)")
LED_X = [81.0 - 6.0 * i for i in range(10)]  # LED 1 at the 1T end, LED 10 at the 3T end
for i, x in enumerate(LED_X):
    add(f"D{i + 2}", "SK6812SIDE-A", f"{LIB}:SK6812SIDE-A", f"{LIB}:LED_SK6812SIDE-A_4.0x1.6mm",
        "C5378721", {"1": f"LB_D{i}", "2": "VLED", "3": f"LB_D{i + 1}" if i < 9 else None, "4": "GND"},
        (x, 8.2, 180), "ledbar", "Side-firing RGB, light exits the +Y board edge" if i == 0 else "")
# decoupling in the gaps between LEDs (none under the motor bracket); gen/ledbar_route.py
# pre-routes the row: VLED rail along the edge, data hops inboard, a GND via per gap
for j, x in enumerate((77.7, 71.7, 53.7, 47.7, 35.7, 29.7)):
    Cap(f"C{20 + j}", "100nF", "C1525", "VLED", "GND", (x, 7.55, 90), "ledbar")
add("#FLG05", "PWR_FLAG", "power:PWR_FLAG", None, "", {"1": "VLED"}, None, "ledbar")

# board extents (fader coordinates)
BOARD_X0, BOARD_X1, BOARD_HW = -6.0, 114.0, 9.0
# keep-outs under the fader body (from the FreeCAD model, mostly [EST])
KEEPOUT_TALL = [(6.0, 20.5), (60.0, 66.5)]  # terminal block, motor bracket: nothing
LOW_ZONE = [(66.5, 106.5)]  # under motor / pulley: parts <= 2.5 mm
