#!/bin/bash
#
# BBS Server Apps Installer
# https://github.com/emcomm-tools/bbs-server-apps
#
# Author  : Sylvain Deguire (VA2OPS)
# Date    : January 2026
# Purpose : Install and configure BBS Server Apps for LinBPQ
#
# This installer will:
# 1. Install Python dependencies
# 2. Let you select which apps to enable
# 3. Configure /etc/services and /etc/inetd.conf
# 4. Create config files from templates
# 5. Restart inetd service
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS_DIR="${SCRIPT_DIR}"
SERVICES_FILE="/etc/services"
INETD_CONF="/etc/inetd.conf"
BPQ_TEMPLATE_DIR="/opt/emcomm-tools/conf/template.d/bbs"

# App definitions: name|port|description|script|requires_config|config_template
declare -A APPS
APPS=(
    ["wqf"]="63000|Weather Quebec Forecast|wqf.py|none|"
    ["qrz"]="63010|QRZ Callsign Lookup|qrz.py|config.py|config.py.example"
    ["hamqsl"]="63020|Solar Data (HamQSL)|hamqsl.py|none|"
    ["space"]="63030|Space Weather Report|space.py|none|"
    ["relay"]="63040|SMTP Relay Service|smtp.py|smtp_config.json|smtp_config.json.example"
    ["wiki"]="63050|Offline Wikipedia/ZIM|wiki.py|wiki_config.json|wiki_config.json.example"
    ["isde"]="63060|ISDE Canadian Callsign DB|isde.py|none|"
    ["claude"]="63070|Claude AI Gateway|claude_gateway.py|claude_config.json|claude_config.json.example"
    ["gemini"]="63080|Google Gemini AI|gemini_gateway.py|gemini_config.json|gemini_config.json.example"
    ["blog"]="63090|Blog over HF|blog-app/blog.py|blog-app/blog_config.json|blog-app/blog_config.json.example"
)

# Order for menu display
APP_ORDER=("wqf" "qrz" "hamqsl" "space" "relay" "wiki" "isde" "claude" "gemini" "blog")

# Logging function
log() {
    echo -e "${GREEN}[BBS-APPS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as root for system configuration
check_sudo() {
    if [[ $EUID -ne 0 ]]; then
        error "This script requires sudo privileges to modify /etc/services and /etc/inetd.conf"
        error "Please run: sudo ./install.sh"
        exit 1
    fi
}

# Get the actual user who invoked sudo
get_real_user() {
    if [[ -n "${SUDO_USER}" ]]; then
        echo "${SUDO_USER}"
    else
        whoami
    fi
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    local missing=()
    
    # Check for dialog
    if ! command -v dialog &> /dev/null; then
        missing+=("dialog")
    fi
    
    # Check for Python 3
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi
    
    # Check for pip
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null 2>&1; then
        missing+=("python3-pip")
    fi
    
    # Check for inetd
    if ! command -v inetd &> /dev/null && ! systemctl list-unit-files | grep -q inetutils-inetd; then
        missing+=("inetutils-inetd")
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        warn "Missing dependencies: ${missing[*]}"
        log "Installing missing dependencies..."
        apt-get update
        apt-get install -y "${missing[@]}"
    fi
    
    log "All dependencies satisfied."
}

# Install Python packages
install_python_deps() {
    log "Installing Python dependencies..."
    
    if [[ -f "${SCRIPT_DIR}/requirements.txt" ]]; then
        pip3 install --break-system-packages -r "${SCRIPT_DIR}/requirements.txt" 2>/dev/null || \
        pip3 install -r "${SCRIPT_DIR}/requirements.txt"
    else
        # Fallback: install known dependencies
        pip3 install --break-system-packages requests beautifulsoup4 lxml 2>/dev/null || \
        pip3 install requests beautifulsoup4 lxml
    fi
    
    log "Python dependencies installed."
}

# Show app selection menu
select_apps() {
    local menu_items=()
    local i=1
    
    for app in "${APP_ORDER[@]}"; do
        IFS='|' read -r port desc script config template <<< "${APPS[$app]}"
        menu_items+=("$app" "$desc (port $port)" "off")
    done
    
    # Show dialog checklist
    SELECTED_APPS=$(dialog --clear --backtitle "BBS Server Apps Installer" \
        --title "Select Apps to Install" \
        --checklist "Use SPACE to select, ENTER to confirm:\n\nNote: Some apps require API keys or additional configuration." \
        20 70 10 \
        "${menu_items[@]}" \
        3>&1 1>&2 2>&3)
    
    EXIT_STATUS=$?
    clear
    
    if [[ $EXIT_STATUS -ne 0 ]] || [[ -z "$SELECTED_APPS" ]]; then
        warn "No apps selected. Exiting."
        exit 0
    fi
    
    # Convert to array
    read -ra SELECTED_APPS_ARRAY <<< "$SELECTED_APPS"
    
    log "Selected apps: ${SELECTED_APPS_ARRAY[*]}"
}

# Configure a single app's config file
configure_app_config() {
    local app="$1"
    IFS='|' read -r port desc script config template <<< "${APPS[$app]}"
    
    if [[ "$config" == "none" ]]; then
        return 0
    fi
    
    local config_path="${APPS_DIR}/${config}"
    local template_path="${APPS_DIR}/${template}"
    
    # Check if config already exists
    if [[ -f "$config_path" ]]; then
        info "Config file already exists: $config"
        return 0
    fi
    
    # Check if template exists
    if [[ ! -f "$template_path" ]]; then
        warn "Template not found: $template"
        return 1
    fi
    
    log "Creating config file: $config"
    cp "$template_path" "$config_path"
    
    # Special handling for different config types
    case "$app" in
        "qrz")
            echo ""
            info "QRZ.com requires a subscription with XML access."
            read -p "Enter your QRZ username (or press Enter to skip): " qrz_user
            if [[ -n "$qrz_user" ]]; then
                read -sp "Enter your QRZ password: " qrz_pass
                echo ""
                sed -i "s/YOUR_QRZ_USERNAME/${qrz_user}/" "$config_path"
                sed -i "s/YOUR_QRZ_PASSWORD/${qrz_pass}/" "$config_path"
            fi
            ;;
        "claude")
            echo ""
            info "Claude AI requires an Anthropic API key."
            info "Get one at: https://console.anthropic.com/"
            read -sp "Enter your Anthropic API key (or press Enter to skip): " api_key
            echo ""
            if [[ -n "$api_key" ]]; then
                # Update JSON config
                local tmp_file=$(mktemp)
                python3 -c "
import json
with open('$config_path', 'r') as f:
    config = json.load(f)
config['default_api_key'] = '$api_key'
with open('$config_path', 'w') as f:
    json.dump(config, f, indent=4)
" 2>/dev/null || sed -i "s/Enter here your Claude API Key/${api_key}/" "$config_path"
            fi
            ;;
        "gemini")
            echo ""
            info "Google Gemini requires a Google AI API key."
            info "Get one at: https://aistudio.google.com/apikey"
            read -sp "Enter your Google AI API key (or press Enter to skip): " api_key
            echo ""
            if [[ -n "$api_key" ]]; then
                local tmp_file=$(mktemp)
                python3 -c "
import json
with open('$config_path', 'r') as f:
    config = json.load(f)
config['default_api_key'] = '$api_key'
with open('$config_path', 'w') as f:
    json.dump(config, f, indent=4)
" 2>/dev/null || sed -i "s/Enter here your Gemini API Key/${api_key}/" "$config_path"
            fi
            ;;
        "relay")
            echo ""
            info "SMTP Relay requires mail server configuration."
            read -p "Enter SMTP server (e.g., smtp.gmail.com): " smtp_server
            if [[ -n "$smtp_server" ]]; then
                read -p "Enter SMTP port (default 587): " smtp_port
                smtp_port=${smtp_port:-587}
                read -p "Enter your email address: " email_addr
                read -sp "Enter your email password/app-password: " email_pass
                echo ""
                python3 -c "
import json
with open('$config_path', 'r') as f:
    config = json.load(f)
config['smtp_server'] = '$smtp_server'
config['smtp_port'] = $smtp_port
config['email'] = '$email_addr'
config['password'] = '$email_pass'
with open('$config_path', 'w') as f:
    json.dump(config, f, indent=4)
" 2>/dev/null
            fi
            ;;
        "wiki")
            echo ""
            info "Wiki app requires ZIM files (offline Wikipedia)."
            info "Default location: ~/wikipedia/"
            info "You can download ZIM files from: https://download.kiwix.org/zim/"
            ;;
        "blog")
            echo ""
            info "Blog app requires PostgreSQL database."
            info "Run: python3 ${APPS_DIR}/blog-app/setup_blog.py"
            ;;
    esac
    
    # Fix ownership
    local real_user=$(get_real_user)
    chown "${real_user}:${real_user}" "$config_path" 2>/dev/null || true
}

# Add entry to /etc/services
add_service_entry() {
    local app="$1"
    IFS='|' read -r port desc script config template <<< "${APPS[$app]}"
    
    # Check if already exists
    if grep -q "^${app}[[:space:]]" "$SERVICES_FILE" 2>/dev/null; then
        info "Service entry already exists: $app"
        return 0
    fi
    
    log "Adding service entry: $app -> $port/tcp"
    
    # Add to services file
    echo -e "${app}\t\t${port}/tcp\t\t\t# ${desc}" >> "$SERVICES_FILE"
}

# Add entry to /etc/inetd.conf
add_inetd_entry() {
    local app="$1"
    local username="$2"
    
    IFS='|' read -r port desc script config template <<< "${APPS[$app]}"
    
    # Check if already exists
    if grep -q "^${app}[[:space:]]" "$INETD_CONF" 2>/dev/null; then
        info "inetd entry already exists: $app"
        return 0
    fi
    
    # Determine script path
    local script_path="${APPS_DIR}/${script}"
    
    log "Adding inetd entry: $app"
    
    # Add HAM-RADIO section header if not present
    if ! grep -q "#:HAM-RADIO:" "$INETD_CONF" 2>/dev/null; then
        echo "" >> "$INETD_CONF"
        echo "#:HAM-RADIO: amateur-radio BBS services" >> "$INETD_CONF"
        echo "" >> "$INETD_CONF"
    fi
    
    # Add entry
    echo "${app}	stream	tcp	nowait	${username}	${script_path}" >> "$INETD_CONF"
}

# Make scripts executable
make_scripts_executable() {
    log "Making scripts executable..."
    
    chmod +x "${APPS_DIR}"/*.py 2>/dev/null || true
    chmod +x "${APPS_DIR}"/blog-app/*.py 2>/dev/null || true
    chmod +x "${APPS_DIR}"/wiki/*.py 2>/dev/null || true
}

# Restart inetd service
restart_inetd() {
    log "Restarting inetd service..."
    
    if systemctl is-active --quiet inetutils-inetd; then
        systemctl restart inetutils-inetd
    elif systemctl is-active --quiet inetd; then
        systemctl restart inetd
    else
        warn "inetd service not found or not running"
        info "Try: sudo systemctl start inetutils-inetd"
        return 1
    fi
    
    log "inetd service restarted successfully."
}

# Generate BPQ template snippet
generate_bpq_snippet() {
    local apps=("$@")
    
    echo ""
    echo "=============================================="
    echo "BPQ Configuration Snippet"
    echo "=============================================="
    echo ""
    echo "Add these lines to your BPQ configuration file."
    echo "Template location: ${BPQ_TEMPLATE_DIR}/"
    echo ""
    echo "--- CTEXT Section (add these commands to your CTEXT) ---"
    echo ""
    
    for app in "${apps[@]}"; do
        # Remove quotes if present
        app=$(echo "$app" | tr -d '"')
        IFS='|' read -r port desc script config template <<< "${APPS[$app]}"
        local upper_app=$(echo "$app" | tr '[:lower:]' '[:upper:]')
        printf "%-8s %s\n" "${upper_app}" "${desc}"
    done
    
    echo ""
    echo "--- PORT Section (add CMDPORT line to your Telnet PORT) ---"
    echo ""
    echo -n "CMDPORT "
    local ports=()
    for app in "${apps[@]}"; do
        app=$(echo "$app" | tr -d '"')
        IFS='|' read -r port desc script config template <<< "${APPS[$app]}"
        ports+=("$port")
    done
    echo "${ports[*]}" | tr ' ' ' '
    
    echo ""
    echo "--- APPLICATION Section (add after your PORT definitions) ---"
    echo ""
    
    local app_num=3  # Start after BBS and CHAT typically
    for app in "${apps[@]}"; do
        app=$(echo "$app" | tr -d '"')
        IFS='|' read -r port desc script config template <<< "${APPS[$app]}"
        local upper_app=$(echo "$app" | tr '[:lower:]' '[:upper:]')
        local host_num=$((app_num - 3))
        echo "APPLICATION ${app_num},${upper_app},C 2 HOST ${host_num} NOCALL K S"
        ((app_num++))
    done
    
    echo ""
    echo "=============================================="
}

# Show completion summary
show_summary() {
    local apps=("$@")
    
    clear
    echo ""
    echo "=============================================="
    echo "  BBS Server Apps Installation Complete!"
    echo "=============================================="
    echo ""
    echo "Installed apps:"
    for app in "${apps[@]}"; do
        app=$(echo "$app" | tr -d '"')
        IFS='|' read -r port desc script config template <<< "${APPS[$app]}"
        echo "  ✓ ${app} (port ${port}) - ${desc}"
    done
    echo ""
    
    generate_bpq_snippet "${apps[@]}"
    
    echo ""
    echo "Next Steps:"
    echo "1. Edit your BPQ config file in: ${BPQ_TEMPLATE_DIR}/"
    echo "2. Add the CMDPORT and APPLICATION lines shown above"
    echo "3. Restart your BPQ node"
    echo ""
    echo "To test an app manually:"
    echo "  telnet localhost <port>"
    echo ""
    echo "Documentation: ${APPS_DIR}/README.md"
    echo ""
}

# Uninstall function
uninstall() {
    log "Uninstalling BBS Server Apps..."
    
    # Remove entries from inetd.conf
    for app in "${APP_ORDER[@]}"; do
        sed -i "/^${app}[[:space:]]/d" "$INETD_CONF" 2>/dev/null || true
    done
    
    # Remove entries from services
    for app in "${APP_ORDER[@]}"; do
        sed -i "/^${app}[[:space:]]/d" "$SERVICES_FILE" 2>/dev/null || true
    done
    
    # Restart inetd
    restart_inetd
    
    log "Entries removed from system configuration."
    log "App files remain in: ${APPS_DIR}"
    log "To completely remove, delete the apps directory."
}

# Main function
main() {
    echo ""
    echo "=============================================="
    echo "  BBS Server Apps Installer"
    echo "  https://github.com/emcomm-tools/bbs-server-apps"
    echo "=============================================="
    echo ""
    
    # Handle uninstall flag
    if [[ "$1" == "--uninstall" ]] || [[ "$1" == "-u" ]]; then
        check_sudo
        uninstall
        exit 0
    fi
    
    # Handle help flag
    if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
        echo "Usage: sudo ./install.sh [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  -h, --help      Show this help message"
        echo "  -u, --uninstall Remove app entries from system config"
        echo ""
        echo "This installer will:"
        echo "  1. Install Python dependencies"
        echo "  2. Let you select which apps to enable"
        echo "  3. Configure /etc/services and /etc/inetd.conf"
        echo "  4. Create config files from templates"
        echo "  5. Restart inetd service"
        echo ""
        exit 0
    fi
    
    check_sudo
    
    REAL_USER=$(get_real_user)
    log "Installing as user: ${REAL_USER}"
    
    check_dependencies
    install_python_deps
    
    select_apps
    
    make_scripts_executable
    
    # Process each selected app
    for app in "${SELECTED_APPS_ARRAY[@]}"; do
        # Remove quotes if present
        app=$(echo "$app" | tr -d '"')
        
        log "Configuring: $app"
        configure_app_config "$app"
        add_service_entry "$app"
        add_inetd_entry "$app" "$REAL_USER"
    done
    
    restart_inetd
    
    show_summary "${SELECTED_APPS_ARRAY[@]}"
}

main "$@"
