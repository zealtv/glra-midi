# Outside chip-ID lead: ZXW / Masses Chip M9F9520 (another agent's report, 2026-11-13)

A research report another AI agent produced from the search terms in
`loom:firmware-approaches`; Bob pasted it into the glra-osc session on
2026-11-13. Kept whole in `content/report.md`, with its links as pasted
(they carry `utm_source=chatgpt.com`). Only the favicon-image lines and empty footnote markers were dropped; source domains they named appear as "(cited: …)".

## Source

Bob, pasting into the Claude Code session, 2026-11-13: "from another agent:".
The agent isn't named beyond that.

## Claude's spot checks (2026-11-13)

- **Reproduced:** `https://zxw-chip.com/article/7` lists `M9F9520`: 2.2–5.5 V,
  RAM 2216, ROM 32K (no units given), IRC/XTAL 24M, 44 IO, 2 UART / 2 SPI /
  2 I2C, full-speed USB, 3 timers, "8/6路WS2812" in the PWM column,
  LQFP48/QFN48. Siblings on the same page: `M9F9800` (680 / 16K, LQFP48,
  WS2812) and `M9F951` (2295 / 32K, ADC, 23+3 PWM, LQFP48/64).
- **Not reproduced:** `www.masses-chip.com` failed with an expired TLS
  certificate; web searches for `磐芯 M9F9520`, `5566:0008 ZXWMicroChip` and
  `ZXWM9F9800` found nothing; the Debian bug and CNIPA layout-registration
  claims weren't checked further.
- **Corroboration from our own notes:** the vendor updater's `951` and `9520`
  `mcu_type` names line up with ZXW's `M9F951` and `M9F9520`
  (`glean:sdcx-prior-art`, `glean:k16n3-firmware-replacement`).

## Tags

- hardware
- mcu
- firmware
- chip-identification
