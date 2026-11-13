# fix-lighting-readback — firmware 103 normalises bytes the app compares

Bob, 2026-11-13, tour 3.3: after the first change (which read back fine), later
Applies report "Written to the pad, but it did not read back as expected",
also Breathing with a colour, then Custom, then Lit on press. "the lighting
modes do seem to be setting correctly". Screenshots in `../evidence/`.

The bytes (payload `[1,0,mode,bright,speed,dir,flag,byte7,h,s,v]`):

- Flow (columns), one colour off: expected `…03 00 08 aa ff ff`, after
  `…03 00 08 ff ff ff`. With the flag off the pad reset hue `aa` → `ff`.
- Breathing, one colour on, h215: expected `…03 01 08 d7 ff ff`, after
  `…03 01 ff d7 ff ff`. With the flag on the pad set byte 7 `08` → `ff`.

Claude's reading (2026-11-13, from these two captures only): the write worked;
the readback check compares bytes firmware 103 rewrites. Fix: compare mode,
brightness and speed (where the mode reads them), the flag, and HSV only when
the flag is on; ignore byte 7 and HSV with the flag off; still show any other
difference. This also answers review finding 2 (per-mode HSV not kept with the
flag off). Add both captures as test fixtures. Record byte 7's behaviour in
`glean:k16n3-lighting`. Check with Bob at the pad: the same sequence shows
"Applied and read back."
