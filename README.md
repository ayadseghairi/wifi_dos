# WiFi DDoS Tool

A passive Wi-Fi discovery and deauthentication attack tool using Python3 and Aircrack-ng suite.

## Description

This tool uses `airodump-ng` and `aireplay-ng` from the Aircrack-ng suite to perform the following functions:

- **Passive Scanning**: Discover nearby Wi-Fi access points without transmitting any signals
- **Information Display**: Show detailed network information (BSSID, channel, signal strength, ESSID)
- **Deauthentication Attacks**: Execute DDoS attacks on selected access points to disconnect devices

## Requirements

### Required Software
```bash
sudo apt update
sudo apt install aircrack-ng wireless-tools iw
```

### System Permissions
- Must be run with root privileges
- Wireless adapter that supports monitor mode

## Installation

1. Clone or download the code:
```bash
git clone <repository-url>
cd wif
```

2. Ensure Python3 is available:
```bash
python3 --version
```

## Usage

### Running the Tool
```bash
sudo python3 wifiddos.py
```

### Execution Steps

1. **Select Network Interface**:
   - The tool will display available wireless network interfaces
   - Choose the number corresponding to the desired interface

2. **Enable Monitor Mode**:
   - The tool will automatically enable monitor mode
   - A new interface may be created (e.g., wlan0mon)

3. **Passive Scanning**:
   - Network scanning will begin automatically
   - Press `Ctrl+C` to stop scanning and proceed to target selection

4. **Target Selection**:
   - A list of discovered networks will be displayed
   - Choose the network number to target or type 'q' to quit

5. **Execute Attack**:
   - Deauthentication attack will begin on the selected network
   - Press `Ctrl+C` to stop the attack

## Features

### Passive Scanning
- No transmitted signals that reveal your presence
- Displays detailed network information:
  - BSSID (Access Point MAC address)
  - Transmission channel
  - Signal strength
  - Network name (ESSID)

### Interface Management
- Automatic detection of wireless network interfaces
- Automatic enable/disable of monitor mode
- Interface status verification before starting attacks

### Data Preservation
- Automatic backup of existing CSV files
- Save scan results in CSV files for later review

## File Structure

```
wif/
├── wifiddos.py          # Main script file
├── README.md            # This file
├── backup_csvs/         # Backup directory (created automatically)
└── scanfile-*.csv       # Scan result files (created automatically)
```

## Common Error Handling

### "No wireless interfaces detected"
- Ensure wireless adapter is connected
- Verify adapter drivers are installed
- Try running `iwconfig` to check interfaces

### "This script requires root"
- Run the tool using `sudo` or as root user

### "No such device"
- Monitor mode interface may have been disabled
- The tool will attempt to re-enable it automatically

### "No such BSSID available"
- Ensure the target access point is still active
- May need to rescan for updated information

## Configuration

Settings can be modified at the beginning of the file:

```python
AIRODUMP_PREFIX = "scanfile"    # Scan file name prefix
AIRODUMP_INTERVAL = 1.0         # Display update interval (seconds)
BACKUP_DIR = "backup_csvs"      # Backup directory name
```

## Legal Warnings

⚠️ **Important Warning**: This tool is intended for educational purposes and security testing only.

- Do not use this tool on networks you do not own or do not have explicit permission to test
- Using this tool on others' networks without permission may be illegal
- The developer is not responsible for any illegal use of this tool

## Features Overview

- **Passive Discovery**: Non-intrusive network detection
- **Real-time Display**: Live updates of discovered networks
- **Graceful Interruption**: Proper Ctrl+C handling for user control
- **Automatic Cleanup**: Monitor mode management and cleanup
- **Channel Switching**: Automatic tuning to target AP channel
- **CSV Export**: Scan results saved for analysis

## Technical Details

### Dependencies
- Python 3.x
- Aircrack-ng suite (airodump-ng, aireplay-ng, airmon-ng)
- Standard Linux wireless tools (iwconfig, iw)

### Supported Interfaces
- Most USB Wi-Fi adapters with monitor mode support
- Built-in wireless cards (if monitor mode capable)
- Common interface patterns: wlan*, wlp*, etc.

## License

This project is for educational purposes. Use
