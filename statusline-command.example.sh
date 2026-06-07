#!/bin/sh
# Minimal, self-contained Claude Code statusLine command.
# - prints a one-line status to Claude Code's footer
# - writes ~/.cache/claude/statusbar.json for the iTerm2 components
#
# Install: copy to ~/.claude/statusline-command.sh and set in ~/.claude/settings.json:
#   "statusLine": { "type": "command", "command": "sh ~/.claude/statusline-command.sh" }
#
# Requires: jq. Already have your own statusLine? Don't use this file — just paste
# statusline-cache-snippet.sh into yours instead.

input=$(cat)

model=$(echo "$input"  | jq -r '.model.display_name // "Unknown"')
effort=$(echo "$input" | jq -r '.effort.level // empty')
rl_5h_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty' | awk 'NF{printf "%.0f",$1}')
rl_7d_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty' | awk 'NF{printf "%.0f",$1}')
rl_5h_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
rl_7d_reset=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

rl_5h_time=$(date -r "$rl_5h_reset" "+%H:%M" 2>/dev/null || date -d "@$rl_5h_reset" "+%H:%M" 2>/dev/null)
rl_7d_day=$(date  -r "$rl_7d_reset" "+%A"    2>/dev/null || date -d "@$rl_7d_reset" "+%A"    2>/dev/null)
rl_7d_time=$(date -r "$rl_7d_reset" "+%H:%M" 2>/dev/null || date -d "@$rl_7d_reset" "+%H:%M" 2>/dev/null)

mkdir -p "$HOME/.cache/claude"
jq -n \
  --arg model "$model" \
  --arg effort "$effort" \
  --argjson l5 "${rl_5h_pct:-null}" \
  --argjson l7 "${rl_7d_pct:-null}" \
  --arg r5 "${rl_5h_time:-}" \
  --arg d7 "${rl_7d_day:-}" \
  --arg r7 "${rl_7d_time:-}" \
  '{model:$model, effort:$effort, limit_5h_pct:$l5, limit_7d_pct:$l7,
    limit_5h_reset:$r5, limit_7d_day:$d7, limit_7d_reset:$r7}' \
  > "$HOME/.cache/claude/statusbar.json" 2>/dev/null

# Footer line shown inside Claude Code itself
if [ -n "$effort" ]; then
  printf "🤖 %s | 🧠 %s | 5h %s%% · 7d %s%%" "$model" "$effort" "${rl_5h_pct:-0}" "${rl_7d_pct:-0}"
else
  printf "🤖 %s | 5h %s%% · 7d %s%%" "$model" "${rl_5h_pct:-0}" "${rl_7d_pct:-0}"
fi
