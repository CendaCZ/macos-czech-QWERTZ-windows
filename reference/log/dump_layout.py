#!/usr/bin/env python3
"""Dump a macOS .keylayout file as readable tables (resolving dead-key actions)."""
import re
import sys
import xml.etree.ElementTree as ET

# ANSI physical key labels by macOS virtual key code (HIToolbox Events.h kVK_*)
KEYNAME = {
    "50": "grave/tilde (left of 1)",
    "18": "1", "19": "2", "20": "3", "21": "4", "23": "5", "22": "6",
    "26": "7", "28": "8", "25": "9", "29": "0", "27": "minus (-_)", "24": "equal (=+)",
    "12": "Q", "13": "W", "14": "E", "15": "R", "17": "T", "16": "Y",
    "0": "A", "1": "S", "2": "D", "3": "F", "5": "G", "4": "H",
    "38": "J", "40": "K", "37": "L", "41": "semicolon (;:)", "39": "quote ('\")",
    "6": "Z", "7": "X", "8": "C", "9": "V", "11": "B", "45": "N", "46": "M",
    "43": "comma (,<)", "47": "period (.>)", "44": "slash (/?)", "42": "backslash (\\|)",
    "32": "U", "33": "leftBracket ([)", "31": "O", "34": "I", "35": "P", "30": "rightBracket (])",
    "10": "ISO § (next to LShift)", "49": "space", "36": "return", "48": "tab",
    "51": "delete", "123": "left", "124": "right", "125": "down", "126": "up",
}
ROW = ["10", "50",
       "18", "19", "20", "21", "23", "22", "26", "28", "25", "29", "27", "24",
       "12", "13", "14", "15", "17", "16",
       "0", "1", "2", "3", "5", "4", "38", "40", "37", "41", "39",
       "6", "7", "8", "9", "11", "45", "46", "43", "47", "44", "42",
       "32", "33", "31", "34", "35", "30",
       "49", "36", "48"]


def load_root(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()

    def repl(m):
        raw = m.group(1)
        v = int(raw[1:], 16) if raw.lower().startswith("x") else int(raw)
        if v < 0x20 and v not in (0x09, 0x0A, 0x0D):
            return f"CTRL-U+{v:04X}"
        return m.group(0)

    text = re.sub(r"&#(x[0-9A-Fa-f]+|\d+);", repl, text)
    return ET.fromstring(text)


def main(path):
    root = load_root(path)
    print(f"file: {path}")
    print(f"name={root.get('name')!r} id={root.get('id')} group={root.get('group')} maxout={root.get('maxout')}")

    actions = {}
    if root.find("actions") is not None:
        for a in root.find("actions"):
            actions[a.get("id")] = [(w.get("state"), w.get("next"), w.get("output")) for w in a]

    def resolve(el, state="none"):
        if el.get("output") is not None:
            return el.get("output"), ""
        aid = el.get("action")
        if aid is None:
            return "", ""
        states = actions.get(aid, [])
        out, nxt = None, None
        for st, n, o in states:
            if st == state:
                out, nxt = o, n
                break
        if out is None:
            for st, n, o in states:
                if st == "none":
                    out, nxt = o, n
                    break
        txt = out if out is not None else f"<action '{aid}' (dead)>"
        notes = []
        if nxt:
            notes.append(f"DEAD -> state {nxt}")
        others = [f"{st}{'->'+n if n else ''}{':'+o if o else ''}"
                  for st, n, o in states if st != state and o is not None or (st != state and n)]
        if others:
            notes.append("states: " + ", ".join(others))
        return txt, ("   [" + "; ".join(notes) + "]" if notes else "")

    mods = {}
    for mm in root.findall("modifierMap"):
        mods[mm.get("id")] = {sel.get("mapIndex"): [m.get("keys") for m in sel] for sel in mm}
    print("\nmodifier maps:")
    for mm in root.findall("modifierMap"):
        print(f"  modifierMap id={mm.get('id')}:")
        for i, keys in sorted(mods[mm.get("id")].items(), key=lambda x: int(x[0])):
            print(f"    index {i}: {keys}")

    kss = root.find("keyMapSets")
    if kss is None:
        kss_els = root.findall("keyMapSet")
    else:
        kss_els = list(kss)
    first_mapset = root.find("layouts/layout").get("mapSet")
    print(f"\nmapSets: {[ks.get('id') for ks in kss_els]} — showing '{first_mapset}'")
    for ks in kss_els:
        if ks.get("id") != first_mapset:
            continue
        for km in ks:
            print(f"\n=== keyMap index {km.get('index')} ===")
            keys = {k.get("code"): k for k in km}
            seen = set()
            for code in ROW:
                el = keys.get(code)
                if el is None:
                    continue
                seen.add(code)
                txt, note = resolve(el)
                print(f"  {KEYNAME.get(code, code):26s} ({code:>3s}): {txt!r}{note}")
            for code, el in sorted(keys.items(), key=lambda x: int(x[0])):
                if code in seen:
                    continue
                txt, note = resolve(el)
                print(f"  {f'[other code {code}]':26s}      : {txt!r}{note}")


if __name__ == "__main__":
    main(sys.argv[1])
