#!/usr/bin/env python3
"""
RF SMTP Gateway - Emergency email relay system
Designed to work with telnet console and later integrate with VARA/LinBPQ
Similar to Winlink functionality for packet radio
"""

import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
import sys
import os
from datetime import datetime
import json

class RFSMTPGateway:
    def __init__(self, config_file="smtp_config.json"):
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(script_dir, config_file)
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from JSON file"""
        default_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "gateway_email": "",
            "gateway_password": "",
            "gateway_name": "RF Gateway"
        }
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                print(f"Config loaded from: {self.config_path}")
                return config
        except FileNotFoundError:
            print(f"Config file not found: {self.config_path}")
            print("Please create smtp_config.json in the same directory as the script")
            return default_config
        except json.JSONDecodeError as e:
            print(f"Error reading config file: {e}")
            return default_config
    
    def test_connection(self):
        """Test SMTP gateway connection"""
        if not self.config['gateway_email'] or not self.config['gateway_password']:
            print("ERROR: Gateway email and password must be configured")
            return False
            
        try:
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            if self.config['use_tls']:
                server.starttls()
            server.login(self.config['gateway_email'], self.config['gateway_password'])
            server.quit()
            print("SMTP Gateway connection test: SUCCESS")
            return True
            
        except Exception as e:
            print(f"SMTP Gateway connection test: FAILED - {str(e)}")
            return False
    
    def send_message(self):
        """Send email via SMTP gateway"""
        print("\n=== RF SMTP Gateway - Compose Message ===")
        
        # Get sender information
        sender_name = input("Your name: ").strip()
        reply_to_email = input("Your email (for replies): ").strip()
        
        # Get recipient and message details
        to_email = input("To (email address): ").strip()
        subject = input("Subject: ").strip()
        
        print("\nMessage body (type 'END' on a new line to finish):")
        body_lines = []
        while True:
            line = input()
            if line.strip().upper() == 'END':
                break
            body_lines.append(line)
        
        message_body = '\n'.join(body_lines)
        
        # Confirm before sending
        print("\n=== Message Summary ===")
        print(f"From: {sender_name} <{reply_to_email}>")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Body: {len(message_body)} characters")
        
        confirm = input("\nSend message? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Message cancelled")
            return False
        
        try:
            # Create message with strict RFC compliance
            msg = MIMEText(message_body, 'plain')
            
            # Set required headers (only once each per RFC 5322)
            msg['From'] = f"{self.config['gateway_name']} <{self.config['gateway_email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # RFC 2822 compliant Date header
            from email.utils import formatdate
            msg['Date'] = formatdate(localtime=True)
            
            # Reply-To for responses
            msg['Reply-To'] = f"{sender_name} <{reply_to_email}>"
            
            # Optional custom headers (X- headers are safe)
            msg['X-RF-Gateway'] = 'LinBPQ-VARA'
            msg['X-Emergency-Origin'] = f"{sender_name} <{reply_to_email}>"
            
            # Create body with sender info
            full_body = f"Message sent via RF SMTP Gateway\n"
            full_body += f"From: {sender_name} <{reply_to_email}>\n"
            full_body += f"Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            full_body += f"{'-' * 50}\n\n"
            full_body += message_body
            full_body += f"\n\n{'-' * 50}\n"
            full_body += f"This message was relayed via RF SMTP Gateway\n"
            full_body += f"Reply to: {reply_to_email}"
            
            # Update the message body
            msg.set_payload(full_body)
            
            # Send via SMTP
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            if self.config['use_tls']:
                server.starttls()
            server.login(self.config['gateway_email'], self.config['gateway_password'])
            
            text = msg.as_string()
            server.sendmail(self.config['gateway_email'], to_email, text)
            server.quit()
            
            print(f"\nSUCCESS: Message sent to {to_email}")
            print(f"Replies will go to: {reply_to_email}")
            return True
            
        except Exception as e:
            print(f"FAILED to send message: {str(e)}")
            return False
    
    def show_status(self):
        """Show gateway status"""
        print("\n=== RF SMTP Gateway Status ===")
        print(f"SMTP Server: {self.config['smtp_server']}:{self.config['smtp_port']}")
        print(f"TLS Enabled: {self.config['use_tls']}")
        print(f"Gateway Email: {self.config['gateway_email']}")
        print(f"Gateway Name: {self.config['gateway_name']}")
        
        # Test connection
        self.test_connection()
    
    def list_commands(self):
        """Display available commands"""
        commands = {
            'SEND': 'Send a message via SMTP gateway',
            'STATUS': 'Show gateway status and test connection',
            'HELP': 'Show this help',
            'QUIT': 'Exit the program'
        }
        
        print("\n=== Available Commands ===")
        for cmd, desc in commands.items():
            print(f"{cmd:<8} - {desc}")
    
    def run_console(self):
        """Main console interface"""
        print("RF SMTP Gateway v1.0")
        print("Emergency email relay system for LinBPQ/VARA")
        print("Type HELP for commands")
        
        # Check configuration
        if not self.config['gateway_email'] or not self.config['gateway_password']:
            print("\nWARNING: Gateway not configured!")
            print("Please edit smtp_config.json with your gateway credentials")
            print("Use --config to create a sample configuration file")
        
        # Main command loop
        while True:
            try:
                command = input(f"\nRF-SMTP> ").strip().upper()
                
                if command == 'SEND':
                    self.send_message()
                elif command == 'STATUS':
                    self.show_status()
                elif command == 'HELP':
                    self.list_commands()
                elif command == 'QUIT' or command == 'EXIT':
                    print("73! Gateway shutting down...")
                    break
                else:
                    print(f"Unknown command: {command}")
                    print("Type HELP for available commands")
                    
            except KeyboardInterrupt:
                print("\nExiting... 73!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == '--config':
        # Create sample config file
        sample_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "gateway_email": "your-gateway@gmail.com",
            "gateway_password": "your-app-password",
            "gateway_name": "RF Emergency Gateway"
        }
        
        with open('smtp_config.json', 'w') as f:
            json.dump(sample_config, f, indent=4)
        print("Sample config file created: smtp_config.json")
        print("Please edit smtp_config.json with your SMTP gateway credentials")
        return
    
    # Run the SMTP gateway
    gateway = RFSMTPGateway()
    gateway.run_console()

if __name__ == "__main__":
    main()
