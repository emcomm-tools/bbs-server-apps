# BBS Server Apps - Installation Guide

This guide provides detailed instructions for installing and configuring the BBS Server Apps for LinBPQ.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [LinBPQ Integration](#linbpq-integration)
5. [Individual App Setup](#individual-app-setup)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Uninstallation](#uninstallation)

---

## Prerequisites

### System Requirements

- **Operating System:** Debian 12+ or Ubuntu 22.04+
- **Python:** 3.8 or higher
- **Memory:** 512MB RAM minimum (1GB+ recommended for AI apps)
- **Disk:** 100MB for apps + space for ZIM files if using Wiki

### Required Packages

The installer will automatically install these, but you can install them manually:

```bash
sudo apt update
sudo apt install -y git python3 python3-pip dialog inetutils-inetd
```

### LinBPQ

You must have LinBPQ installed and running with a working Telnet PORT configured.

---

## Installation

### Step 1: Create Directory Structure

```bash
# Create the parent directory if it doesn't exist
mkdir -p ~/.local/share/emcomm-tools/bbs-server

# Navigate to it
cd ~/.local/share/emcomm-tools/bbs-server
```

### Step 2: Clone the Repository

```bash
git clone https://github.com/emcomm-tools/bbs-server-apps.git apps
cd apps
```

### Step 3: Run the Installer

```bash
sudo ./install.sh
```

The installer will:

1. Check and install missing system dependencies
2. Install Python packages from `requirements.txt`
3. Present a menu to select which apps to enable
4. Prompt for configuration (API keys, credentials) for each app
5. Add entries to `/etc/services`
6. Add entries to `/etc/inetd.conf`
7. Restart the inetd service
8. Display the LinBPQ configuration snippet

### Step 4: Configure LinBPQ

After installation, you'll see a configuration snippet. Add this to your LinBPQ configuration file.

---

## Configuration

### Configuration Files

Each app that requires configuration has a template file ending in `.example`:

| Template | Actual Config | Purpose |
|----------|--------------|---------|
| `config.py.example` | `config.py` | QRZ.com credentials |
| `claude_config.json.example` | `claude_config.json` | Claude AI settings |
| `gemini_config.json.example` | `gemini_config.json` | Gemini AI settings |
| `smtp_config.json.example` | `smtp_config.json` | Email relay settings |
| `wiki_config.json.example` | `wiki_config.json` | ZIM file paths |
| `blog-app/blog_config.json.example` | `blog-app/blog_config.json` | Blog database |

### Creating Config Files

The installer will prompt you for credentials and create the config files automatically. To create them manually:

```bash
# Example: QRZ config
cp config.py.example config.py
nano config.py
```

---

## LinBPQ Integration

### BPQ Configuration File Location

The BPQ template files are typically located at:

```
/opt/emcomm-tools/conf/template.d/bbs/
```

### CTEXT Section

Add the available commands to your CTEXT so users know what's available:

```
CTEXT:
Command  Description
?        help
BBS      Connect BBS
CHAT     Chat with users
INFO     Contact info
WQF      QC Forecast
QRZ      CallSign Lookup
HAMQSL   Solar Data
SPACE    Space Weather
RELAY    SMTP Relay
WIKI     Offline Wiki
ISDE     Canadian Callsigns
CLAUDE   Claude AI
GEMINI   Google Gemini AI
BLOG     Blog over HF
***
```

### PORT Section - CMDPORT

Add the app ports to your Telnet PORT's CMDPORT line:

```
PORT
  PORTNUM=2
  ID=Telnet
  DRIVER=Telnet
  CONFIG
  CMDPORT 63000 63010 63020 63030 63040 63050 63060 63070 63080 63090
  # ... rest of config
ENDPORT
```

### APPLICATION Entries

Add APPLICATION entries after your PORT definitions. The HOST number corresponds to the position in CMDPORT (0-indexed):

```
APPLICATION 1,BBS,,YOURCALL-11,ETCBBS,255
APPLICATION 2,CHAT,,YOURCALL-12,ETCCHT,255
APPLICATION 3,WQF,C 2 HOST 0 NOCALL K S
APPLICATION 4,QRZ,C 2 HOST 1 NOCALL K S
APPLICATION 5,HAMQSL,C 2 HOST 2 NOCALL K S
APPLICATION 6,SPACE,C 2 HOST 3 NOCALL K S
APPLICATION 7,RELAY,C 2 HOST 4 NOCALL K S
APPLICATION 8,WIKI,C 2 HOST 5 NOCALL K S
APPLICATION 9,ISDE,C 2 HOST 6 NOCALL K S
APPLICATION 10,CLAUDE,C 2 HOST 7 NOCALL K S
APPLICATION 11,GEMINI,C 2 HOST 8 NOCALL K S
APPLICATION 12,BLOG,C 2 HOST 9 NOCALL K S
```

---

## Individual App Setup

### WQF - Weather Quebec Forecast

**No configuration required.** Fetches weather data from Environment Canada.

```bash
# Test
telnet localhost 63000
```

### QRZ - Callsign Lookup

**Requires:** QRZ.com XML subscription ($29.95/year)

1. Get your subscription at: https://www.qrz.com/i/subscriptions.html
2. Edit `config.py`:

```python
qrz_user = "YOURCALL"
qrz_pass = "your_password"
```

### HAMQSL - Solar Data

**No configuration required.** Fetches data from HamQSL.com.

### SPACE - Space Weather

**No configuration required.** Fetches data from NOAA Space Weather.

### RELAY - SMTP Email Relay

**Requires:** Email account with SMTP access

1. Edit `smtp_config.json`:

```json
{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": true,
    "gateway_email": "yourcall@gmail.com",
    "gateway_password": "your_app_password",
    "gateway_name": "YOURCALL SMTP Gateway"
}
```

**Note for Gmail:** You need to create an "App Password" in your Google Account security settings.

### WIKI - Offline Wikipedia

**Requires:** ZIM files (offline Wikipedia)

1. Download ZIM files from: https://download.kiwix.org/zim/
2. Place them in `~/wikipedia/`
3. Edit `wiki_config.json`:

```json
{
    "zim_files": [
        {
            "name": "English Wikipedia",
            "description": "Simple English Wikipedia",
            "path": "~/wikipedia/wikipedia_en_simple_all_nopic.zim"
        }
    ],
    "default_max_chars": 2000,
    "rf_callsign": "YOURCALL"
}
```

### ISDE - Canadian Callsign Database

**No configuration required.** Uses offline JSON database files included in the `isde/` directory.

### CLAUDE - Claude AI Gateway

**Requires:** Anthropic API key

1. Get your API key at: https://console.anthropic.com/
2. Edit `claude_config.json`:

```json
{
    "default_api_key": "sk-ant-your-key-here",
    ...
}
```

### GEMINI - Google Gemini AI

**Requires:** Google AI API key

1. Get your API key at: https://aistudio.google.com/apikey
2. Edit `gemini_config.json`:

```json
{
    "default_api_key": "your-google-ai-key",
    ...
}
```

### BLOG - Blog over HF

**Requires:** PostgreSQL database

1. Install PostgreSQL if not already installed:

```bash
sudo apt install postgresql postgresql-contrib
```

2. Create database and user:

```bash
sudo -u postgres createuser YOURCALL
sudo -u postgres createdb YOURCALL -O YOURCALL
sudo -u postgres psql -c "ALTER USER YOURCALL WITH PASSWORD 'your_password';"
```

3. Edit `blog-app/blog_config.json`:

```json
{
    "database": {
        "host": "localhost",
        "port": 5432,
        "user": "YOURCALL",
        "password": "your_password",
        "database": "YOURCALL"
    },
    "admin_callsign": "YOURCALL",
    ...
}
```

4. Initialize the database:

```bash
python3 blog-app/setup_blog.py
```

---

## Testing

### Test Individual Apps

```bash
# Weather
telnet localhost 63000

# QRZ (requires config)
telnet localhost 63010

# Solar data
telnet localhost 63020

# Space weather
telnet localhost 63030
```

### Check inetd Status

```bash
# Check if inetd is running
sudo systemctl status inetutils-inetd

# View inetd logs
sudo journalctl -u inetutils-inetd -f
```

### Check Port Listening

```bash
# See which ports are listening
sudo netstat -tlnp | grep -E "630[0-9][0-9]"
```

---

## Troubleshooting

### "Connection refused"

1. Check if inetd is running:
   ```bash
   sudo systemctl status inetutils-inetd
   ```

2. Verify the entry exists in `/etc/inetd.conf`

3. Restart inetd:
   ```bash
   sudo systemctl restart inetutils-inetd
   ```

### "Permission denied"

1. Make sure scripts are executable:
   ```bash
   chmod +x ~/.local/share/emcomm-tools/bbs-server/apps/*.py
   ```

2. Check file ownership matches the user in inetd.conf

### Python Import Errors

Install missing dependencies:
```bash
pip3 install -r requirements.txt --break-system-packages
```

### App Works via Telnet but Not via BPQ

1. Check your CMDPORT includes the correct port number
2. Verify the HOST number in APPLICATION matches the CMDPORT position (0-indexed)
3. Check BPQ logs for errors

---

## Uninstallation

### Remove System Configuration

```bash
cd ~/.local/share/emcomm-tools/bbs-server/apps
sudo ./install.sh --uninstall
```

This removes entries from `/etc/services` and `/etc/inetd.conf` but leaves the app files intact.

### Complete Removal

```bash
# Remove system config
cd ~/.local/share/emcomm-tools/bbs-server/apps
sudo ./install.sh --uninstall

# Remove app files
cd ~/.local/share/emcomm-tools/bbs-server
rm -rf apps
```

---

## Support

- **GitHub Issues:** https://github.com/emcomm-tools/bbs-server-apps/issues
- **EmComm-Tools:** https://github.com/emcomm-tools

---

*73 de VA2OPS* 📻
