# Czech (Windows original) — macOS keyboard layout

An exact macOS replica of the **original Windows "Czech" keyboard layout**
(KLID `00000405`, the regular/default one — QWERTZ, digits behind Shift).

Built from **official Microsoft data**: the interactive layout page
<https://learn.microsoft.com/en-us/globalization/keyboards/kbdcz> (every
modifier state + the official dead-key tables), cross-checked against the
MSKLC-format source in `reference/czech_source_utf8.klc` and the Wikipedia
*Windows Czech keyboard layout* SVG in `reference/win_cz.svg`.

- **File:** `../Czech (Windows original).keylayout` (project root)
- Plain `.keylayout` XML — **no binaries, no code signing, works as-is on
  Apple Silicon** (and any Mac). DTD-validated against
  `/System/Library/DTDs/KeyboardLayout.dtd`.
- Layout id `-30105` (no collision with the installed ones: 4711 / −21957 / −9364 / −14193).

## Install (Apple Silicon)

```sh
# per-user (no sudo needed):
mkdir -p ~/Library/"Keyboard Layouts"
cp "Czech (Windows original).keylayout" ~/Library/"Keyboard Layouts"/
```

…or system-wide for all accounts (admin password):

```sh
sudo cp "Czech (Windows original).keylayout" /Library/"Keyboard Layouts"/
```

Then:

1. **Log out and log back in** (or restart) — macOS only scans the keyboard-layout
   folders at login.
2. System Settings → **Keyboard** → **Input Sources…** → **+** → **Others** →
   *Czech (Windows original)* → Add.
3. Switch to it with the input-menu (globe/flag) icon.

> The old custom layouts (`Czech PC`, `czech_windows`) can stay installed while
> you compare. To remove them later:
> `sudo rm /Library/"Keyboard Layouts"/Czech_PC.keylayout /Library/"Keyboard Layouts"/czech_windows.keylayout`
> then log out/in again.

## Typing the basics (identical to original Windows Czech)

| | |
|---|---|
| **`;` semicolon** | key **left of `1`** (the `` ` ``/`~` key on a US board) — no Shift |
| **`°` degree** | that key held with Shift, **then Space** (it is a dead key, exactly like Windows) |
| **digits** | behind **Shift** (`1`…`0` on the number row are ě š č ř ž ý á í é keys) |
| **`+`** | key `1` (unshifted) |
| **`=` / `%`** | key right of `0` / Shift on it |
| **dead acute `´` / dead caron `ˇ`** | the two keys right of `=` (i.e. US `-` and `=` positions), Shift on the second one |
| **`ů ů"`** | US `;` key → `ů`, Shift → `"` |
| **`§ !`** | US `'` key → `§`, Shift → `!` |
| **`/`** | Shift + US `[` key (also the only place for `/` — like Windows) |
| **`-` `_` `*`** | US `/?` key (base / Shift / Option) |
| **`Q W E R T Z`** | QWERTZ: `Z` types on the US-`Y` key, `Y` on the US-`Z` key |
| **AltGr characters** | **Option (⌥) = AltGr**, right Option also works; Option+Shift is blank, exactly like Windows |

### AltGr (Option) table — official

```
AltGr+1..0 : ~  ˇ  ˆ  ˘  °  ˛  `  ˙  ´  ˝      (2..0 are DEAD accents)
AltGr+'-' key = dead ¨   ·   AltGr+'=' key = dead ¸   (the two keys right of `0`)
Q \    W |    E €    [ ú ] ÷   ) ×   \ ¤
S đ    D Đ    F [    G ]   K ł   L Ł   ů $   § ß
X #    C &    V @    B {   N }   , <   . >   - *
R T Y U I O P A H J M and LSGT: no AltGr character (official "Blank key.")
```

Dead-key compositions are the **official Windows tables** (space composes the
accent itself; e.g. dead caron + `n` → `ň`, dead acute + `z` → `ź`,
dead degree + `u` → `ů`, dead dot above + space → `·`).

## What was wrong in the previous custom layouts

Compared with the official Windows `kbdcz` data:

| | Czech PC (was active) | czech_windows | Windows original (new) |
|---|---|---|---|
| base + Shift rows, QWERTZ, digits-on-Shift | ✓ correct | `;` on ISO key, `\` on `` ` `` key ✗ | ✓ |
| **AltGr digit row** | US symbols `! @ # $ …` ✗ | merged Option+Shift ✗ | dead accents `ˇ ˆ ˘ ° ˛ ` ˙ ´ ˝` + `~` ✓ |
| **AltGr letters đ Đ ł Ł** | missing ✗ | missing ✗ | ✓ |
| AltGr `¤` on `\` key | missing ✗ | ✓ | ✓ |
| Option+Shift (AltGr+Shift) | partial junk (`±`) ✗ | same as Option ✗ | blank, like Windows ✓ |
| ISO key next to Left Shift | `§`/`±` ✗ | `;` ✗ | `\` / `\|` ✓ |
| dead-key tables | shortened | — | official MS tables (25-pair acute, cedilla, ogonek, …) ✓ |
| AltGr `R T M A H J` etc. | empty ✓ | — | empty ✓ (official has no ®/™/µ — the KLC variant added those) |

## Rebuild

```sh
python3 keyboard/make_czech_windows_layout.py   # regenerates the .keylayout from reference/kbdcz.html
python3 keyboard/dump_layout.py "Czech (Windows original).keylayout"   # human-readable dump
```

The generator re-parses the official Microsoft page and asserts every key of
every state against it (49 spot checks + blank-key checks + dead positions),
so the output cannot drift from the official layout.

## Want the other official Windows variants?

Microsoft ships two more (also parsed-ready in `reference/kbdcz.html`'s
siblings): **Czech (QWERTY)** `kbdcz1` (KLID 00010405) and **Czech
Programmers** `kbdcz2` (KLID 00020405). Say the word and the generator can be
pointed at those pages too.
