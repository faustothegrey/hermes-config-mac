# Shuttle iTerm2 config + hostname labels (addendum, Nov 2026)

Supersedes the terminal/theme/name fields in `templates/shuttle.json` and the
roster in `references/shuttle-ssh-config.md` with the values confirmed against the
live network this session.

## iTerm2 settings (the non-obvious gotchas)

The stock `~/.shuttle.json` sample ships `"terminal": "Terminal.app"` and
`"default_theme": "Homebrew"` — both wrong for a real iTerm2 setup:

- `"terminal": "iTerm"` (NOT `iTerm2`, NOT `iTerm.app`).
- `"iTerm_version": "nightly"` for modern iTerm2 3.x. `"stable"` targets the OLD
  iTerm 2.x AppleScript and fails silently on iTerm2 v3 — the window opens and
  immediately closes. See upstream issue fitztrev/shuttle#176.
- `"default_theme"` MUST equal the user's real iTerm2 default profile name
  (case-sensitive). `"Homebrew"` is the *author's* profile, not a standard value;
  a mismatch reproduces the open-then-close bug.
- Discover the real default profile name:
  ```bash
  defaults read com.googlecode.iterm2 "Default Bookmark Guid"
  plutil -p ~/Library/Preferences/com.googlecode.iterm2.plist | grep -iE '"Name"|"Guid"'
  ```
  then match the default Guid to a `Name`. (This user's default profile: `Default`.)

## Display label = hostname, not peer id

The user wants menu labels to read the peer **hostname** (`Stella`, `Charon`, …)
while `cmd` still runs the `~/.ssh/config` alias (`ssh peer141`). `name` and `cmd`
are independent fields.

## Corrected hostnames (live `hostname` probe)

| Peer | hostname (was) | hostname (now) |
|------|----------------|----------------|
| peer70 | — | Charon |
| peer84 | N56VV | Machiste |

peer128 = `192.168.178.112` (NOT `.128`); peer60/105/106 were offline so their
hostnames remain unconfirmed.
