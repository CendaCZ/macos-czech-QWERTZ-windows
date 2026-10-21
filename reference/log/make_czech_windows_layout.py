#!/usr/bin/env python3
"""
Generate "Czech (Windows original).keylayout" — an exact macOS replica of the
original Windows Czech keyboard layout.

Data source (OFFICIAL, Microsoft):
  reference/kbdcz.html    Microsoft Learn "Czech Keyboard" interactive page
                          (https://learn.microsoft.com/en-us/globalization/keyboards/kbdcz)
                          KLID 00000405 = Windows "Czech" (the regular/default one).
                          Contains every modifier state (normal, Shift, Caps,
                          Caps+Shift, AltGr, AltGr+Shift/Ctrl+Alt) plus the
                          official DEAD-KEY composition tables.
  reference/czech_source_utf8.klc   cross-check source (MSKLC-format Czech QWERTZ)

Only two things are not on the MS page (they render no graphics), taken from the
KLC cross-check: Option+Space = NO-BREAK SPACE, and the numeric keypad.

Output: ../Czech (Windows original).keylayout   (plain .keylayout → works on
Apple Silicon as-is; copy to ~/Library/Keyboard Layouts or /Library/Keyboard
Layouts and log out/in).
"""
import html as ht
import os
import re
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "reference")
OUT = os.path.join(HERE, "..", "Czech (Windows original).keylayout")

LAYOUT_NAME = "Czech (Windows original)"
LAYOUT_ID = "-30105"          # unique: in use are 4711, -21957, -9364, -14193
GROUP = "126"

# ---------------------------------------------------------------------------
# 1. physical geometry: official page rows -> macOS virtual key codes
#    page renders ISO-105: row0 number, row1 Q-row, row2 home, row3 bottom
# ---------------------------------------------------------------------------
ROW_CODES = [
    [50, 18, 19, 20, 21, 23, 22, 26, 28, 25, 29, 27, 24, 51],
    [48, 12, 13, 14, 15, 17, 16, 32, 34, 31, 35, 33, 30, 42],
    [57,  0,  1,  2,  3,  5,  4, 38, 40, 37, 41, 39, 36],
    [56, 10,  6,  7,  8,  9, 11, 45, 46, 43, 47, 44, 60],
]
MODIFIER_CODES = {57, 56, 60}        # Caps / LShift / RShift: no character
SPECIAL = {51: "\x08", 48: "\x09", 36: "\r"}   # Backspace / Tab / Return

# official state div  ->  keyMap index
STATE_TO_INDEX = {
    "normallower": 0,
    "shiftlower": 1,
    "ctrlaltlower": 2,       # AltGr (Ctrl+Alt)
    # index 3 = AltGr+Shift  -> official page: EVERY key blank
    "normalcaps": 4,
    "shiftcaps": 5,
    "ctrlaltcaps": 6,
    # index 7 = Caps+Shift+AltGr -> official page: EVERY key blank
}

# official VK name of a dead key -> mac key code
VK_TO_MAC = {
    "VK_OEM_3": 50, "VK_1": 18, "VK_2": 19, "VK_3": 20, "VK_4": 21,
    "VK_5": 23, "VK_6": 22, "VK_7": 26, "VK_8": 28, "VK_9": 25, "VK_0": 29,
    "VK_OEM_PLUS": 27, "VK_OEM_2": 24, "VK_OEM_5": 42,
}

ACCENT_TO_STATE = {
    0x00B4: "s_acute", 0x00A8: "s_diaeresis", 0x00B0: "s_degree",
    0x02C7: "s_caron", 0x005E: "s_circumflex", 0x02D8: "s_breve",
    0x02DB: "s_ogonek", 0x0060: "s_grave", 0x02D9: "s_dotabove",
    0x02DD: "s_doubleacute", 0x00B8: "s_cedilla",
}
STATE_IDS = list(ACCENT_TO_STATE.values())

KEYPAD = {
    65: ",", 67: "*", 69: "+", 75: "/", 76: "\r", 78: "-", 81: "=",
    82: "0", 83: "1", 84: "2", 85: "3", 86: "4",
    87: "5", 88: "6", 89: "7", 91: "8", 92: "9",
}


# ---------------------------------------------------------------------------
# 2. parse the official Microsoft page
# ---------------------------------------------------------------------------
def parse_official_states():
    text = open(os.path.join(REF, "kbdcz.html"), encoding="iso-8859-1").read()
    divs = [(m.start(), m.group(1))
            for m in re.finditer(r"<DIV ID=([a-z0-9]+) CLASS=", text)]
    divs.append((len(text), "END"))
    states = {}
    for i in range(len(divs) - 1):
        name, seg = divs[i][1], text[divs[i][0]:divs[i + 1][0]]
        rows = []
        for trm in re.finditer(r"<TR>(.*?)</TR>", seg, re.S | re.I):
            cells = []
            for cm in re.finditer(r"<TD><IMG [^>]*?ALT=\"([^\"]*)\"", trm.group(1), re.I):
                alt = ht.unescape(cm.group(1))
                # character keys have ALT "U+XXXX NAME"; special keys start
                # with "Backspace key..." etc. -> None (position placeholder)
                u = re.search(r"U\+([0-9A-Fa-f]{2,6})", alt)
                cells.append(int(u.group(1), 16) if u and alt.startswith("U+") else None)
            if any(c is not None for c in cells):
                rows.append(cells)
        if rows:
            states[name] = rows
    return states


def parse_dead_tables():
    """(state, VK) -> {accent_cp, pairs} from the official DeadKey popups."""
    text = open(os.path.join(REF, "kbdcz.html"), encoding="iso-8859-1").read()
    divs = [(m.start(), m.group(1))
            for m in re.finditer(r"<DIV ID=([a-z0-9]+) CLASS=", text)]
    divs.append((len(text), "END"))

    def state_at(pos):
        st = None
        for s, name in divs:
            if s <= pos:
                st = name
            else:
                break
        return st

    out = {}
    for m in re.finditer(r"popup\('(.*?)'\);", text, re.S):
        pop = ht.unescape(m.group(1))
        if "DeadKey" not in pop:
            continue
        st = state_at(m.start())
        vk = re.search(r"VK_[A-Z0-9_]+", pop).group(0)
        accent = int(re.search(r"U\+([0-9A-Fa-f]{2,6})", pop).group(1), 16)
        pairs = []
        for chunk in pop[pop.find("DeadKey:"):].split("+")[1:]:
            mm = re.match(r"^(\{space\}|\S)\s*=\s*(\S)\s", chunk + " ")
            if not mm:
                continue
            base = " " if mm.group(1).startswith("{space") else mm.group(1)
            pairs.append((base, mm.group(2)))
        out[(st, vk)] = {"accent_cp": accent, "pairs": pairs}
    return out


# ---------------------------------------------------------------------------
# 3. build the keylayout
# ---------------------------------------------------------------------------
def xml_attr(s):
    """escape a value for an XML attribute (numeric refs for C0 controls)."""
    res = []
    for ch in s:
        o = ord(ch)
        if o < 0x20 or o == 0x7F:
            res.append(f"&#x{o:04X};")
        elif ch == "&":
            res.append("&amp;")
        elif ch == "<":
            res.append("&lt;")
        elif ch == ">":
            res.append("&gt;")
        elif ch == '"':
            res.append("&quot;")
        else:
            res.append(ch)
    return "".join(res)


def main():
    states = parse_official_states()
    deads = parse_dead_tables()

    # sanity: official geometry
    for st in ("normallower", "shiftlower", "normalcaps", "shiftcaps",
               "ctrlaltlower", "ctrlaltcaps"):
        lens = [len(r) for r in states[st]]
        assert lens == [14, 14, 13, 13], (st, lens)

    # ---- merged official compose tables, per state id ----
    compose = {sid: {} for sid in STATE_IDS}          # state -> {base: composed}
    for (st, vk), info in deads.items():
        sid = ACCENT_TO_STATE[info["accent_cp"]]
        for base, comp in info["pairs"]:
            compose[sid].setdefault(base, comp)

    # characters that participate in composition -> need <action>
    action_chars = sorted({b for tbl in compose.values() for b in tbl} - {" "})

    # ---- dead-key positions per keyMap ----
    dead_by_index = {}      # map index -> {mac code: state id}
    for (st, vk), info in deads.items():
        if st not in STATE_TO_INDEX:
            continue
        idx = STATE_TO_INDEX[st]
        dead_by_index.setdefault(idx, {})[VK_TO_MAC[vk]] = ACCENT_TO_STATE[info["accent_cp"]]

    # ---- keyMaps ----
    maps = {i: {} for i in range(8)}
    for st, idx in STATE_TO_INDEX.items():
        m = maps[idx]
        for row, codes in enumerate(ROW_CODES):
            for col, code in enumerate(codes):
                if code in MODIFIER_CODES:
                    continue
                cp = states[st][row][col]
                if cp is None:
                    continue
                m[code] = chr(cp)
        # fixed specials
        for code, ch in SPECIAL.items():
            m[code] = ch
        m[49] = " " if idx in (0, 1, 4, 5) else "\u00A0"   # Option+Space = NBSP (KLC)
        m[53] = "\x1b"                                       # Escape
        if idx in (0, 1, 4, 5):                              # keypad (non-AltGr)
            m.update(KEYPAD)

    # indexes 3 & 7 (AltGr+Shift / Caps+AltGr+Shift): the official page renders
    # ONLY Backspace, Tab and Enter in that state — every character key is
    # "Blank key." Keep exactly those (DTD also requires >=1 key per keyMap).
    for idx in (3, 7):
        maps[idx] = {51: "\x08", 48: "\x09", 36: "\r", 53: "\x1b"}

    # ---- XML ----
    def key_el(code, map_index):
        if code in dead_by_index.get(map_index, {}):
            sid = dead_by_index[map_index][code]
            return f'<key code="{code}" action="dead_{sid}"/>'
        ch = maps[map_index][code]
        if ch in action_chars:
            return f'<key code="{code}" action="k{ord(ch):04X}"/>'
        if ch in (" ", "\u00A0") and map_index in (0, 1, 4, 5):
            return f'<key code="{code}" action="spc"/>'
        if ch == "\u00A0":
            return f'<key code="{code}" action="spc_nbsp"/>'
        return f'<key code="{code}" output="{xml_attr(ch)}"/>'

    lines = []
    lines.append('<?xml version="1.1" encoding="UTF-8"?>')
    lines.append('<!DOCTYPE keyboard SYSTEM "file://localhost/System/Library/DTDs/KeyboardLayout.dtd">')
    lines.append(f'<!-- {LAYOUT_NAME}: exact replica of Windows "Czech" keyboard layout')
    lines.append('     (KLID 00000405) built from official Microsoft kbdcz data.')
    lines.append('     Generated by keyboard/make_czech_windows_layout.py -->')
    lines.append(f'<keyboard group="{GROUP}" id="{LAYOUT_ID}" name="{LAYOUT_NAME}" maxout="1">')
    lines.append('  <layouts>')
    for first, last in [(0, 17), (18, 18), (21, 23), (30, 30),
                        (194, 194), (197, 197), (200, 201), (206, 207)]:
        lines.append(f'    <layout first="{first}" last="{last}" mapSet="csm" modifiers="mods"/>')
    lines.append('  </layouts>')
    lines.append('  <modifierMap id="mods" defaultIndex="0">')
    for map_index, keys in [
        (7, "caps anyShift anyOption anyControl?"),
        (3, "anyShift anyOption anyControl?"),
        (6, "caps anyOption anyControl?"),
        (2, "anyOption anyControl?"),
        (5, "caps anyShift"),
        (1, "anyShift caps?"),
        (4, "caps"),
        (0, "command?"),
        (1, "anyShift caps? command"),
        (0, "anyControl anyShift? caps?"),
    ]:
        lines.append(f'    <keyMapSelect mapIndex="{map_index}">')
        lines.append(f'      <modifier keys="{keys}"/>')
        lines.append('    </keyMapSelect>')
    lines.append('  </modifierMap>')
    lines.append('  <keyMapSet id="csm">')
    for idx in range(8):
        lines.append(f'    <keyMap index="{idx}">')
        for code in sorted(maps[idx]):
            lines.append("      " + key_el(code, idx))
        lines.append('    </keyMap>')
    lines.append('  </keyMapSet>')

    # actions: dead keys, letter compositions, space
    lines.append('  <actions>')
    for sid in STATE_IDS:
        lines.append(f'    <action id="dead_{sid}">')
        lines.append(f'      <when state="none" next="{sid}"/>')
        lines.append('    </action>')
    for ch in action_chars:
        lines.append(f'    <action id="k{ord(ch):04X}">')
        lines.append(f'      <when state="none" output="{xml_attr(ch)}"/>')
        for sid in STATE_IDS:
            comp = compose[sid].get(ch)
            if comp:
                lines.append(f'      <when state="{sid}" output="{xml_attr(comp)}"/>')
        lines.append('    </action>')
    for aid, none_out in (("spc", " "), ("spc_nbsp", "\u00A0")):
        lines.append(f'    <action id="{aid}">')
        lines.append(f'      <when state="none" output="{xml_attr(none_out)}"/>')
        for sid in STATE_IDS:
            comp = compose[sid].get(" ")
            if comp:
                lines.append(f'      <when state="{sid}" output="{xml_attr(comp)}"/>')
        lines.append('    </action>')
    lines.append('  </actions>')

    lines.append('  <terminators>')
    seen = set()
    for (st, vk), info in deads.items():
        sid = ACCENT_TO_STATE[info["accent_cp"]]
        if sid in seen:
            continue
        seen.add(sid)
        lines.append(f'    <when state="{sid}" output="{xml_attr(chr(info["accent_cp"]))}"/>')
    lines.append('  </terminators>')
    lines.append('</keyboard>')

    out_path = os.path.abspath(OUT)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("written:", out_path)

    # ---- self-check against the official tables ----
    checks = [
        (0, 50, ";"), (0, 18, "+"), (0, 21, "č"), (0, 16, "z"), (0, 6, "y"),
        (0, 41, "ů"), (0, 39, "§"), (0, 42, "\u00a8"), (0, 24, "\u00b4"),
        (0, 27, "="), (0, 33, "ú"), (0, 30, ")"), (0, 44, "-"),
        (1, 18, "1"), (1, 50, "\u00b0"), (1, 27, "%"), (1, 24, "\u02c7"),
        (1, 44, "_"), (1, 43, "?"), (1, 41, '"'), (1, 39, "!"),
        (1, 33, "/"), (1, 30, "("), (1, 42, "'"), (1, 6, "Y"), (1, 16, "Z"),
        (2, 18, "~"), (2, 1, "đ"), (2, 2, "Đ"), (2, 40, "ł"), (2, 37, "Ł"),
        (2, 41, "$"), (2, 39, "ß"), (2, 33, "÷"), (2, 30, "×"), (2, 42, "¤"),
        (2, 7, "#"), (2, 8, "&"), (2, 9, "@"), (2, 11, "{"), (2, 45, "}"),
        (2, 43, "<"), (2, 47, ">"), (2, 44, "*"), (2, 14, "€"),
        (2, 12, "\\"), (2, 13, "|"), (2, 3, "["), (2, 5, "]"),
        (4, 21, "Č"), (4, 6, "Y"), (4, 33, "Ú"), (4, 39, "§"),
        (5, 17, "t"), (5, 41, '"'), (5, 21, "4"),
    ]
    for idx, code, expect in checks:
        got = maps[idx].get(code)
        assert got == expect, f"map{idx} code{code}: got {got!r} want {expect!r}"
    # AltGr must be EMPTY on these (official "Blank key.")
    for idx in (2, 6):
        for code in (15, 17, 16, 32, 34, 31, 35, 0, 4, 38, 46, 10, 6, 50):
            assert code not in maps[idx], f"map{idx} code{code} should be blank, got {maps[idx][code]!r}"
    assert set(maps[3]) == {36, 48, 51, 53} and set(maps[7]) == {36, 48, 51, 53}, \
        "AltGr+Shift maps must contain only Backspace/Tab/Enter/Esc (official: all blank)"
    # dead positions
    assert dead_by_index[0] == {24: "s_acute", 42: "s_diaeresis"}, dead_by_index[0]
    assert dead_by_index[1] == {24: "s_caron", 50: "s_degree"}, dead_by_index[1]
    assert dead_by_index[2][19] == "s_caron" and dead_by_index[2][24] == "s_cedilla"
    assert len(dead_by_index[2]) == 11, dead_by_index[2]

    # XML well-formed (handle XML1.1 control refs like the dumper does)
    raw = open(out_path, encoding="utf-8").read()
    raw2 = re.sub(r"&#(x[0-9A-Fa-f]+|\d+);",
                  lambda m: (lambda v: f"CTRL-U+{v:04X}" if v < 0x20 and v not in (9, 10, 13) else m.group(0))(
                      int(m.group(1)[1:], 16) if m.group(1).lower().startswith("x") else int(m.group(1))),
                  raw)
    ET.fromstring(raw2)
    print(f"OK: {len(action_chars)} composing letters, "
          f"{len([1 for i in maps for c in maps[i]])} key entries, XML valid")
    print("states parsed:", sorted(states), "| dead tables:", len(deads))


if __name__ == "__main__":
    main()
