# SPDX-License-Identifier: GPL-3.0-only

"""Keep the pad from typing into apps, without root (loom:silent-capture).

macOS applies a per-device `UserKeyMapping` through `hidutil`. Mapping every code
the pad can send to "no event" (`0x700000000`) silences it for the system while
the non-exclusive hidapi readers still receive the original reports (checked by
hand on 2026-11-12, loom:suppression-route). The mapping lives on the pad's HID
services, so a replug wipes it and `watch()` re-applies it on every connect.

Bob's own entries on the same services (for example CapsLock -> Cmd) are kept:
`apply` reads the current mapping, merges ours in, sets it and reads it back.
macOS can replace a service's whole mapping a moment after a (re)connect, for
example when it reapplies Bob's modifier-key setting, so `ensure` (run about
every 100 ms for 10 s after a connect, then every 2 s) re-merges ours into whatever is there now.
`restore` and `unsilence` remove only our sources from the current mapping; no
snapshot from connect time is ever put back.

Everything that touches hidutil goes through `Hidutil.run(*args)`, so the rest
is testable with a fake. hidutil prints "Run as root to remap alphanumerics..."
and applies nothing if any source is disallowed, so that text (or a non-zero
exit, or a failed read-back) counts as failure.
"""

import json
import re
import subprocess
import time

VENDOR_ID = 0x36AE
PRODUCT_ID = 0x2475
KEYBOARD_PAGE = 0x700000000  # (usage page << 32) | usage, as hidutil writes them
CONSUMER_PAGE = 0xC00000000
NO_EVENT = KEYBOARD_PAGE  # usage 0 on the keyboard page: swallowed
ROOT_REFUSAL = "Run as root"

RETRY_SECONDS = 5.0
RETRY_INTERVAL = 0.25
CHECK_SECONDS = 2.0  # how often `watch` asks the Guard to re-verify the mapping, in steady state
# macOS can overwrite the mapping a moment after a (re)connect (2026-11-12 replug: one key typed
# inside the 2 s gap), so for FAST_WINDOW_SECONDS after each `on_pad` the check runs this often.
# One `hidutil --get` takes about 5 ms (measured 2026-11-12), so 100 ms polling for 10 s is cheap.
FAST_CHECK_SECONDS = 0.1
FAST_WINDOW_SECONDS = 10.0


def check_interval(since_connect):
    """Seconds to wait before the next re-check, `since_connect` seconds after the last on_pad."""
    return FAST_CHECK_SECONDS if since_connect < FAST_WINDOW_SECONDS else CHECK_SECONDS


TYPING_WARNING = (
    "WARNING: --allow-typing: the pad is not silenced, so it types into the focused app\n"
    "         (keys send their key codes, dials change the volume) while it plays MIDI."
)


def refusal_message(exc):
    return (
        f"glra-osc: cannot silence the pad: {exc}\n"
        "  Refusing to run, because the pad would type into the focused app.\n"
        "  Pass --allow-typing to run anyway."
    )


class SilenceError(Exception):
    """Suppression could not be applied, verified or restored."""


class SilenceRefused(SilenceError):
    """hidutil refused the mapping outright; retrying cannot help."""


class Hidutil:
    """The one seam to the `hidutil` binary: run it, return (exit code, text)."""

    def run(self, *args):
        try:
            done = subprocess.run(
                ["hidutil", *args],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise SilenceError(f"could not run hidutil: {exc}") from exc
        return done.returncode, done.stdout + done.stderr


def our_entries(layout):
    """The (src, dst) pairs that silence every code in `layout`, keys then dials."""
    srcs = [KEYBOARD_PAGE | usage for usage in layout["keys"]]
    srcs += [CONSUMER_PAGE | usage for usage in layout["consumer"]]
    return [(src, NO_EVENT) for src in srcs]


_SERVICE = re.compile(r"^([0-9a-fA-F]+)\s+UserKeyMapping\s+(.*)$")
_FIELD = re.compile(r"^\s*HIDKeyboardModifierMapping(Src|Dst)\s*=\s*(\d+)\s*;\s*$")


def parse_mapping(text):
    """Parse `hidutil property --get UserKeyMapping` into {registry id: [(src, dst), ...]}.

    No matching service prints nothing (an empty dict). A service with no
    mapping prints `(` `)` or `(null)` and gets an empty list.
    """
    services = {}
    current = None  # (list of entries, partial {"Src": n, "Dst": n})
    for line in text.splitlines():
        if not line.strip() or line.startswith("RegistryID"):
            continue
        header = _SERVICE.match(line)
        if header:
            entries = services.setdefault(header.group(1).lower(), [])
            current = (entries, {})
            continue
        if current is None:
            raise SilenceError(f"unexpected hidutil output: {line!r}")
        field = _FIELD.match(line)
        if field:
            current[1][field.group(1)] = int(field.group(2))
        elif line.strip() in ("}", "},"):
            part = current[1]
            if set(part) != {"Src", "Dst"}:
                raise SilenceError(f"incomplete mapping entry in hidutil output: {part}")
            current[0].append((part["Src"], part["Dst"]))
            current[1].clear()
        elif line.strip() not in ("(", ")", "{", "(null)"):
            raise SilenceError(f"unexpected hidutil output: {line!r}")
    return services


def _payload(entries):
    return json.dumps(
        {
            "UserKeyMapping": [
                {"HIDKeyboardModifierMappingSrc": src, "HIDKeyboardModifierMappingDst": dst}
                for src, dst in entries
            ]
        }
    )


def _union(services):
    """Entries across all services, first-seen order, without duplicates."""
    seen = []
    for entries in services.values():
        seen += [e for e in entries if e not in seen]
    return seen


class Silencer:
    def __init__(
        self,
        layout,
        hidutil=None,
        retry_seconds=RETRY_SECONDS,
        retry_interval=RETRY_INTERVAL,
        sleep=time.sleep,
        clock=time.monotonic,
    ):
        self.ours = our_entries(layout)
        self.sources = {src for src, _ in self.ours}
        self._hidutil = hidutil or Hidutil()
        self._match = json.dumps({"VendorID": VENDOR_ID, "ProductID": PRODUCT_ID})
        self._retry_seconds = retry_seconds
        self._retry_interval = retry_interval
        self._sleep = sleep
        self._clock = clock
        self._applied = False  # True once we put our entries on the pad

    # -- hidutil calls -------------------------------------------------------

    def _get(self):
        code, text = self._hidutil.run(
            "property", "--matching", self._match, "--get", "UserKeyMapping"
        )
        if code != 0:
            raise SilenceError(f"hidutil --get failed (exit {code}): {text.strip()}")
        return parse_mapping(text)

    def _set(self, entries):
        code, text = self._hidutil.run(
            "property", "--matching", self._match, "--set", _payload(entries)
        )
        if ROOT_REFUSAL in text:
            raise SilenceRefused(f"hidutil refused the mapping: {text.strip()}")
        if code != 0:
            raise SilenceError(f"hidutil --set failed (exit {code}): {text.strip()}")

    def _without_ours(self, entries):
        return [e for e in entries if e[0] not in self.sources]

    # -- public --------------------------------------------------------------

    def apply(self):
        """Silence the pad and verify it; returns the number of services covered.

        Retries for a few seconds when the services are not ready yet. Raises
        SilenceError (SilenceRefused at once for a root-only refusal).
        """
        deadline = self._clock() + self._retry_seconds
        while True:
            try:
                return self._apply_once()
            except SilenceRefused:
                raise
            except SilenceError as exc:
                if self._clock() >= deadline:
                    raise SilenceError(f"{exc} (gave up after {self._retry_seconds:g} s)") from exc
            self._sleep(self._retry_interval)

    def _apply_once(self):
        services = self._get()
        if not services:
            raise SilenceError("hidutil lists no services for the pad (36ae:2475)")
        self._merge_ours(services)
        return len(self._verify())

    def _merge_ours(self, services):
        """Set (every non-ours entry now on the pad) + ours. Returns the entries set."""
        wanted = self._without_ours(_union(services)) + self.ours
        self._applied = True
        self._set(wanted)
        return wanted

    def _verify(self):
        """Re-read and check every one of our entries on every service; returns the services."""
        after = self._get()
        if not after:
            raise SilenceError("the pad's services vanished while applying")
        for rid, entries in after.items():
            missing = [e for e in self.ours if e not in entries]
            if missing:
                raise SilenceError(
                    f"service {rid}: {len(missing)} of {len(self.ours)} of our mapping entries "
                    "missing after the set"
                )
        return after

    def ensure(self):
        """Reapply ours if any service lost some; returns how many entries were missing.

        Merges into whatever the services hold now, so entries macOS added since
        (Bob's CapsLock -> Cmd, say) stay. 0 when all is well or no service is listed.
        """
        services = self._get()
        missing = {e for entries in services.values() for e in self.ours if e not in entries}
        if not missing:
            return 0
        self._merge_ours(services)
        self._verify()
        return len(missing)

    def restore(self):
        """Remove our entries from the current mapping. No-op if nothing was applied."""
        if self._applied:
            self.unsilence()
            self._applied = False

    def unsilence(self):
        """Remove only entries whose source is one of ours; needs no saved state.

        Returns the number of entries removed (0 when the pad is absent or clean).
        """
        services = self._get()
        merged = _union(services)
        cleaned = self._without_ours(merged)  # [] when the mapping is empty or ours only
        removed = len(merged) - len(cleaned)
        if removed:
            self._set(cleaned)
            if any(e[0] in self.sources for es in self._get().values() for e in es):
                raise SilenceError("our entries are still on the pad after removing them")
        return removed


class Guard:
    """Glue for `monitor` and `run`: apply on every connect, restore at the end.

    `on_pad` is the hook `watch()` calls when the pad (re)appears. Without
    `allow_typing` a failure raises SilenceError and the command refuses to
    continue; with it the failure is reported and the pad keeps typing.
    """

    def __init__(self, silencer, say, allow_typing=False):
        self.silencer = silencer
        self.say = say
        self.allow_typing = allow_typing
        self.active = False
        self._tick_error = None

    def on_pad(self):
        try:
            count = self.silencer.apply()
        except SilenceError as exc:
            self.active = False
            if not self.allow_typing:
                raise
            self.say(f"# WARNING: could not silence the pad ({exc}); it will type (--allow-typing)")
            return
        self.active = True
        self.say(f"# pad silenced ({len(self.silencer.ours)} codes on {count} services)")

    def tick(self):
        """Re-verify the mapping (on `check_interval`'s schedule while the pad is connected).

        Failures are reported once per distinct message, never raised: a replug in
        progress makes hidutil fail briefly, and `watch` runs `on_pad` again after it.
        """
        if not self.active:
            return
        try:
            missing = self.silencer.ensure()
        except SilenceError as exc:
            if str(exc) != self._tick_error:
                self._tick_error = str(exc)
                self.say(f"# WARNING: could not re-check the pad's key mapping: {exc}")
            return
        self._tick_error = None
        if missing:
            self.say(f"# pad mapping reapplied ({missing} entries were missing)")

    def close(self):
        """Remove our entries from the pad's mapping; report (don't raise) if that fails."""
        try:
            self.silencer.restore()
        except SilenceError as exc:
            self.say(f"# WARNING: could not restore the pad's key mapping: {exc}")
            self.say("# run `glra-osc unsilence` to remove our entries by hand")
        else:
            if self.active:
                self.say("# pad mapping restored")
        self.active = False
