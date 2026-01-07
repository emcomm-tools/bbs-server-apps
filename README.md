# BBS Server Apps for LinBPQ

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A collection of Python-based applications that extend LinBPQ's functionality, providing additional services accessible via packet radio. These apps run as inetd services and integrate seamlessly with LinBPQ's Telnet port.

## 📡 Available Apps

| App | Port | Description |
|-----|------|-------------|
| **WQF** | 63000 | Weather Quebec Forecast - Environment Canada weather data |
| **QRZ** | 63010 | QRZ.com callsign lookup (requires subscription) |
| **HAMQSL** | 63020 | Solar propagation data from HamQSL |
| **SPACE** | 63030 | Space weather report (solar flares, geomagnetic storms) |
| **RELAY** | 63040 | SMTP email relay gateway |
| **WIKI** | 63050 | Offline Wikipedia/ZIM file reader |
| **ISDE** | 63060 | ISDE Canadian amateur callsign database |
| **CLAUDE** | 63070 | Claude AI gateway (requires Anthropic API key) |
| **GEMINI** | 63080 | Google Gemini AI gateway (requires Google AI API key) |
| **BLOG** | 63090 | Blog over HF - PostgreSQL-based blogging system |

## 🚀 Quick Start

### Prerequisites

- Debian/Ubuntu-based Linux system
- LinBPQ installed and configured
- Python 3.8 or higher
- inetd (inetutils-inetd)
- Git

### Installation

1. **Clone the repository:**

```bash
cd ~/.local/share/emcomm-tools/bbs-server
git clone https://github.com/emcomm-tools/bbs-server-apps.git
cd bbs-server-apps
```

2. **Run the installer:**

```bash
sudo ./install.sh
```

3. **Select the apps you want to enable** using the dialog menu.

4. **Configure your LinBPQ** with the provided configuration snippet.

5. **Restart your BPQ node.**

## 📖 Detailed Documentation

See [INSTALL.md](INSTALL.md) for comprehensive installation and configuration instructions.

## 🔧 Manual Configuration

If you prefer manual setup, here's what you need to do:

### 1. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Add to /etc/services

```
wqf             63000/tcp                       # Weather Quebec Forecast
qrz             63010/tcp                       # QRZ Callsign Lookup
hamqsl          63020/tcp                       # Solar Data
space           63030/tcp                       # Space Weather Report
relay           63040/tcp                       # SMTP Relay
wiki            63050/tcp                       # Offline Wiki
isde            63060/tcp                       # ISDE Database
claude          63070/tcp                       # Claude AI
gemini          63080/tcp                       # Gemini AI
blog            63090/tcp                       # Blog over HF
```

### 3. Add to /etc/inetd.conf

```
#:HAM-RADIO: amateur-radio BBS services

wqf     stream  tcp     nowait  USERNAME     /path/to/apps/wqf.py
qrz     stream  tcp     nowait  USERNAME     /path/to/apps/qrz.py
# ... add more as needed
```

### 4. Restart inetd

```bash
sudo systemctl restart inetutils-inetd
```

### 5. Configure LinBPQ

Add the CMDPORT numbers to your Telnet PORT section and add APPLICATION entries.

## 🔒 Configuration Files

Each app that requires configuration has an `.example` template file. Copy it to the actual filename and edit with your credentials:

| App | Config File | Notes |
|-----|-------------|-------|
| QRZ | `config.py` | Requires QRZ.com XML subscription |
| Claude | `claude_config.json` | Requires Anthropic API key |
| Gemini | `gemini_config.json` | Requires Google AI API key |
| SMTP | `smtp_config.json` | Email server credentials |
| Wiki | `wiki_config.json` | ZIM file paths |
| Blog | `blog-app/blog_config.json` | PostgreSQL connection |

## 🧪 Testing

Test any app locally with telnet:

```bash
telnet localhost 63000   # Test WQF
telnet localhost 63010   # Test QRZ
# etc.
```

## 📁 Directory Structure

```
bbs-server-apps/           # Repository root
├── install.sh             # Main installer
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── INSTALL.md             # Detailed installation guide
├── LICENSE                # GPL v3
├── .gitignore
├── templates/
│   └── bpq32.apps.cfg.example  # BPQ config template
└── apps/                  # Application scripts
    ├── wqf.py             # Weather Quebec Forecast
    ├── qrz.py             # QRZ callsign lookup
    ├── hamqsl.py          # Solar data
    ├── space.py           # Space weather
    ├── smtp.py            # SMTP relay
    ├── wiki.py            # Offline Wikipedia
    ├── isde.py            # Canadian callsign DB
    ├── claude_gateway.py  # Claude AI
    ├── gemini_gateway.py  # Gemini AI
    ├── config.py.example  # QRZ config template
    ├── *_config.json.example  # Other config templates
    ├── wiki/              # Wiki module
    ├── isde/              # ISDE JSON data files
    └── blog-app/          # Blog application
```

## 🤝 Contributing

Contributions are welcome! This project follows the Ham Radio spirit of sharing and collaboration.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **TheTechPrepper** - Original EmComm-Tools OS Community project
- **LinBPQ** by G8BPQ - The backbone BBS system
- All amateur radio operators who test and provide feedback

## 📞 Contact

- **Author:** Sylvain Deguire (VA2OPS)
- **Project:** [EmComm-Tools](https://github.com/emcomm-tools)

---

*73 de VA2OPS* 📻
