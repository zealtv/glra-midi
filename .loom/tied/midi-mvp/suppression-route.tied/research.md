# Research: suppressing a USB macropad's keystrokes on macOS 14.6 (web research, 2026-11-12)

Labels: **documented** = vendor/author text, **reported** = reported by users, **inferred** = my reading. Web research only; nothing was run on a device. Several searches returned thin results, and I flag each gap.

## 1. Seizing keyboard-class HID devices

- Seizing needs root. **Documented** (Karabiner dev notes): the grabber (now Karabiner-Core-Service) runs as root, "required to seize the device and send events to the virtual driver". https://github.com/pqrs-org/Karabiner-Elements/blob/main/DEVELOPMENT.md (via search summary; I did not read the page itself).
- **Reported:** KMonad's macOS seize call fails with a not-privileged error without root. https://hackage-content-origin.haskell.org/package/kmonad-0.4.1/candidate/src/c_src/mac/keyio_mac.cpp
- Your 0xe00002c1 matches kIOReturnNotPrivileged. **Inferred:** a plain root check fits your observation that Input Monitoring alone does not help.
- **Not found:** no Apple document stating "keyboard seize is root-only on 10.15+". I found no entitlement, TCC service or DriverKit route that lets a non-root process seize a keyboard. **Inferred** only.
- Root is not sufficient in every setup. An Apple forum thread reports a root `SMAppService` daemon getting `kIOReturnNotPermitted` on seize, while an `SMJobBless` helper worked. Apple's Quinn suspected TCC and gave no resolution. https://developer.apple.com/forums/thread/795686 (**reported**)
- Karabiner design: **documented** that its DriverKit virtual HID devices accept commands only from root processes. https://github.com/pqrs-org/Karabiner-DriverKit-VirtualHIDDevice
- Karabiner's current manual lists Input Monitoring (needed for 15.9 and earlier; Accessibility covers it from 16.0). https://karabiner-elements.pqrs.org/docs/manual/misc/required-macos-settings/ (**documented**)
- Process names may differ by version. One unofficial page says v15 moved the grabber into SMAppService app bundles. https://project-notes-4iy.pages.dev/_archive/wispr-mouse-button/2026-04-29-session-findings.html (**reported**, single source).
- Seize inside a DriverKit dext was reported not to hide the device from IOHIDManager (Karabiner 14.3, macOS 12). https://gist.github.com/akemin-dayo/0e7291b85efc107427b5b12e6d6608bd (**reported**)
- Why vendor-interface seize works: **inferred** that the keyboard path is gated and other usage pages are not. An Apple forum responder said Input Monitoring covers "anything the system directly understands" (keyboards, mice). https://developer.apple.com/forums/thread/804793 (**reported**, paraphrased by a search summary).

## 2. `hidutil` UserKeyMapping

- Format: values are `(usagePage << 32) | usageID`, keyboard page is 0x700000000. Apple's TN2450 shows `HIDKeyboardModifierMappingSrc` and `HIDKeyboardModifierMappingDst`. https://developer.apple.com/library/archive/technotes/tn2450/_index.html (**documented**)
- **No documented no-op destination.** TN2450 gives none. I found no source confirming that 0x700000000, 0x0 or 0x7000000FF produces no event. Test these empirically.
- One user swallowed all keys on a Keychron K8 with `"Dst": 0x70000007E` and matching by `"Product":"Keychron K8"`. https://forum.keyboardmaestro.com/t/using-hidutil-to-remap-keyboard/27014 (**reported**). The page does not say why that value works.
- **Inferred** guess: 0x70000007E sits in an unassigned or rarely handled stretch of the keyboard page. I could not verify what usage it names. Check the HID Usage Tables.
- Layer: a nanoANT article says the remap happens in `IOHIDKeyboardFilter::remapKey`, in IOHIDFamily's keyboard filter. https://www.nanoant.com/mac/macos-function-key-remapping-with-hidutil (**reported**). **Inferred:** a non-exclusive reader still gets the raw reports. No source confirms this for hidapi, so test it.
- Persistence: **documented** (TN2450) that mappings are lost on restart or when the keyboard service is removed (e.g. last keyboard disconnected). Whether a per-device match survives replug of one device is **not documented**. Plan on a LaunchAgent that reapplies it.
- Scope: **documented** (TN2450) as applying to all users, with no special privileges.
- Version problems: users reported `hidutil` stopped working after macOS 14.2, with some needing root, and macOS 15 reportedly needing Input Monitoring for hidutil/Terminal. https://discussions.apple.com/thread/255340598 and https://openradar.appspot.com/FB13465290 (**reported**). **Inferred:** verify on 14.6 with `hidutil property --get UserKeyMapping`.
- Consumer page (0x0C): **not found.** I found no source on usage page 0x0C inside UserKeyMapping. Volume keys may stay unaffected. Test.

## 3. TCC for non-exclusive input-report reads

- **Reported** (Apple forum, summarised): `IOHIDDeviceRegisterInputReportCallback` never fired without Input Monitoring on keyboards. https://developer.apple.com/forums/thread/804793
- **Reported:** `IOHIDManagerCopyDevices`/open on keyboards triggers the Input Monitoring prompt on 10.15. https://developer.apple.com/forums/thread/124368 (the thread has no Apple reply).
- TCC grant is tied to the binary that opens the device. That claim comes from an unofficial AI-generated write-up, so treat it as weak. https://instagit.com/AprilNEA/OpenLogi/request-manage-macos-input-monitoring-permissions.md
- `IOHIDCheckAccess` reportedly returns denied even after a grant. https://developer.apple.com/forums/thread/809431 (**reported**)
- Root launchd daemon: **not found.** The root/system TCC database is separate from the user's, per Quinn at https://developer.apple.com/forums/thread/795686 (**reported**). **Inferred:** a daemon may need its own grant, and can't get one through the UI easily. Test.

## 4. python-rtmidi on macOS

- Latest release 1.5.8 (2023-11-20). Wheels cover cp38–cp312 only, with macOS arm64 for 3.8–3.12. **No cp313 or cp314 wheels** as of the PyPI page I fetched. https://pypi.org/project/python-rtmidi/ (**documented**)
- **Inferred:** on Python 3.13/3.14, pip builds from the sdist, which needs Xcode command line tools. A gist shows a failed source build of 1.4.9 on arm64. https://gist.github.com/tedthetrumpet/dc16a8d40aa6ddc7ce4bfcbdacbace85 (**reported**)
- `open_virtual_port` exists on `MidiOut`. https://spotlightkid.github.io/python-rtmidi/rtmidi.html (**documented**). I found no 3.13-specific gotcha beyond the missing wheel.
- Alternatives: `rtmidi2` has a cp313 macOS arm64 wheel and `open_virtual_port` (https://pypi.org/project/rtmidi2/, **documented**); `supriya-midi` (nanobind RtMidi binding) targets 3.13+ wheels (https://pypi.org/project/supriya-midi/, **reported** by its author). `mido` can use either as a backend; I did not check that.
- Simplest fallback, **inferred**: run the tool under Python 3.12, which has wheels.

## 5. Relative CC encodings

- Two's complement: 1 = +1, 127 = −1. https://www.cantabilesoftware.com/guides/controllerEncoding (**documented**)
- Binary offset: 64 = zero, 65 = +1, 63 = −1. https://manual.ardour.org/using-control-surfaces/generic-midi/working-with-encoders/ (**documented**)
- Signed bit (sign-magnitude): 1–63 positive, 65–127 negative or the reverse, depending on the product. Logic lists 1 = +1 and 65 = −1; one Ableton forum post says 65 increments and 1 decrements. https://support.apple.com/kn-in/guide/logicpro-ipad/lpip9f6084ee/ipados and https://forum.ableton.com/viewtopic.php?p=1365002 (**reported**). Ableton's "signed bit" sign convention is unverified.
- **Ableton Live:** **reported** that it offers signed bit, signed bit 2, binary offset and 2's complement. https://forum.ableton.com/viewtopic.php?p=1365002 and https://forum.arturia.com/t/minilab-mk3-relative-mode-ableton-still-not-working/1270/20. I found no official Ableton page.
- **Bitwig:** the official user guide page I fetched does not mention relative modes. https://www.bitwig.com/userguide/latest/midi_controllers One KVR user switched a mapping to "Relative 2's complement" manually and got it working; "Bin Offset" worked for no one in that thread. https://www.kvraudio.com/forum/viewtopic.php?t=488163 (**reported**, older Bitwig version). A different user recommended "Relative (Bin offset)" for LED-ring encoders. https://www.kvraudio.com/forum/viewtopic.php?p=7178872 (**reported**, loosely matched).
- **Inferred:** two's complement has the best evidence on both DAWs. Check what each DAW's mapping panel lists.

## Gaps to test

1. Which Dst value yields no event. Try 0x70000007E and the others, using `--matching` on VID/PID.
2. Whether hidapi still sees raw reports under the mapping.
3. Replug behaviour for a per-device mapping.
4. Whether usage page 0x0C works in UserKeyMapping.
5. Whether a root daemon needs its own Input Monitoring grant.
