---
name: virtualbox-troubleshooting
description: Diagnose VirtualBox VM startup failures — "terminated unexpectedly during startup because of signal 6" (SIGABRT), NS_ERROR_FAILURE (0x80004005), MachineWrap errors — on macOS and other hosts. Read VBox.log / VBoxSVC.log, parse macOS .ips crash reports, isolate GUI-frontend vs VM-engine crashes, and fix orphaned VBoxSVC daemon problems.
---

# VirtualBox Troubleshooting

## When to use
- VM fails to start with: "The virtual machine 'X' has terminated unexpectedly during startup because of signal 6" + `NS_ERROR_FAILURE (0x80004005)` + `Component: MachineWrap`
- VM aborts instantly at launch; exit code 1 / SIGABRT / "Abort trap: 6"
- Any VirtualBox VM won't boot but the host itself is fine

## Key mental model
**Signal 6 (SIGABRT) at startup is usually NOT a VM/disk/config problem.** It means a VirtualBox process (often the GUI window frontend `VirtualBoxVM`, or the `VBoxHeadless` engine) called `abort()` before or during early init. The guest OS and its .vdi are usually untouched.

**First differential — headless vs GUI.**
```
VBoxManage startvm <VM> --type headless   # engine only, no window
VBoxManage startvm <VM> --type gui        # engine + window frontend
```
- Headless works + GUI crashes → problem is in the window/frontend layer (macOS: WindowServer registration). VM is fine.
- Both crash → problem in the engine, config, or disk image.

## Evidence locations (macOS)
1. `~/Library/VirtualBox/VBoxSVC.log` — the daemon log. Shows every launch attempt, PID, and the Watcher error lines. **Check this FIRST** — it survives even when the VM log never opens.
2. `~/VirtualBox VMs/<VM>/Logs/VBox.log` — per-VM engine log. Rotates (VBox.log.N). If the crash happens before the engine starts, this file may only contain the PREVIOUS successful session — the tail looks clean and misleading.
3. `~/Library/Logs/DiagnosticReports/VirtualBoxVM-*.ips` — macOS crash reports. **The definitive evidence** for frontend aborts. Check `/Library/Logs/DiagnosticReports/` too (root-owned).
4. `~/Library/VirtualBox/VBoxHardening.log` — only exists on hardening failures; absence is normal.

## Reading macOS .ips crash reports
.ips files are JSON: line 1 = header dict, then the body dict. Parse programmatically:
```python
import json
with open(path) as f:
    data = json.loads(f.read().split('\n', 1)[1])   # body = everything after first line
t = data['threads'][data['faultingThread']]
for fr in t['frames'][:20]:
    img = data['usedImages'][fr.get('imageIndex')]['name'] if fr.get('imageIndex') is not None else '?'
    print(f"{img:30s} {fr.get('symbol','?')} +{fr.get('symbolLocation',0)}")
```
Key fields: `exception` (type/signal), `termination.indicator` ("Abort trap: 6"), `faultingThread`, `parentProc` / `parentPid`, `responsiblePid`, `procLaunch` (start time — compare with launch attempts in VBoxSVC.log).

## Known root cause: orphaned VBoxSVC (macOS)
**Symptom:** all crash reports show the same `responsiblePid` that no longer exists, and VBoxSVC's PPID is 1 (launchd) with an old start time.
**Mechanism:** VBoxSVC (the COM daemon) outlived the GUI process that spawned it. It gets re-parented to launchd. Every VM window it spawns inherits a broken "responsible process" chain → `HIServices.___RegisterApplication_block_invoke` calls `abort()` → SIGABRT. Confirms with any number of VMs crashing identically — it's environmental, not per-VM.
**Fix (non-destructive, no data touched):**
```
kill -9 <VBoxSVC pid>     # SIGTERM is ignored while the Manager GUI holds it
VBoxManage startvm <VM> --type gui   # or relaunch from the VirtualBox Manager GUI
```
A fresh VBoxSVC respawns automatically with a live responsible-process chain. User-level alternative: fully quit VirtualBox (Cmd+Q kills VBoxSVC too), then reopen.

## General fixes checklist (in order)
1. Restart VBoxSVC (`killall VBoxSVC` or Cmd+Q VirtualBox + reopen) — fixes the orphaned-daemon class
2. Try headless start to confirm engine health
3. Check `VBoxManage list vms` + VM .vbox XML for obvious corruption (compare with `.vbox-prev`)
4. Check host free disk (`df -h /`) and that the .vdi exists with sane size
5. Look for missing Extension Pack in VBox.log header ("Installed Extension Packs: None installed") — needed for USB 2.0/EHCI etc.
6. Only if all else fails: reinstall VirtualBox (same version or newer) — refreshes app registration

## Pitfalls
- **NEM "AppleHV error" / "UNDEFINED (AppleHV error)" lines in VBox.log are NORMAL noise** on macOS (especially Apple Silicon / newer macOS). Do not chase them. Real errors are `VERR_*` in the console or an abort in the crash report.
- "Firmware type: failed - VERR_NOT_SUPPORTED" at log start is also benign on macOS.
- `VBOX_E_OBJECT_NOT_FOUND ... The UEFI NVRAM file is not existing` in VBoxSVC.log is noise when the VM uses legacy BIOS (no UEFI) — expected, ignore.
- VBox.log tail showing a clean "PoweredOff" does NOT mean the current start worked — it may be the previous session. Always correlate timestamps (VBoxSVC.log launch attempts vs crash report `procLaunch`).
- A single `VBoxManage startvm` that succeeds doesn't prove GUI works — verify with `VBoxManage list runningvms` after a few seconds AND check no new `.ips` appeared.
- Don't diagnose per-VM when multiple VMs crash identically — run the differential; shared failure ⇒ host/daemon problem.

## Verification
- `VBoxManage list runningvms` shows the VM
- `ps aux | grep VirtualBoxVM` shows a live GUI process (not `?? Z` zombie)
- No NEW `VirtualBoxVM-*.ips` files since the fix
- VM stays up past the first ~30s (crash-on-startup dies in <1s)

## References
- `references/macos-signal6-gui-registration.md` — full worked case: crash stack, log evidence, root-cause chain for the orphaned-VBoxSVC / RegisterApplication abort
