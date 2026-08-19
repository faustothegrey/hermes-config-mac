# Private Wi-Fi Address & IP Change Diagnosis

## Session Context (2026-07-09)

Fausto noticed his MacBook Pro IP changed from 192.168.178.128 (2.4GHz WiFi) to 192.168.178.133 (5GHz WiFi) after switching bands. The root cause: macOS Private Wi-Fi Address generates different randomized MAC addresses per SSID, so each band gets a different DHCP lease.

## Hardware Specs

- **Machine:** MacBook Pro (macOS 26.5.1)
- **Wi-Fi interface:** en0
- **Hardware MAC:** `88:66:5a:4f:a5:3f`
- **Current MAC (on 5GHz):** `96:46:16:fa:ee:04`
- **Subnet:** 192.168.178.0/24

## Diagnosis Commands

```bash
# Hardware MAC (permanent)
networksetup -getmacaddress en0

# Current active MAC (may be randomized)
ifconfig en0 | awk '/ether/{print $2}'

# Current IP
ifconfig en0 | grep "inet " | grep -v 127.0.0.1

# Check Private Wi-Fi Address status
# (per-network setting, not directly readable via CLI on macOS 26)
# Check if PrivateMACAddressModeSystemSetting is 0 (per-network) or 1 (system-wide)
defaults read /Library/Preferences/SystemConfiguration/com.apple.airport.preferences.plist 2>/dev/null \
  | grep -E "PrivateMACAddress"

# Current SSID
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I \
  | awk '/ SSID/{print $2}'
```

## Root Cause Map

```
Separate SSIDs for 2.4GHz and 5GHz
  → macOS Private Wi-Fi Address ON
  → Different randomized MAC per SSID
  → DHCP sees different client → different IP lease
  → User sees IP change when switching bands
```

## Solutions (in preference order)

### 1. Disable Private Wi-Fi Address (recommended)
System Settings → Wi-Fi → click network name → Details → turn OFF "Private Wi-Fi Address".
Then set DHCP reservation on router for the hardware MAC.

### 2. Static IP on Mac
System Settings → Wi-Fi → Details → TCP/IP → Configure IPv4 → Manually.
Band-agnostic but loses DHCP convenience (DNS, gateway auto-config).

### 3. Unified SSID
Configure router to use same SSID for both 2.4GHz and 5GHz bands.
macOS treats it as one network → one randomized MAC → one IP.
Requires router admin access.

## Key Insight

On a home LAN, Private Wi-Fi Address is more useful on public hotspots than on trusted networks. Disabling it for the home SSID + adding a DHCP reservation for the hardware MAC gives stable IPs across both bands without losing the privacy feature for other networks.