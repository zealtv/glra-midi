# SPDX-License-Identifier: GPL-3.0-only

"""The app's model: a `Controller(QObject)` over a `profile.Profile` (docs/config-app.md 4.1).

The profile lives here, in Python. QML draws what `ui` properties hold and calls the slots
below; it keeps no profile logic and no summary text. The controller touches no device.

Files (design 4.8): the profile opens from `profile.current_profile_path()`; Open and Save As
work inside the profiles folder and call `set_current`, so `glra-midi run` follows. A change
to the open file, or to `current`, on disk reloads (no unsaved edits) or raises a
"changed on disk" notice (unsaved edits). `poll()` does that check; `poll_ms` > 0 runs it on a
timer.

The device panel (design 4.10, 5): its fields edit the profile like any other. The controller
holds a *pad object* (`device.py`) and opens no device itself; with none given it uses `NoPad`
("Pad: not found", no I/O at all). Pad reads and the one lighting write run on a worker thread
(`padworker.py`). The only call that can write to the pad is `applyLighting`, which QML calls
from the [Apply to pad] button; no edit, save, open or start-up path calls it. Prompts are two signals the window answers: `unsavedPrompt` (Save / Don't save /
Cancel, answered by `resolveUnsaved`) and `confirmPrompt` (Yes / No, `resolveConfirm`).
"""

import re
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from .. import orientation as orient
from .. import profile as prof
from ..lighting import MODE_BY_NUMBER
from . import devicepanel as dev
from . import inspector as insp
from .device import NoPad, PadReading, describe_reading, not_found
from .padworker import PadWorker
from .summary import tile_info

_HEADER_LINES = {line for line in prof.HEADER.splitlines() if line}
_LAYER_IN_PATH = re.compile(r"\.layers\.(\d+)")


def has_comments(text):
    """True when `text` holds a TOML comment line other than the header the app writes itself.
    (A saved file loses its comments: tomli-w writes none, design 2.8.)"""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and stripped not in _HEADER_LINES:
            return True
    return False


def _stamp(path):
    """`(mtime_ns, size, inode)` of a file, or None when it can't be read."""
    try:
        st = Path(path).stat()
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size, st.st_ino)


def _plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


class Controller(QObject):
    changed = Signal()
    unsavedPrompt = Signal(str)  # message; the window answers with resolveUnsaved
    confirmPrompt = Signal(str, str)  # title, message; answered with resolveConfirm
    quitApproved = Signal()

    APPLY_COOLDOWN_MS = 1000  # the button stays off this long after a write (design 5.3)

    def __init__(
        self,
        home=None,
        poll_ms=0,
        scheme="system",
        parent=None,
        pad=None,
        read_on_start=True,
        cooldown_ms=APPLY_COOLDOWN_MS,
    ):
        super().__init__(parent)
        self._scheme = scheme
        self._home = home
        self._pad = NoPad() if pad is None else pad
        self._worker = PadWorker(self)
        self._worker.done.connect(self._pad_done)
        self._cooldown_ms = cooldown_ms
        self._pad_connected = False
        self._pad_headline = "Pad: not found" if isinstance(self._pad, NoPad) else "Pad: checking…"
        self._pad_now = ""
        self._pad_busy = False  # a read or the Apply write is running
        self._cooling = False
        self._applying = False  # the one pad write is running; the window must not close now
        self._quit_waiting = False  # a quit was asked for while that write ran
        self._last = ""  # the Apply result line
        self._last_kind = ""  # "ok" | "info" | "warn" | "err"
        self._port_draft = None  # (text, error) while the port field holds something invalid
        self._after = None  # what to do once the unsaved-changes prompt is answered
        self._confirmed = None  # what to do on "yes" to a confirmPrompt
        self._error = ""
        self._notice = ""
        self._disk_message = ""
        self._warned = set()  # files already warned about for comments
        self._load_error = ""
        self._tab = 1  # starts on layer 1; 0 is the Global tab
        self._selected = ""
        self._drafts = {}  # typed field text not (yet) in the profile: key -> (text, error)
        self._draft_for = None  # the (control, tab) the drafts belong to
        self._note_names = True
        self._path = prof.current_profile_path(home)
        self._profile = prof.Profile()
        self._baseline = self._profile
        self._file_stamp = None
        self._current_stamp = None
        self._load(self._path, startup=True)
        self._ui = {}
        self._refresh()
        self._timer = None
        if read_on_start and not isinstance(self._pad, NoPad):
            self.refreshPad()
        if poll_ms > 0:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self.poll)
            self._timer.start(poll_ms)

    # --- reading and writing the file ----------------------------------------------------

    @property
    def profile(self):
        return self._profile

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._path.stem

    @property
    def is_dirty(self):
        """Unsaved edits: the profile differs from the file, or the port field holds a draft
        the profile refused (it stays in the field, so quitting must ask)."""
        return self._profile != self._baseline or self._port_draft is not None

    def _current_file(self):
        return prof.app_dir(self._home) / prof.CURRENT_FILE_NAME

    def _record_stamps(self):
        self._file_stamp = _stamp(self._path)
        self._current_stamp = _stamp(self._current_file())

    def _load(self, path, startup=False):
        """Read `path` into the app. On failure keep what is open and say why; at start-up
        (nothing open yet) show an empty profile and block Save so the broken file stays."""
        try:
            text = Path(path).read_text(encoding="utf-8")
            loaded = prof.parse_profile(text, source=str(path))
        except (OSError, UnicodeDecodeError, prof.ProfileError) as err:
            self._error = f"Can't open {Path(path).stem}: {err}"
            if startup:
                self._path = Path(path)
                self._load_error = self._error
            self._record_stamps()
            return False
        self._path = Path(path)
        self._profile = self._baseline = loaded
        self._port_draft = None
        self._load_error = ""
        self._error = ""
        self._disk_message = ""
        self._notice = ""
        if has_comments(text) and str(self._path) not in self._warned:
            self._warned.add(str(self._path))
            self._notice = (
                f"{self.name}.toml has comments. Saving from the app writes it without them."
            )
        self._tab = min(self._tab, loaded.layer_count)
        self._record_stamps()
        return True

    def _save_to(self, path, allow_broken=False):
        """Write the profile to `path`. A start-up read failure blocks plain Save (it would
        overwrite the broken file); Save As passes `allow_broken` since it names another file."""
        problems = prof.validate(self._profile)
        if self._port_draft is not None:
            # The field shows something the profile refused; saving would write the old port
            # under a field that says otherwise.
            self._error = f"Fix the MIDI port before saving: {self._port_draft[1]}"
            self._refresh()
            return False
        if problems or (self._load_error and not allow_broken):
            self._error = self._load_error or (
                f"Fix {_plural(len(problems), 'problem')} before saving: "
                f"{self._display_message(problems[0])}"
            )
            self._refresh()
            return False
        try:
            prof.dump_profile(self._profile, path)
        except (OSError, prof.ProfileError) as err:
            self._error = f"Can't save {Path(path).stem}: {err}"
            self._refresh()
            return False
        self._path = Path(path)
        self._baseline = self._profile
        self._error = ""
        self._disk_message = ""
        self._warned.add(str(self._path))
        self._notice = ""
        self._record_stamps()
        return True

    # --- the model the window shows -------------------------------------------------------

    def _display_message(self, problem):
        """A problem's message with physical control names turned into displayed labels."""
        if not problem.control or not problem.message.startswith(problem.control):
            return problem.message
        path, _, rest = problem.message.partition(": ")
        tail = path[len(problem.control) :]
        text = orient.label(self._profile.orientation, problem.control)
        layer = _LAYER_IN_PATH.search(tail)
        if layer:
            text += f", layer {layer.group(1)}"
        field = tail.rsplit(".", 1)[-1] if tail and not tail.rsplit(".", 1)[-1].isdigit() else ""
        if field and field != "layers":
            text += f" ({field})"
        return f"{text}: {rest}" if rest else text

    def _tab_label(self, layer):
        name = self._profile.layer_names[layer - 1]
        return f"{layer} {name}" if name else str(layer)

    def _tile(self, control, caption):
        tab = self._tab or None
        info = tile_info(self._profile, control, tab, self._note_names)
        info.update(
            control=control,
            caption=caption,
            selected=control == self._selected,
            label=orient.label(self._profile.orientation, control),
        )
        return info

    def _shown(self):
        """The tab as the inspector words it: `layer 1 "Drums"` or `Global tab`."""
        if not self._tab:
            return "Global tab"
        name = self._profile.layer_names[self._tab - 1]
        return f'layer {self._tab} "{name}"' if name else f"layer {self._tab}"

    def _inspector(self):
        profile, tab = self._profile, self._tab or None
        if not self._selected:
            total = len(prof.CONTROL_NAMES)
            if tab is None:
                same = sum(
                    1
                    for c in prof.CONTROL_NAMES
                    if prof.control_shape(profile.controls.get(c)) in ("global", "layer-key")
                )
                count = f"Global tab: {same} of {total} controls act the same on every layer."
            else:
                doing = sum(1 for c in prof.CONTROL_NAMES if profile.action(c, tab) is not None)
                shown = self._shown()
                count = f"{shown[0].upper()}{shown[1:]}: {doing} of {total} controls do something here."
            return {
                "selected": False,
                "title": "",
                "subtitle": "",
                "lines": [],
                "hint": "Click a key or dial to edit.",
                "count": count,
                "edit": {"mode": "none"},
            }
        control = self._selected
        shape = prof.control_shape(profile.controls.get(control))
        label = orient.label(profile.orientation, control).upper()
        if shape == "layer-key":
            subtitle = "🔒 on every layer"
        elif shape == "global":
            subtitle = "same on every layer (global)"
        else:
            subtitle = self._shown()
        tile = tile_info(profile, control, self._tab or None, self._note_names)
        lines = [tile["line1"], tile["line2"]] if tile["state"] != "empty" else ["Does nothing here."]
        return {
            "selected": True,
            "title": label,
            "subtitle": subtitle,
            "lines": [line for line in lines if line],
            "hint": "",
            "count": "",
            "edit": insp.describe(profile, control, tab, self._drafts, self._note_names),
        }

    def _device_line(self):
        profile = self._profile
        light = profile.lighting
        if light is None:
            rgb = "RGB: left as it is"
        else:
            mode = MODE_BY_NUMBER.get(light.mode)
            rgb = f"RGB: {mode.name if mode else light.mode}"
        return f'{rgb} · orientation {profile.orientation} · port "{profile.port}" ch {profile.channel}'

    def _can_apply(self):
        light = self._profile.lighting
        return (
            light is not None
            and not dev.lighting_problem(light)
            and self._pad_connected
            and not self._pad_busy
            and not self._cooling
        )

    def _device_model(self):
        """Everything the device panel shows (design 4.10); the QML holds no logic of its own."""
        profile = self._profile
        port, port_error = self._port_draft or (profile.port, "")
        light = dev.describe_lighting(profile.lighting)
        problem = dev.lighting_problem(profile.lighting)
        return {
            "orientation": profile.orientation,
            "orientations": [
                {"value": o, "label": o.removeprefix("dials-").capitalize()} for o in prof.ORIENTATIONS
            ],
            "port": {"text": port, "error": port_error},
            "channel": profile.channel,
            "lighting": light,
            "pad": {
                "connected": self._pad_connected,
                "headline": self._pad_headline,
                "now": self._pad_now,
            },
            "apply": {
                "enabled": self._can_apply(),
                "busy": self._pad_busy,
                "problem": problem,
                "note": "Each Apply is saved in the pad's memory.",
                "last": self._last,
                "lastKind": self._last_kind,
            },
        }

    def _refresh(self):
        profile = self._profile
        if self._draft_for != (self._selected, self._tab):
            self._drafts = {}
            self._draft_for = (self._selected, self._tab)
        o = profile.orientation
        keys = []
        for number in range(1, prof.KEY_COUNT + 1):
            tile = self._tile(f"key.{orient.physical_key(o, number)}", str(number))
            tile.update(number=number, row=(number - 1) // orient.GRID, col=(number - 1) % orient.GRID)
            keys.append(tile)
        dials = []
        for number in range(1, prof.ENCODER_COUNT + 1):
            physical = orient.physical_dial(o, number)
            dials.append(
                {
                    "number": number,
                    "push": self._tile(f"enc.{physical}.push", f"D{number}"),
                    "turn": self._tile(f"enc.{physical}.turn", f"D{number} turn"),
                }
            )
        tabs = [{"index": 0, "label": "Global"}]
        tabs += [{"index": n, "label": self._tab_label(n)} for n in range(1, profile.layer_count + 1)]
        problems = [
            {"control": p.control or "", "message": self._display_message(p)}
            for p in prof.validate(profile)
        ]
        self._ui = {
            "title": f"glra-midi config — {self.name}" + (" •" if self.is_dirty else ""),
            "keys": keys,
            "dials": dials,
            "tabs": tabs,
            "problems": problems,
            "inspector": self._inspector(),
            "device": self._device_model(),
            "canSave": not problems and not self._load_error and self._port_draft is None,
            "canSaveAs": not problems and self._port_draft is None,
        }
        self.changed.emit()

    # --- properties for QML -------------------------------------------------------------

    @Property(str, constant=True)
    def scheme(self):
        """`"system"` (follow the OS light/dark setting), or `"light"` / `"dark"` when forced."""
        return self._scheme

    @Property(str, notify=changed)
    def title(self):
        return self._ui["title"]

    @Property(str, notify=changed)
    def profileName(self):
        return self.name

    @Property(bool, notify=changed)
    def dirty(self):
        return self.is_dirty

    @Slot(result="QVariantList")
    def listProfiles(self):
        """The names in the profiles folder (for Open…), read fresh each time."""
        folder = prof.profiles_dir(self._home)
        return sorted(p.stem for p in folder.glob("*.toml") if not p.name.startswith("."))

    @Property(int, notify=changed)
    def tab(self):
        return self._tab

    @Property(int, notify=changed)
    def layerCount(self):
        return self._profile.layer_count

    @Property("QVariantList", notify=changed)
    def tabs(self):
        return self._ui["tabs"]

    @Property(str, notify=changed)
    def orientation(self):
        return self._profile.orientation

    @Property(str, notify=changed)
    def dialSide(self):
        return orient.dial_side(self._profile.orientation)

    @Property("QVariantList", notify=changed)
    def keys(self):
        return self._ui["keys"]

    @Property("QVariantList", notify=changed)
    def dials(self):
        return self._ui["dials"]

    @Property(str, notify=changed)
    def selected(self):
        return self._selected

    @Property("QVariantMap", notify=changed)
    def inspector(self):
        return self._ui["inspector"]

    @Property("QVariantList", notify=changed)
    def problems(self):
        return self._ui["problems"]

    @Property(bool, notify=changed)
    def canSave(self):
        return self._ui["canSave"]

    @Property(bool, notify=changed)
    def canSaveAs(self):
        return self._ui["canSaveAs"]

    @Property(str, notify=changed)
    def error(self):
        return self._error

    @Property(str, notify=changed)
    def notice(self):
        return self._notice

    @Property(str, notify=changed)
    def diskMessage(self):
        return self._disk_message

    @Property(str, notify=changed)
    def deviceLine(self):
        return self._device_line()

    @Property("QVariantMap", notify=changed)
    def device(self):
        return self._ui["device"]

    @Property(str, notify=changed)
    def padHeadline(self):
        return self._pad_headline

    @property
    def pad(self):
        """The pad object (`FakePad` in tests, `--demo` and captures)."""
        return self._pad

    def wait_for_pad(self, timeout=5.0):
        """Run the event loop until the worker has no call outstanding (tests and captures)."""
        import time

        from PySide6.QtCore import QCoreApplication

        end = time.monotonic() + timeout
        while not self._worker.idle or self._cooling:
            QCoreApplication.processEvents()
            if time.monotonic() > end:
                raise TimeoutError("the pad worker did not finish")
            time.sleep(0.005)

    # --- tabs, selection, layers --------------------------------------------------------

    @Slot(int)
    def selectTab(self, tab):
        if 0 <= tab <= self._profile.layer_count and tab != self._tab:
            self._tab = tab
            self._refresh()

    @Slot(str)
    def selectControl(self, control):
        if control in prof.CONTROL_NAMES and control != self._selected:
            self._selected = control
            self._refresh()

    @Slot()
    def clearSelection(self):
        if self._selected:
            self._selected = ""
            self._refresh()

    def _edit(self, profile):
        self._profile = profile
        self._error = ""
        self._refresh()

    @Slot(str)
    def setOrientation(self, value):
        if value not in prof.ORIENTATIONS:
            self._error = f"pad.orientation: expected one of {', '.join(prof.ORIENTATIONS)}"
            self._refresh()
        elif value != self._profile.orientation:
            self._edit(replace(self._profile, orientation=value))

    # --- the device panel (design 4.10, 5) ----------------------------------------------------

    @Slot(int)
    def setLightingMode(self, mode):
        """The mode selector; `-1` ("Leave as it is") removes `[lighting]`. Edits the profile
        only: nothing reaches the pad until [Apply to pad]."""
        try:
            new = dev.with_mode(self._profile.lighting, mode)
        except dev.lights.LightingError as err:
            self._fail(err)
            return
        if new != self._profile.lighting:
            self._edit(replace(self._profile, lighting=new))

    @Slot(str, int)
    def setLightingLevel(self, field, value):
        """Brightness or speed, 0..4."""
        self._edit_lighting(lambda light: dev.with_level(light, field, value))

    @Slot(bool)
    def setLightingColor(self, on):
        """The "One colour" switch."""
        self._edit_lighting(lambda light: dev.with_color(light, on))

    @Slot(int, int)
    def setLightingHsv(self, index, value):
        """One of hue, saturation, value (index 0, 1, 2), 0..255."""
        self._edit_lighting(lambda light: dev.with_hsv(light, index, value))

    def _edit_lighting(self, change):
        try:
            new = change(self._profile.lighting)
        except dev.lights.LightingError as err:
            self._fail(err)
            return
        if new != self._profile.lighting:
            self._edit(replace(self._profile, lighting=new))

    @Slot(str)
    def setPort(self, text):
        """The MIDI port name. An invalid one (empty) stays in the field with the profile's
        message and never reaches the profile."""
        candidate = replace(self._profile, port=text)
        bad = [p for p in prof.validate(candidate) if p.message.startswith("midi.port")]
        if bad:
            self._port_draft = (text, bad[0].message.partition(": ")[2])
            self._refresh()
            return
        self._port_draft = None
        if text != self._profile.port:
            self._edit(candidate)
        else:
            self._refresh()

    @Slot(int)
    def setChannel(self, channel):
        """The default MIDI channel, 1..16."""
        if not 1 <= channel <= 16:
            self._fail(prof.ProfileError(f"midi.channel: expected an integer 1..16, got {channel}"))
        elif channel != self._profile.channel:
            self._edit(replace(self._profile, channel=channel))

    @Slot()
    def refreshPad(self):
        """Read the pad's state (read-only: status and the 11 lighting bytes) on the worker."""
        if self._pad_busy:
            return
        self._pad_busy = True
        self._worker.submit("read", self._pad.read)
        self._refresh()

    @Slot()
    def applyLighting(self):
        """[Apply to pad]: the app's one pad write, and only from this slot. Sends the profile's
        `[lighting]` as shown, on the worker thread, guarded (`lighting.apply`)."""
        if self._profile.lighting is None:
            self._last, self._last_kind = dev.NO_LIGHTING, "info"
            self._refresh()
            return
        if not self._can_apply():
            return
        self._pad_busy = True
        self._applying = True
        self._last, self._last_kind = "", ""
        directory = prof.app_dir(self._home) / "backups"
        self._worker.submit("apply", self._pad.apply, self._profile.lighting, directory)
        self._refresh()

    def _pad_done(self, kind, result, error):
        """A worker call finished (on the UI thread)."""
        self._worker.finished_one()
        self._pad_busy = False
        if kind == "read":
            reading = result if error is None else not_found(str(error))
            self._pad_connected = reading.connected
            self._pad_headline, self._pad_now = describe_reading(reading)
        else:
            self._applying = False
            if isinstance(error, dev.lights.WriteNotConfirmed):
                # The write went out: say so, and show what the pad holds now when it could be read.
                self._last, self._last_kind = str(error), "warn"
                if error.after is not None:
                    self._pad_now = describe_reading(PadReading(True, None, bytes.fromhex(error.after)))[1]
            elif error is not None:
                self._last, self._last_kind = f"Not applied: {error}", "err"
            else:
                self._pad_now = describe_reading(PadReading(True, None, result.payload))[1]
                if result.unchanged:
                    self._last, self._last_kind = "Already set.", "info"
                else:
                    self._last, self._last_kind = "Applied and read back.", "ok"
            if self._cooldown_ms > 0:
                self._cooling = True
                QTimer.singleShot(self._cooldown_ms, self._end_cooldown)
        if kind != "read" and self._quit_waiting:
            self._quit_waiting = False
            self._notice = ""
            self._refresh()
            self._guard_unsaved(self.quitApproved.emit)
            return
        self._refresh()

    def _end_cooldown(self):
        self._cooling = False
        self._refresh()

    @Slot()
    def addLayer(self):
        try:
            edit = prof.add_layer(self._profile)
        except prof.ProfileError as err:
            self._error = str(err)
            self._refresh()
            return
        self._tab = edit.profile.layer_count
        self._edit(edit.profile)

    @Slot(int)
    def removeLayer(self, layer):
        """Remove layer `layer`; asks first when it holds events."""
        try:
            edit = prof.remove_layer(self._profile, layer)
        except prof.ProfileError as err:
            self._error = str(err)
            self._refresh()
            return
        if edit.discarded:
            self._confirmed = lambda: self._apply_remove(layer, edit.profile)
            n = len(edit.discarded)
            self.confirmPrompt.emit(
                f"Remove layer {layer}?", f"Layer {layer} has {_plural(n, 'event')}. Remove it?"
            )
        else:
            self._apply_remove(layer, edit.profile)

    def _apply_remove(self, layer, profile):
        if self._tab == layer:
            self._tab = min(layer, profile.layer_count)
        elif self._tab > layer:
            self._tab -= 1
        self._edit(profile)

    @Slot(int, str)
    def renameLayer(self, layer, name):
        try:
            edit = prof.rename_layer(self._profile, layer, name.strip())
        except prof.ProfileError as err:
            self._error = str(err)
            self._refresh()
            return
        if edit.profile != self._profile:
            self._edit(edit.profile)

    # --- editing the selected control (the inspector, design 4.5, 4.6) ---------------------

    def _shown_event(self):
        """The press or turn event of the selected control on the shown tab, or None (nothing
        there, a layer key, or a per-layer control seen from the Global tab)."""
        if not self._selected:
            return None
        action = self._profile.action(self._selected, self._tab) if self._tab else None
        if not self._tab:
            control = self._profile.controls.get(self._selected)
            action = None if isinstance(control, prof.PerLayer) else control
        return None if action is None or insp.is_layer_key(action) else action

    def _label(self):
        return orient.label(self._profile.orientation, self._selected)

    def _fail(self, err):
        self._error = str(err)
        self._refresh()

    def _commit(self, edit, title, question):
        """Apply `edit`; when it throws events away, ask `question` first."""
        self._drafts = {}
        if edit.discarded:
            self._confirmed = lambda: self._edit(edit.profile)
            self.confirmPrompt.emit(title, question)
        else:
            self._edit(edit.profile)

    def _put(self, event):
        """Set the selected control's event on the shown tab (the Global tab: globally)."""
        try:
            edit = prof.set_event(self._profile, self._selected, self._tab or None, event)
        except prof.ProfileError as err:
            self._fail(err)
            return
        self._drafts = {}
        self._edit(edit.profile)

    @Slot(str)
    def setAction(self, action):
        """The Action row: `"event"` | `"layer"` | `"none"` (a turn's kinds go to `setKind`)."""
        if not self._selected:
            return
        control, tab = self._selected, self._tab or None
        shape = prof.control_shape(self._profile.controls.get(control))
        if action == "none":
            try:
                edit = prof.clear_event(self._profile, control, tab)
            except prof.ProfileError as err:
                self._fail(err)
                return
            self._drafts = {}
            self._edit(edit.profile)
        elif action == "event":
            if self._shown_event() is None and not (shape == "per-layer" and tab is None):
                self._put(insp.default_event("cc-relative" if control in prof.TURN_CONTROLS else "note"))
        elif action == "layer" and shape != "layer-key" and control not in prof.TURN_CONTROLS:
            self.setLayerKey("layer-inc", 0)

    @Slot(str)
    def setKind(self, kind):
        """Change the shown event to another kind (keeps `cc` and `channel`)."""
        if not self._selected:
            return
        event = self._shown_event()
        valid = [k for k, _ in (insp.TURN_KINDS if self._selected in prof.TURN_CONTROLS else insp.PRESS_KINDS)]
        if kind not in valid:
            self._fail(prof.ProfileError(f"kind: expected one of {', '.join(valid)}, got {kind!r}"))
        elif event is None or event.kind != kind:
            self._put(insp.default_event(kind, event))

    @Slot(str, str)
    def setField(self, key, text):
        """Set one field of the shown event from typed text. An invalid value stays in the
        field with the parser's message and never reaches the profile."""
        event = self._shown_event()
        if event is None:
            return
        try:
            new = insp.apply_field(event, key, text)
        except prof.ProfileError as err:
            self._drafts[key] = (text, str(err))
            self._refresh()
            return
        self._drafts[key] = (text, "")
        try:
            edit = prof.set_event(self._profile, self._selected, self._tab or None, new)
        except prof.ProfileError as err:
            self._fail(err)
            return
        self._edit(edit.profile)

    @Slot(str)
    def setApplies(self, value):
        """`"global"`: the shown layer's event applies on every layer (asks before discarding
        other layers' events). `"layer"`: a global event is copied onto every layer."""
        control, tab = self._selected, self._tab or None
        shape = prof.control_shape(self._profile.controls.get(control))
        try:
            if value == "global" and shape == "per-layer":
                edit = prof.make_global(self._profile, control, tab)
                kept = tab or min(n for n, _ in self._profile.controls[control].events)
                text = insp.discard_text(self._label(), edit.discarded, kept)
                self._commit(edit, "Make it global?", text)
            elif value == "layer" and shape == "global" and tab is not None:
                self._commit(prof.make_per_layer(self._profile, control), "", "")
        except prof.ProfileError as err:
            self._fail(err)

    @Slot(str, int)
    def setLayerKey(self, kind, layer):
        """Make the selected press a layer key: `layer-set` (to `layer`), `layer-inc` or
        `layer-dec`. Asks before discarding the events it held."""
        control = self._selected
        if kind not in insp.LAYER_KEY_KINDS or control not in prof.PRESS_CONTROLS:
            return
        if kind == "layer-set":
            key = prof.LayerSet(layer=layer or self._tab or 1)
        else:
            key = prof.EVENT_CLASSES[kind]()
        try:
            edit = prof.set_layer_key(self._profile, control, key)
        except prof.ProfileError as err:
            self._fail(err)
            return
        text = insp.discard_text(self._label(), edit.discarded)
        self._commit(edit, "Make it a layer key?", text)

    # --- prompts ------------------------------------------------------------------------

    def _guard_unsaved(self, action):
        if not self.is_dirty:
            action()
            return
        self._after = action
        self.unsavedPrompt.emit(f"Save changes to {self.name}?")

    @Slot(str)
    def resolveUnsaved(self, choice):
        """Answer `unsavedPrompt`: `"save"`, `"discard"` or `"cancel"`."""
        after, self._after = self._after, None
        if after is None or choice == "cancel":
            return
        if choice == "save" and not self._save_to(self._path):
            return
        after()

    @Slot(bool)
    def resolveConfirm(self, yes):
        """Answer `confirmPrompt`."""
        action, self._confirmed = self._confirmed, None
        if yes and action is not None:
            action()

    # --- files --------------------------------------------------------------------------

    @Slot()
    def saveProfile(self):
        if self._save_to(self._path):
            self._refresh()

    @Slot(str, result=str)
    def checkName(self, name):
        """The reason `name` can't name a profile, or `""` when it can (for Save As…)."""
        try:
            prof.check_profile_name(name.strip())
        except prof.ProfileError as err:
            return str(err).removeprefix("profile name: ")
        return ""

    @Slot(str)
    def saveProfileAs(self, name):
        name = name.strip()
        try:
            path = prof.profile_path(name, self._home)
        except prof.ProfileError as err:
            self._error = str(err)
            self._refresh()
            return
        if path.exists() and path != self._path:
            self._confirmed = lambda: self._finish_save_as(name, path)
            self.confirmPrompt.emit(f"Replace {name}?", f"{name} already exists. Replace it?")
        else:
            self._finish_save_as(name, path)

    def _finish_save_as(self, name, path):
        if self._save_to(path, allow_broken=True):
            self._load_error = ""
            self._point_current_at(name)
            self._refresh()

    def _point_current_at(self, name):
        try:
            prof.set_current(name, self._home)
        except (OSError, prof.ProfileError) as err:
            self._error = f"Saved {name}, but couldn't make it current: {err}"
        self._record_stamps()

    @Slot(str)
    def openProfile(self, name):
        self._guard_unsaved(lambda: self._open(name))

    def _open(self, name):
        try:
            path = prof.profile_path(name, self._home)
        except prof.ProfileError as err:
            self._error = str(err)
            self._refresh()
            return
        if self._load(path):
            self._selected = ""
            self._point_current_at(name)
        self._refresh()

    @Slot()
    def revertProfile(self):
        """Re-read the open file from disk; asks first when there are unsaved changes."""
        if self.is_dirty:
            self._confirmed = self._revert
            self.confirmPrompt.emit(
                f"Revert {self.name}?", f"Throw away the unsaved changes to {self.name}?"
            )
        else:
            self._revert()

    def _revert(self):
        self._load(self._path)
        self._refresh()

    @Property(bool, notify=changed)
    def applying(self):
        """True while the Apply write runs on the worker; the window refuses to close then."""
        return self._applying

    @Slot()
    def requestQuit(self):
        """The window was asked to close. While the one pad write runs, wait for it (with a
        message) rather than quit mid-write; then ask about unsaved changes as usual."""
        if self._applying:
            self._quit_waiting = True
            self._notice = "Waiting for the pad write to finish before closing."
            self._refresh()
            return
        self._guard_unsaved(self.quitApproved.emit)

    def shutdown(self):
        """Join the pad worker; `gui.main` calls this after the event loop ends."""
        self._worker.shutdown()

    # --- changes on disk ----------------------------------------------------------------

    @Slot()
    def poll(self):
        """Look for a change to the open file or to `current` on disk (design 4.8)."""
        file_now = _stamp(self._path)
        current_now = _stamp(self._current_file())
        if file_now == self._file_stamp and current_now == self._current_stamp:
            return
        if self._disk_message:
            # Already told the user; wait for Reload or Keep mine.
            return
        if self.is_dirty:
            self._disk_message = f"{self.name} changed on disk."
            if file_now == self._file_stamp:
                self._disk_message = "The current profile changed on disk."
            self._refresh()
            return
        self._reload()

    def _reload(self):
        """Load whatever `current` names now; if it won't read, `_load` keeps the open profile."""
        before_path = self._path
        if self._load(prof.current_profile_path(self._home)) and self._path != before_path:
            self._selected = ""
        self._refresh()

    @Slot()
    def reloadFromDisk(self):
        """[Reload] on the "changed on disk" notice: drop unsaved edits, read the disk."""
        self._disk_message = ""
        self._reload()

    @Slot()
    def keepMine(self):
        """[Keep mine]: stop asking about this disk change; the next Save overwrites it."""
        self._disk_message = ""
        self._record_stamps()
        self._refresh()

    @Slot()
    def dismissNotice(self):
        self._notice = ""
        self._error = ""
        self._refresh()
