#!/usr/bin/env python3
"""Make the Claude status bar components win the width fight.

iTerm2 stores per-component layout knobs (priority, compression resistance,
minimum width) in its prefs plist — they are NOT settable from a status bar
script or the Python API. This sets, for every profile slot whose registration
references one of the Claude identifiers:

    base: priority             -> 20   (kept before lower-priority components)
    base: compression resistance -> 10 (resists being squeezed to nothing)
    minwidth                   -> 0    (may shrink freely; never forced wide)

iTerm2 rewrites this plist on quit, so:

    1. QUIT iTerm2 completely (Cmd-Q).
    2. From **Terminal.app** (not iTerm2):  python3 set-priority.py
    3. Reopen iTerm2.

Tradeoff: in a narrow pane the Claude components now win, so CPU/RAM/clock may
be squeezed instead. That is the point of "priority high".
"""
import base64
import plistlib
import os
import subprocess
import sys

PLIST = os.path.expanduser("~/Library/Preferences/com.googlecode.iterm2.plist")
IDENTS = (b"com.pmi.claude.ratelimits", b"com.pmi.claude.model", b"com.pmi.claude.effort")

PRIORITY = 20.0
COMPRESSION_RESISTANCE = 10
MINWIDTH = 0


def is_claude(component):
    cfg = component.get("configuration", {})
    for key, val in cfg.items():
        if "registration" not in key.lower():
            continue
        try:
            raw = base64.b64decode(val) if isinstance(val, str) else bytes(val)
        except Exception:
            continue
        if any(i in raw for i in IDENTS):
            return True
    return False


def main():
    if "iTerm" in subprocess.run(["pgrep", "-x", "iTerm2"], capture_output=True, text=True).stdout or \
       subprocess.run(["pgrep", "-f", "iTerm.app/Contents/MacOS/iTerm2"], capture_output=True, text=True).stdout.strip():
        print("⚠️  iTerm2 is running — QUIT it first (Cmd-Q), then re-run from Terminal.app.")
        sys.exit(1)

    with open(PLIST, "rb") as f:
        d = plistlib.load(f)

    changed = 0
    for prof in d.get("New Bookmarks", []):
        layout = prof.get("Status Bar Layout")
        if not isinstance(layout, dict):
            continue
        for comp in layout.get("components", []):
            if not is_claude(comp):
                continue
            knobs = comp.setdefault("configuration", {}).setdefault("knobs", {})
            knobs["base: priority"] = PRIORITY
            knobs["base: compression resistance"] = COMPRESSION_RESISTANCE
            knobs["minwidth"] = MINWIDTH
            changed += 1
            print(f"  set knobs on '{prof.get('Name')}' / {comp.get('class')}")

    if not changed:
        print("No Claude components found in any profile layout. Add them first.")
        sys.exit(1)

    with open(PLIST, "wb") as f:
        plistlib.dump(d, f)
    subprocess.run(["killall", "cfprefsd"], capture_output=True)
    print(f"✅ Updated {changed} component(s). Reopen iTerm2.")


if __name__ == "__main__":
    main()
