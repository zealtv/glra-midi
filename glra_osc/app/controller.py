# SPDX-License-Identifier: GPL-3.0-only

"""The app's model: a `Controller(QObject)` over a `profile.Profile` (docs/config-app.md 4.1).

The profile lives here, in Python. QML draws what `ui` properties hold and calls the slots
below; it keeps no profile logic and no summary text. The controller touches no device.

Files (design 4.8): the profile opens from `profile.current_profile_path()`; Open and Save As
work inside the profiles folder and call `set_current`, so `glra-osc run` follows. A change
to the open file, or to `current`, on disk reloads (no unsaved edits) or raises a
"changed on disk" notice (unsaved edits). `poll()` does that check; `poll_ms` > 0 runs it on a
timer. Prompts are two signals the window answers: `unsavedPrompt` (Save / Don't save /
Cancel, answered by `resolveUnsaved`) and `confirmPrompt` (Yes / No, `resolveConfirm`).
"""

import re
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from .. import orientation as orient
from .. import profile as prof
from ..lighting import MODE_BY_NUMBER
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

    def __init__(self, home=None, poll_ms=0, scheme="system", parent=None):
        super().__init__(parent)
        self._scheme = scheme
        self._home = home
        self._after = None  # what to do once the unsaved-changes prompt is answered
        self._confirmed = None  # what to do on "yes" to a confirmPrompt
        self._error = ""
        self._notice = ""
        self._disk_message = ""
        self._warned = set()  # files already warned about for comments
        self._load_error = ""
        self._tab = 1  # starts on layer 1; 0 is the Global tab
        self._selected = ""
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
        return self._profile != self._baseline

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
            "hint": "Editing fields arrive in the next update.",
            "count": "",
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

    def _refresh(self):
        profile = self._profile
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
            "title": f"glra-osc config — {self.name}" + (" •" if self.is_dirty else ""),
            "keys": keys,
            "dials": dials,
            "tabs": tabs,
            "problems": problems,
            "inspector": self._inspector(),
            "canSave": not problems and not self._load_error,
            "canSaveAs": not problems,
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

    @Slot()
    def requestQuit(self):
        self._guard_unsaved(self.quitApproved.emit)

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
