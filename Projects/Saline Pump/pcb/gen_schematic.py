#!/usr/bin/env python3
"""
Generate a self-contained KiCad 7/8 schematic (.kicad_sch) for the
saline-pump controller. Every symbol is defined locally (no dependency on
KiCad's stock libraries) and all connectivity is done by net-label name, so
the netlist is unambiguous regardless of layout. Import into KiCad, then
'Annotate' + 'Update PCB from Schematic' as normal.

Author: Jarvis, 2026-08-14.
"""
import uuid

ROOT = str(uuid.uuid4())
PROJECT = "saline_pump"

def U():
    return str(uuid.uuid4())

# ---- geometry helpers -------------------------------------------------------
LEN = 2.54          # pin length
PITCH = 2.54        # vertical spacing between pins
HALFW = 15.24       # half body width

def sym_def(name, ref_prefix, value, pins):
    """pins: list of (number, pinname, side)  side in {'L','R'}."""
    lefts  = [p for p in pins if p[2] == 'L']
    rights = [p for p in pins if p[2] == 'R']
    n = max(len(lefts), len(rights))
    top = (n - 1) * PITCH / 2 + PITCH        # a little headroom
    bot = -top
    out = []
    out.append(f'    (symbol "{PROJECT}:{name}" (in_bom yes) (on_board yes)')
    out.append(f'      (property "Reference" "{ref_prefix}" (at 0 {top+2.54:.2f} 0)'
               f' (effects (font (size 1.27 1.27))))')
    out.append(f'      (property "Value" "{value}" (at 0 {bot-2.54:.2f} 0)'
               f' (effects (font (size 1.27 1.27))))')
    out.append(f'      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    out.append(f'      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    # graphic body
    out.append(f'      (symbol "{name}_0_1"')
    out.append(f'        (rectangle (start {-HALFW:.2f} {top:.2f}) (end {HALFW:.2f} {bot:.2f})'
               f' (stroke (width 0.254) (type default)) (fill (type background)))')
    out.append(f'      )')
    # pins (unit 1)
    out.append(f'      (symbol "{name}_1_1"')
    def place(lst, side):
        m = len(lst)
        for i, (num, pname, _s) in enumerate(lst):
            y = top - PITCH - i * ( (top-PITCH - (bot+PITCH)) / max(m-1,1) ) if m > 1 else 0.0
            if side == 'L':
                x = -(HALFW + LEN); ang = 0
            else:
                x = (HALFW + LEN); ang = 180
            out.append(f'        (pin passive line (at {x:.2f} {y:.2f} {ang})'
                       f' (length {LEN:.2f})'
                       f' (name "{pname}" (effects (font (size 1.016 1.016))))'
                       f' (number "{num}" (effects (font (size 1.016 1.016)))))')
            # record the world-space offset for label placement (y-flip applied later)
            PIN_OFFSETS[(name, num)] = (x, y, side)
    place(lefts, 'L')
    place(rights, 'R')
    out.append(f'      )')
    out.append(f'    )')
    return "\n".join(out)

PIN_OFFSETS = {}   # (symname, pinnum) -> (x, y, side) in symbol space

# ---- part catalogue ---------------------------------------------------------
# Each symbol type defined once. pins = [(num, name, side), ...]
SYMBOLS = {}
def define(name, ref, value, pins):
    SYMBOLS[name] = (ref, value, pins)

define("ESP32", "U", "ESP32-DevKitC-30", [
    ("1", "VIN(5V)", 'L'), ("2", "3V3", 'L'), ("3", "GND", 'L'), ("4", "EN", 'L'),
    ("5", "IO25", 'L'), ("6", "IO26", 'L'), ("7", "IO32", 'L'), ("8", "IO33", 'L'),
    ("9", "IO27", 'L'), ("10", "IO14", 'L'), ("11", "IO13", 'L'), ("12", "IO22", 'L'),
    ("13", "IO23", 'R'), ("14", "IO18", 'R'), ("15", "IO16", 'R'), ("16", "IO17", 'R'),
    ("17", "IO5",  'R'), ("18", "IO4",  'R'), ("19", "IO21", 'R'), ("20", "IO34", 'R'),
    ("21", "IO35", 'R'), ("22", "IO19", 'R'),
])
define("BARREL", "J", "DC_5.5x2.1", [("1", "+12V", 'R'), ("2", "GND", 'R'), ("3", "SHLD", 'R')])
define("ESTOP", "SW", "E-STOP_NC", [("1", "IN", 'L'), ("2", "OUT", 'R')])
define("BUCK", "U", "MP1584_5V", [("1", "IN+", 'L'), ("2", "IN-", 'L'),
                                  ("3", "OUT+", 'R'), ("4", "OUT-", 'R')])
define("MOSFET", "Q", "IRLZ44N", [("1", "G", 'L'), ("2", "D", 'R'), ("3", "S", 'R')])
define("R", "R", "R", [("1", "1", 'L'), ("2", "2", 'R')])
define("C", "C", "C", [("1", "1", 'L'), ("2", "2", 'R')])
define("DIODE", "D", "1N5822", [("1", "K", 'L'), ("2", "A", 'R')])
define("PUMP", "J", "PUMP_MOTOR", [("1", "+", 'L'), ("2", "-", 'R')])
define("ENC", "J", "EC11", [("1", "A", 'L'), ("2", "C", 'L'), ("3", "B", 'L'),
                            ("4", "SW1", 'R'), ("5", "SW2", 'R')])
define("TRRS", "J", "TRRS_3.5mm", [("1", "T", 'L'), ("2", "R1", 'L'),
                                   ("3", "R2", 'R'), ("4", "S", 'R')])
define("TFT", "J", "GC9A01", [("1", "VCC", 'L'), ("2", "GND", 'L'), ("3", "SCL", 'L'),
                              ("4", "SDA", 'L'), ("5", "RES", 'R'), ("6", "DC", 'R'),
                              ("7", "CS", 'R'), ("8", "BLK", 'R')])

# ---- instances --------------------------------------------------------------
# (refdes, symtype, x, y, value_override, {pinnum: net})
INSTANCES = []
def inst(ref, sym, x, y, nets, value=None):
    INSTANCES.append((ref, sym, x, y, nets, value))

# ESP32
inst("U1", "ESP32", 100, 120, {
    "1": "+5V", "2": "+3V3", "3": "GND", "4": None,
    "5": "PUMP_L", "6": "PUMP_R", "7": "ENC_L_A", "8": "ENC_L_B",
    "9": "ENC_L_SW", "10": "ENC_R_A", "11": "ENC_R_B", "12": "ENC_R_SW",
    "13": "TFT_MOSI", "14": "TFT_SCK", "15": "TFT_DC", "16": "TFT_RST",
    "17": "TFT_CS_L", "18": "TFT_CS_R", "19": "HX_SCK", "20": "HX_DT_L",
    "21": "HX_DT_R", "22": "ESTOP_SENSE",
})
# Power input
inst("J1", "BARREL", 40, 40, {"1": "+12V", "2": "GND", "3": "GND"})
inst("SW1", "ESTOP", 40, 70, {"1": "+12V", "2": "+12V_SW"})
inst("U2", "BUCK", 40, 110, {"1": "+12V", "2": "GND", "3": "+5V", "4": "GND"})
inst("C1", "C", 70, 40, {"1": "+12V", "2": "GND"}, "100nF")
inst("C2", "C", 90, 40, {"1": "+12V", "2": "GND"}, "470uF")
inst("C3", "C", 70, 155, {"1": "+5V", "2": "GND"}, "100nF")
inst("C4", "C", 90, 155, {"1": "+5V", "2": "GND"}, "100uF")

# Pump L cluster
inst("R1", "R", 200, 40, {"1": "PUMP_L", "2": "Q1_G"}, "150")
inst("R2", "R", 200, 60, {"1": "Q1_G", "2": "GND"}, "10k")
inst("Q1", "MOSFET", 240, 50, {"1": "Q1_G", "2": "PUMP_L_M", "3": "GND"})
inst("D1", "DIODE", 240, 80, {"1": "+12V_SW", "2": "PUMP_L_M"})
inst("JPL", "PUMP", 280, 50, {"1": "+12V_SW", "2": "PUMP_L_M"})

# Pump R cluster
inst("R3", "R", 200, 110, {"1": "PUMP_R", "2": "Q2_G"}, "150")
inst("R4", "R", 200, 130, {"1": "Q2_G", "2": "GND"}, "10k")
inst("Q2", "MOSFET", 240, 120, {"1": "Q2_G", "2": "PUMP_R_M", "3": "GND"})
inst("D2", "DIODE", 240, 150, {"1": "+12V_SW", "2": "PUMP_R_M"})
inst("JPR", "PUMP", 280, 120, {"1": "+12V_SW", "2": "PUMP_R_M"})

# E-stop sense divider (optional)
inst("R5", "R", 200, 180, {"1": "+12V_SW", "2": "ESTOP_SENSE"}, "100k")
inst("R6", "R", 200, 200, {"1": "ESTOP_SENSE", "2": "GND"}, "33k")

# Encoders
inst("JEL", "ENC", 40, 170, {"1": "ENC_L_A", "2": "GND", "3": "ENC_L_B",
                             "4": "ENC_L_SW", "5": "GND"})
inst("JER", "ENC", 40, 210, {"1": "ENC_R_A", "2": "GND", "3": "ENC_R_B",
                             "4": "ENC_R_SW", "5": "GND"})

# HX711 reservoir base jacks (SCK shared, DT separate)
inst("JHL", "TRRS", 340, 40, {"1": "+3V3", "2": "GND", "3": "HX_SCK", "4": "HX_DT_L"})
inst("JHR", "TRRS", 340, 80, {"1": "+3V3", "2": "GND", "3": "HX_SCK", "4": "HX_DT_R"})

# Displays (shared bus, unique CS)
inst("JDL", "TFT", 340, 130, {"1": "+3V3", "2": "GND", "3": "TFT_SCK", "4": "TFT_MOSI",
                              "5": "TFT_RST", "6": "TFT_DC", "7": "TFT_CS_L", "8": "+3V3"})
inst("JDR", "TFT", 340, 180, {"1": "+3V3", "2": "GND", "3": "TFT_SCK", "4": "TFT_MOSI",
                              "5": "TFT_RST", "6": "TFT_DC", "7": "TFT_CS_R", "8": "+3V3"})

# ---- emit -------------------------------------------------------------------
# build symbol defs (populates PIN_OFFSETS)
symdefs = "\n".join(sym_def(name, ref, val, pins)
                    for name, (ref, val, pins) in SYMBOLS.items())

body = []
labels = []
for ref, sym, x, y, nets, value in INSTANCES:
    refval = value if value else SYMBOLS[sym][1]
    iu = U()
    b = []
    b.append(f'  (symbol (lib_id "{PROJECT}:{sym}") (at {x} {y} 0) (unit 1)')
    b.append(f'    (in_bom yes) (on_board yes) (dnp no) (uuid "{iu}")')
    b.append(f'    (property "Reference" "{ref}" (at {x} {y-2.54} 0) (effects (font (size 1.27 1.27))))')
    b.append(f'    (property "Value" "{refval}" (at {x} {y+2.54} 0) (effects (font (size 1.27 1.27))))')
    b.append(f'    (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))')
    b.append(f'    (property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))')
    for num, pname, side in SYMBOLS[sym][2]:
        b.append(f'    (pin "{num}" (uuid "{U()}"))')
    b.append(f'    (instances (project "{PROJECT}" (path "/{ROOT}" (reference "{ref}") (unit 1))))')
    b.append(f'  )')
    body.append("\n".join(b))
    # labels at each connected pin
    for num, pname, side in SYMBOLS[sym][2]:
        net = nets.get(num)
        if not net:
            continue
        ox, oy, s = PIN_OFFSETS[(sym, num)]
        wx = x + ox
        wy = y - oy            # symbol Y is up, schematic Y is down -> flip
        just = "left" if s == 'L' else "right"
        ang = 0 if s == 'L' else 180
        labels.append(
            f'  (global_label "{net}" (shape bidirectional) (at {wx:.2f} {wy:.2f} {ang})'
            f' (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {just}))'
            f' (uuid "{U()}"))')

doc = []
doc.append(f'(kicad_sch (version 20230121) (generator eeschema)')
doc.append(f'  (uuid "{ROOT}")')
doc.append(f'  (paper "A2")')
doc.append(f'  (title_block (title "Saline Pump Controller") (date "2026-08-14")'
           f' (rev "v1") (company "Rob / Jarvis"))')
doc.append(f'  (lib_symbols')
doc.append(symdefs)
doc.append(f'  )')
doc.extend(body)
doc.extend(labels)
doc.append(f'  (sheet_instances (path "/" (page "1")))')
doc.append(f')')

out = "\n".join(doc) + "\n"
with open("saline_pump.kicad_sch", "w") as f:
    f.write(out)
print("wrote saline_pump.kicad_sch", len(out), "bytes")
