# Third-party notices

glra-osc is licensed GPL-3.0-only (see `LICENSE`).

## glra-studio

`glra_osc/device/` contains code copied from
[glra-studio](https://github.com/imolitor/glra-studio) (GPL-3.0-only),
Copyright (c) 2026 GLRA Studio contributors, taken at commit `33aa281`. The
files keep their SPDX and copyright headers. See `glra_osc/device/README.md` for
the file list. `lighting.py` (the factory lighting payload checks and guarded write)
was added on 2026-11-13 from the same commit.

## Dependencies

Dependencies keep their own licences.

| Component | Version | Upstream |
|---|---|---|
| cython-hidapi (`hidapi`) | 0.15.0 | https://github.com/trezor/cython-hidapi |
| HIDAPI | bundled by cython-hidapi | https://github.com/libusb/hidapi#license |
| rtmidi2 | >=1.5.0 | https://github.com/gesellkammer/rtmidi2 |
| RtMidi | bundled by rtmidi2 | https://github.com/thestk/rtmidi |

glra-osc is an independent community project, not an official product of
G-LRA or Apple. Device names identify compatibility.
