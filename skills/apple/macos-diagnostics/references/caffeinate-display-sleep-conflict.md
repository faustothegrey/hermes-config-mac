# Caffeinate / Display Sleep Conflict

## Scenario

L'utente imposta `displaysleep 5` via pmset ma il display non si oscura mai. La verifica con `pmset -g` mostra:

```
displaysleep         5 (display sleep prevented by caffeinate)
```

## Diagnostic Path

### 1. Check current pmset

```bash
pmset -g | grep displaysleep
```

Se appare `(display sleep prevented by caffeinate)` — una o più istanze di `caffeinate -d` stanno forzando il display acceso.

### 2. Find caffeinate processes

```bash
ps aux | grep caffeinate | grep -v grep
```

Output tipico:
```
fausto  34303  0.0  0.0  ... caffeinate -d -i -t 86400
```

I flag:
- `-d`: previene display sleep
- `-i`: previene idle sleep
- `-t 86400`: timeout 24h (se KeepAlive, il timeout è irrilevante — respawna)

### 3. Kill and check if it respawns

```bash
killall caffeinate
```

Se dopo qualche secondo riappare con un nuovo PID, c'è un **launchd agent con KeepAlive** che lo respawna.

### 4. Find the source

```bash
# Check launchd
launchctl list | grep caffeinate
# → com.peerXXX.caffeinate

# Find the plist
search_files(pattern="caffeinate", path="~/Library/LaunchAgents", target="content")
```

La plist tipicamente ha:

```xml
<key>RunAtLoad</key>
<true/>
<key>KeepAlive</key>
<true/>
<key>ProgramArguments</key>
<array>
    <string>/usr/bin/caffeinate</string>
    <string>-d</string>
    <string>-i</string>
    <string>-t</string>
    <string>86400</string>
</array>
```

### 5. Fix: unload the launch agent

```bash
launchctl bootout gui/$(id -u)/com.peerXXX.caffeinate
```

Per riabilitarlo in futuro:
```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.peerXXX.caffeinate.plist
```

## Prevention

- Se un lauchd agent caffeinate viene creato da una sessione Hermes precedente, non va dimenticato — blocca display sleep finché non viene esplicitamente scaricato.
- Dopo aver modificato `pmset` per display sleep, verifica sempre che non ci siano `(prevented by caffeinate)` nella riga `displaysleep`.

## Full commands to verify the fix

```bash
# Before
pmset -g | grep displaysleep
ps aux | grep caffeinate | grep -v grep

# Unload
launchctl bootout gui/$(id -u)/com.peerXXX.caffeinate

# After — verify
sleep 2
pmset -g | grep displaysleep   # no more "prevented by caffeinate"
ps aux | grep caffeinate | grep -v grep   # should be empty
```