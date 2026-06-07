# claude-iterm2-statusbar

Show your **Claude Code** state in the **iTerm2 status bar** — live rate-limit
usage, the active model, and the reasoning effort:

```
5h 🟢 2% (11:40) · 7d 🟢 7% (So 14:00)      🤖 Opus 4.8      🧠 X-High
```

Three small, independent components. Color comes from emoji (🟢🟡🔴 by usage), so
no iTerm2 color knobs are required and it matches an emoji statusLine.

---

## How it works

Claude Code pipes a JSON object to your **statusLine** command on every update.
That JSON already contains the model, the effort level, and your rate-limit usage.

```
Claude Code ──stdin JSON──▶ statusline-command.sh ──writes──▶ ~/.cache/claude/statusbar.json
                                                                      │ reads (every 30s)
                                          iTerm2 status bar ◀── claude_statusbar.py (Python API)
```

`claude_statusbar.py` runs as an iTerm2 **AutoLaunch** script and registers three
custom status bar components that render the cached values.

---

## Requirements

- macOS + **iTerm2** 3.5+ (Python API enabled: *Settings → General → Magic →
  Enable Python API*)
- The iTerm2 Python runtime (iTerm2 offers to install it the first time you run a
  script) and the `iterm2` package in that runtime
- **`jq`** on your `PATH` (`brew install jq`)
- **Claude Code** with a `statusLine` configured

---

## Install

### 1. Drop in the component script

```sh
mkdir -p ~/Library/Application\ Support/iTerm2/Scripts/AutoLaunch
cp claude_statusbar.py ~/Library/Application\ Support/iTerm2/Scripts/AutoLaunch/
```

> If `iterm2` isn't importable in the iTerm2 runtime, install it:
> ```sh
> ~/Library/Application\ Support/iTerm2/iterm2env/versions/*/bin/pip install iterm2
> ```

### 2. Make your statusLine write the cache

- **No statusLine yet?** Copy the ready-made one:
  ```sh
  cp statusline-command.example.sh ~/.claude/statusline-command.sh
  ```
  and in `~/.claude/settings.json`:
  ```json
  { "statusLine": { "type": "command", "command": "sh ~/.claude/statusline-command.sh" } }
  ```
- **Already have one?** Paste the contents of `statusline-cache-snippet.sh` into it
  (anywhere after you read stdin into `$input`).

### 3. Start the script and add the components

1. Fully **quit and reopen iTerm2** (so AutoLaunch runs the script).
2. *Settings → Profiles → [your active profile] → Session → **Configure Status Bar***.
3. Drag **Claude Limits**, **Claude Model**, **Claude Effort** from the palette into
   the active row. Click **OK**.
4. **Quit and reopen iTerm2 once more.** ← Don't skip this. See *Gotcha #1*.

Open a Claude Code session in that terminal — within ~30s the components fill in.

---

## ⚠️ Two gotchas (read these — they cost hours)

### #1 — Binding happens at *registration time*

iTerm2 binds a running script's component to a status-bar **slot only when the
script registers** — it does **not** retroactively bind to a slot you add later.
So if the script is already running and you *then* drag a component into the bar,
it stays blank.

**Fix:** add the slots to the profile, then **cold-restart iTerm2** so the
AutoLaunch script registers *after* the slots exist. (At startup iTerm2 builds the
window's bar first, then runs AutoLaunch — the correct order.)

> The component-config dialog shows the component's hardcoded **`exemplar`** text,
> not live data. It looks like it's working even when nothing is bound. Trust the
> actual bar, not the dialog.

### #2 — Wide values get compressed to nothing

A status-bar slot defaults to `minwidth=0` and low compression resistance. A wide
value gets squeezed to **width 0** on layout reflow and disappears (it may flash
once, then vanish). Symptom: "it worked for a second, then nothing."

**Fix:** keep every rendered string **short** — which is exactly why these
components render `5h 🟢 2%` and not `5h ████░░░░ 2% 11:40`. If you must go wide,
raise the slot's *minimum width* / priority in the component's **Advanced** config
(stored in the profile, not settable from the script).

---

## Customize

All rendering is in `claude_statusbar.py`:

- **Thresholds / colors** — edit `circle()` (default: 🟢 <70%, 🟡 70–89%, 🔴 ≥90%).
- **Effort labels** — edit `EFFORT_LABELS` (`xhigh → "X-High"`, etc.).
- **Format** — edit `render_limits()` / `render_model()` / `render_effort()`.
  Keep it short (Gotcha #2). Re-register after edits: restart iTerm2, or relaunch
  the script (see Troubleshooting).

---

## Troubleshooting

**Nothing shows.** Check the boot log — the script writes it on every start:

```sh
cat ~/.cache/claude/claude_statusbar_boot.log
```

- A `FIRST callback ... ==> BOUND & RENDERING` line ⇒ iTerm2 bound and is polling.
  If you still see nothing, it's Gotcha #2 (too wide) or the component isn't in the
  active profile's bar.
- Only `registered ...` with **no** `FIRST callback` ⇒ the component is registered
  but not bound to a visible slot ⇒ Gotcha #1 (add slot, then cold-restart).

**Check the cache is being written:**

```sh
cat ~/.cache/claude/statusbar.json
```

If it's stale, your statusLine isn't writing it — re-check step 2. The cache only
updates while a Claude Code session is active in that terminal.

**Re-register without a full restart** (e.g. after editing the script). iTerm2 can
hand a script a fresh API cookie, so you can relaunch it connected:

```sh
PYBIN=~/Library/Application\ Support/iTerm2/iterm2env/versions/*/bin/python3
pkill -f claude_statusbar.py
COOKIE=$(osascript -e 'tell application "iTerm2" to request cookie')
ITERM2_COOKIE="$COOKIE" $PYBIN ~/Library/Application\ Support/iTerm2/Scripts/AutoLaunch/claude_statusbar.py &
```

---

## Files

| File | Purpose |
|------|---------|
| `claude_statusbar.py` | iTerm2 AutoLaunch script — registers the 3 components |
| `statusline-cache-snippet.sh` | Paste into an existing statusLine to write the cache |
| `statusline-command.example.sh` | Complete minimal statusLine if you don't have one |

## License

MIT — see [LICENSE](LICENSE).
