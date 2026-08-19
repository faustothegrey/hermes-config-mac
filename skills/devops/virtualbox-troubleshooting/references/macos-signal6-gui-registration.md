# Worked case: orphaned VBoxSVC → SIGABRT at GUI registration (macOS 26, VirtualBox 7.2.6)

Environment: macOS 26.5.2 (Darwin 25.5.0), VirtualBox 7.2.6 r172322, Intel MacBookPro16,2 (darwin.amd64).
Two VMs (LinuxMint, Linux Lite) both failed identically: "The virtual machine 'X' has
terminated unexpectedly during startup because of signal 6" + NS_ERROR_FAILURE + MachineWrap.

## Timeline (local CEST)
- 08:43 — VBoxSVC (pid 85707) starts; first GUI launch of LinuxMint works, runs 19 min
- 09:02 — clean shutdown
- 09:02:34 → 09:14:44 — 5 restart attempts, all SIGABRT within ~0.5 s
- Every subsequent attempt (7 crash reports total, incl. Linux Lite) identical

## Evidence chain
1. `~/VirtualBox VMs/LinuxMint/Logs/VBox.log` tail showed a CLEAN session end
   ("PoweredOff") — misleading; it was the previous successful run. The current
   attempts never got far enough to write a fresh engine log.
2. `~/Library/VirtualBox/VBoxSVC.log` showed the real story:
   `Launched VM: ... frontend: GUI/Qt name: LinuxMint` followed ~0.5 s later by
   Watcher `ERROR [COM]: ... terminated unexpectedly during startup because of signal 6`.
   Five such pairs. Also: `SUP: In driverless mode`, `failed to create vboxnet0..4`
   (benign), recurring `UEFI NVRAM file is not existing` (benign — legacy BIOS VM).
3. Crash reports at `~/Library/Logs/DiagnosticReports/VirtualBoxVM-2026-07-31-09*.ips`
   (7 total, root-owned; also check /Library/Logs/DiagnosticReports/).

## Crash stack (identical in all 7 reports)
```
libsystem_kernel.dylib  __pthread_kill +10
libsystem_pthread.dylib pthread_kill +259
libsystem_c.dylib       abort +126
HIServices               ___RegisterApplication_block_invoke +14351
libdispatch.dylib       _dispatch_client_callout / _dispatch_once_callout
HIServices               _RegisterApplication +107
HIServices               GetCurrentProcess +23
AppKit                   -[NSMenuBarPresentationInstance _getAggregateUIMode:withOptions:] ...
AppKit                   _NSInitializeAppContext
AppKit                   -[NSApplication init]
UICommon.dylib           UICocoaApplication::UICocoaApplication(bool)
VirtualBoxVM             TrustedMain +191
dyld                     start
```
Interpretation: VirtualBoxVM aborts inside macOS's app-registration path
(GetCurrentProcess → RegisterApplication → abort), i.e. while connecting to the
WindowServer — before any VM/guest code executes.

## Root cause confirmation
All 7 crash reports: `parentProc=VBoxSVC parentPid=85707 responsiblePid=85705`.
PID 85705 was dead at crash time (ps: no such process). VBoxSVC 85707's PPID was 1
(launchd) — orphaned after its original parent GUI exited. Its children inherited a
broken responsible-process chain, so macOS's RegisterApplication aborted them.

## Fix (verified)
```
kill -9 85707            # SIGTERM alone was ignored (Manager GUI holds it alive)
VBoxManage startvm LinuxMint --type gui
```
Fresh VBoxSVC (pid 46519) respawned automatically; VirtualBoxVM GUI process stayed
alive; `VBoxManage list runningvms` confirmed; no new .ips after the fix.

## Reusable one-liner for the user
`killall VBoxSVC` (or fully quit VirtualBox with Cmd+Q, which also kills it) — reopening
the app respawns a clean daemon. No data loss, no config change.

## Differential test that proved environmental scope
`VBoxManage startvm "Linux Lite" --type gui` also crashed with signal 6 → not a
per-VM config issue → host/daemon layer. And headless start of LinuxMint succeeded →
engine + .vdi healthy → frontend layer only.
