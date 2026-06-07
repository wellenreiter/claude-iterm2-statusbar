#!/usr/bin/env python3
"""iTerm2 status bar components for Claude Code: rate limits, model, effort.

Reads ~/.cache/claude/statusbar.json (written by the Claude Code statusLine
command) and renders three independent, intentionally SHORT components.

Why short: an iTerm2 status bar slot defaults to minwidth=0 + low compression
resistance, so a wide value gets squeezed to width 0 and vanishes on reflow.
Keep every rendered string compact and it stays put.
"""
import iterm2
import json
import os
import datetime

CACHE_FILE = os.path.expanduser("~/.cache/claude/statusbar.json")
LOG_FILE = os.path.expanduser("~/.cache/claude/claude_statusbar_boot.log")


def _ts():
    return datetime.datetime.now().strftime("%H:%M:%S")


try:
    with open(LOG_FILE, "w") as _f:
        _f.write(f"{_ts()} process start (module import)\n")
except Exception:
    pass


def log(msg):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{_ts()} {msg}\n")
    except Exception:
        pass


def load():
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def circle(pct):
    # color by usage threshold, matching the statusLine palette
    if pct >= 90:
        return "🔴"
    if pct >= 70:
        return "🟡"
    return "🟢"


def render_limits():
    d = load()
    p5 = d.get("limit_5h_pct")
    p7 = d.get("limit_7d_pct")
    if p5 is None and p7 is None:
        return "Claude —"
    parts = []
    if p5 is not None:
        r5 = d.get("limit_5h_reset") or ""
        s = f"5h {circle(int(p5))} {int(p5)}%"
        if r5:
            s += f" ({r5})"
        parts.append(s)
    if p7 is not None:
        day = (d.get("limit_7d_day") or "")[:2]
        r7 = d.get("limit_7d_reset") or ""
        when = " ".join(x for x in (day, r7) if x)
        s = f"7d {circle(int(p7))} {int(p7)}%"
        if when:
            s += f" ({when})"
        parts.append(s)
    return " · ".join(parts)


def render_model():
    d = load()
    m = d.get("model")
    return f"🤖 {m}" if m else "🤖 —"


EFFORT_LABELS = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "xhigh": "X-High",
    "max": "Max",
}


def render_effort():
    d = load()
    e = d.get("effort")
    if not e:
        return ""
    return f"🧠 {EFFORT_LABELS.get(str(e).lower(), str(e).capitalize())}"


async def main(connection):
    log("main() entered, connection established")

    specs = [
        ("Claude Limits", "Claude 5h/7d rate-limit usage",
         "5h 🟡 70% (11:40) · 7d 🟢 6% (So 14:00)", "com.pmi.claude.ratelimits", render_limits),
        ("Claude Model", "Active Claude model",
         "🤖 Opus 4.8", "com.pmi.claude.model", render_model),
        ("Claude Effort", "Active reasoning effort",
         "🧠 High", "com.pmi.claude.effort", render_effort),
    ]

    first = {"done": False}

    for short_desc, detail, exemplar, ident, fn in specs:
        component = iterm2.StatusBarComponent(
            short_description=short_desc,
            detailed_description=detail,
            knobs=[],
            exemplar=exemplar,
            update_cadence=30,
            identifier=ident,
        )

        def make_cb(render_fn, name):
            @iterm2.StatusBarRPC
            async def callback(knobs):
                val = render_fn()
                if not first["done"]:
                    log(f"FIRST callback ({name}) -> {val!r}  (==> BOUND & RENDERING)")
                    first["done"] = True
                return val
            return callback

        await component.async_register(connection, make_cb(fn, short_desc))
        log(f"registered {ident}")


iterm2.run_forever(main)
