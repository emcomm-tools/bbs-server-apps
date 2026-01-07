#!/usr/bin/env python3
"""
Claude AI Gateway for LinBPQ BBS
Emergency Communications AI Assistant via Packet Radio

Three-tier API key system:
1. Default shared key (limited usage)
2. Registered users (callsign + verification)
3. Temporary personal key (session-based)

Author: VA2OPS & Claude
"""

import anthropic
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
from typing import Optional, Dict, List, Tuple
import textwrap

class ClaudeGateway:
    """Claude AI Gateway for amateur radio BBS"""
    
    def __init__(self, config_file="claude_config.json"):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.script_dir, config_file)
        self.users_db_path = os.path.join(self.script_dir, "claude_users.json")
        self.usage_log_path = os.path.join(self.script_dir, "claude_usage.json")
        
        self.config = self.load_config()
        self.users_db = self.load_users_db()
        self.usage_log = self.load_usage_log()
        
        # Current session state
        self.current_user = None
        self.current_api_key = None
        self.session_history = []
        self.temp_key_mode = False
        
        # RF optimization settings
        self.max_line_length = 79
        self.page_size = 20  # lines per page
        
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "default_api_key": "",
            "default_key_limits": {
                "queries_per_hour": 5,
                "queries_per_day": 20,
                "max_tokens_per_query": 1000
            },
            "registered_user_limits": {
                "queries_per_hour": 20,
                "queries_per_day": 100,
                "max_tokens_per_query": 2000
            },
            "temp_key_limits": {
                "queries_per_hour": 50,
                "queries_per_day": 200,
                "max_tokens_per_query": 4000
            },
            "model": "claude-sonnet-4-20250514",
            "system_prompt": "You are an AI assistant for amateur radio operators. Provide concise, accurate responses optimized for packet radio transmission (keep responses brief and clear). You help with technical questions, emergency communications, and general information. Always be helpful and accurate.",
            "enable_conversation_history": True,
            "max_history_turns": 5
        }
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            print(f"Config file not found: {self.config_path}")
            print("Creating default config...")
            self.save_config(default_config)
            return default_config
        except json.JSONDecodeError as e:
            print(f"Error reading config: {e}")
            return default_config
    
    def save_config(self, config: Dict):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"Config saved to: {self.config_path}")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def load_users_db(self) -> Dict:
        """Load registered users database"""
        try:
            with open(self.users_db_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print("Warning: Corrupted users database, creating new one")
            return {}
    
    def save_users_db(self):
        """Save users database"""
        try:
            with open(self.users_db_path, 'w') as f:
                json.dump(self.users_db, f, indent=4)
        except Exception as e:
            print(f"Error saving users database: {e}")
    
    def load_usage_log(self) -> Dict:
        """Load usage statistics"""
        try:
            with open(self.usage_log_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"sessions": []}
        except json.JSONDecodeError:
            return {"sessions": []}
    
    def save_usage_log(self):
        """Save usage statistics"""
        try:
            with open(self.usage_log_path, 'w') as f:
                json.dump(self.usage_log, f, indent=4)
        except Exception as e:
            print(f"Error saving usage log: {e}")
    
    def hash_password(self, password: str) -> str:
        """Simple password hashing"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, callsign: str, password: str, api_key: str = None) -> bool:
        """Register a new user with optional personal API key"""
        callsign = callsign.upper().strip()
        
        if callsign in self.users_db:
            print(f"Callsign {callsign} already registered")
            return False
        
        self.users_db[callsign] = {
            "password_hash": self.hash_password(password),
            "api_key": api_key,  # Optional personal key
            "registered_date": datetime.now().isoformat(),
            "total_queries": 0,
            "last_used": None
        }
        
        self.save_users_db()
        print(f"User {callsign} registered successfully")
        return True
    
    def authenticate_user(self, callsign: str, password: str) -> bool:
        """Authenticate a registered user"""
        callsign = callsign.upper().strip()
        
        if callsign not in self.users_db:
            return False
        
        password_hash = self.hash_password(password)
        return self.users_db[callsign]["password_hash"] == password_hash
    
    def check_rate_limit(self, user_type: str) -> Tuple[bool, str]:
        """Check if user has exceeded rate limits"""
        now = datetime.now()
        
        # Get appropriate limits
        if user_type == "default":
            limits = self.config["default_key_limits"]
        elif user_type == "registered":
            limits = self.config["registered_user_limits"]
        else:  # temp
            limits = self.config["temp_key_limits"]
        
        # Count queries in last hour and day
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        hour_count = 0
        day_count = 0
        
        for session in self.usage_log.get("sessions", []):
            if self.current_user and session.get("user") != self.current_user:
                continue
            
            timestamp = datetime.fromisoformat(session.get("timestamp", "2000-01-01"))
            
            if timestamp > hour_ago:
                hour_count += 1
            if timestamp > day_ago:
                day_count += 1
        
        # Check limits
        if hour_count >= limits["queries_per_hour"]:
            return False, f"Rate limit exceeded: {limits['queries_per_hour']} queries per hour"
        
        if day_count >= limits["queries_per_day"]:
            return False, f"Rate limit exceeded: {limits['queries_per_day']} queries per day"
        
        return True, f"OK - {hour_count}/{limits['queries_per_hour']} this hour, {day_count}/{limits['queries_per_day']} today"
    
    def log_query(self, query: str, response: str, tokens_used: int):
        """Log a query for usage tracking"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": self.current_user or "anonymous",
            "user_type": "temp" if self.temp_key_mode else ("registered" if self.current_user else "default"),
            "query_preview": query[:100],
            "tokens_used": tokens_used,
            "response_length": len(response)
        }
        
        self.usage_log["sessions"].append(log_entry)
        
        # Update user stats if registered
        if self.current_user and self.current_user in self.users_db:
            self.users_db[self.current_user]["total_queries"] += 1
            self.users_db[self.current_user]["last_used"] = datetime.now().isoformat()
            self.save_users_db()
        
        self.save_usage_log()
    
    def format_for_rf(self, text: str) -> List[str]:
        """Format text for RF transmission with line wrapping"""
        lines = []
        
        # Split by existing newlines first
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                lines.append("")
                continue
            
            # Wrap long lines
            wrapped = textwrap.fill(
                paragraph,
                width=self.max_line_length,
                break_long_words=False,
                break_on_hyphens=False
            )
            lines.extend(wrapped.split('\n'))
        
        return lines
    
    def query_claude(self, user_message: str, use_history: bool = True) -> Tuple[str, int]:
        """Send query to Claude and get response"""
        
        # Determine which API key to use
        api_key = None
        user_type = "default"
        
        if self.temp_key_mode and self.current_api_key:
            api_key = self.current_api_key
            user_type = "temp"
        elif self.current_user and self.current_user in self.users_db:
            user_api_key = self.users_db[self.current_user].get("api_key")
            if user_api_key:
                api_key = user_api_key
                user_type = "registered"
            else:
                api_key = self.config["default_api_key"]
                user_type = "registered"  # Still gets registered user limits
        else:
            api_key = self.config["default_api_key"]
            user_type = "default"
        
        if not api_key:
            return "ERROR: No API key configured", 0
        
        # Check rate limits
        can_query, limit_msg = self.check_rate_limit(user_type)
        if not can_query:
            return f"ERROR: {limit_msg}", 0
        
        # Get max tokens for this user type
        if user_type == "default":
            max_tokens = self.config["default_key_limits"]["max_tokens_per_query"]
        elif user_type == "registered":
            max_tokens = self.config["registered_user_limits"]["max_tokens_per_query"]
        else:
            max_tokens = self.config["temp_key_limits"]["max_tokens_per_query"]
        
        try:
            client = anthropic.Anthropic(api_key=api_key)
            
            # Build messages list
            messages = []
            
            # Add conversation history if enabled
            if use_history and self.config["enable_conversation_history"]:
                max_history = self.config["max_history_turns"]
                history_to_use = self.session_history[-max_history:] if len(self.session_history) > max_history else self.session_history
                messages.extend(history_to_use)
            
            # Add current message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Call Claude API
            response = client.messages.create(
                model=self.config["model"],
                max_tokens=max_tokens,
                system=self.config["system_prompt"],
                messages=messages
            )
            
            # Extract response text
            response_text = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            # Update conversation history
            if self.config["enable_conversation_history"]:
                self.session_history.append({
                    "role": "user",
                    "content": user_message
                })
                self.session_history.append({
                    "role": "assistant",
                    "content": response_text
                })
            
            # Log the query
            self.log_query(user_message, response_text, tokens_used)
            
            return response_text, tokens_used
            
        except anthropic.APIError as e:
            return f"API Error: {str(e)}", 0
        except Exception as e:
            return f"Error: {str(e)}", 0
    
    def show_status(self):
        """Show current gateway status"""
        print("\n" + "=" * 60)
        print("CLAUDE AI GATEWAY STATUS")
        print("=" * 60)
        
        # User status
        if self.temp_key_mode:
            print(f"Mode: Temporary API Key")
            print(f"User: {self.current_user or 'Anonymous'}")
        elif self.current_user:
            print(f"Mode: Registered User")
            print(f"User: {self.current_user}")
            user_data = self.users_db.get(self.current_user, {})
            print(f"Total queries: {user_data.get('total_queries', 0)}")
            print(f"Has personal key: {'Yes' if user_data.get('api_key') else 'No'}")
        else:
            print(f"Mode: Default Shared Key")
            print(f"User: Anonymous")
        
        # Rate limit status
        user_type = "temp" if self.temp_key_mode else ("registered" if self.current_user else "default")
        can_query, limit_msg = self.check_rate_limit(user_type)
        print(f"\nRate limit: {limit_msg}")
        
        # Configuration
        print(f"\nModel: {self.config['model']}")
        print(f"Conversation history: {'Enabled' if self.config['enable_conversation_history'] else 'Disabled'}")
        print(f"History turns: {len(self.session_history) // 2}")
        
        print("=" * 60)
    
    def clear_history(self):
        """Clear conversation history"""
        self.session_history = []
        print("Conversation history cleared")
    
    def show_help(self):
        """Show help information"""
        print("\n" + "=" * 60)
        print("CLAUDE AI GATEWAY - HELP")
        print("=" * 60)
        print("""
COMMANDS:
  ASK <question>     Ask Claude a question
  HISTORY            Show conversation history
  CLEAR              Clear conversation history
  STATUS             Show gateway status and limits
  
  LOGIN <call> <pw>  Login as registered user
  LOGOUT             Logout current user
  REGISTER           Register new user (interactive)
  
  TEMPKEY <key>      Use temporary API key (this session only)
  CLEARKEY           Clear temporary key
  
  HELP               Show this help
  QUIT               Exit gateway

USAGE TIERS:
1. Default (Anonymous):
   - Shared API key
   - Limited: 5 queries/hour, 20/day
   - Max 1000 tokens per query

2. Registered User:
   - Login with callsign + password
   - Higher limits: 20 queries/hour, 100/day
   - Max 2000 tokens per query
   - Optional: Use your own API key

3. Temporary Key:
   - Provide your own API key
   - Highest limits: 50 queries/hour, 200/day
   - Max 4000 tokens per query
   - Key deleted when you logout

EXAMPLES:
  ASK What is the formula for calculating antenna length?
  ASK Translate to French: The weather is good
  LOGIN VA2OPS mypassword123
  TEMPKEY sk-ant-api03-abc123...

NOTES:
- Responses optimized for packet radio (79 char lines)
- Conversation history maintained within session
- All queries logged for usage tracking
- Be concise - you're charged per token!

For emergency communications use only.
        """)
        print("=" * 60)
    
    def run_interactive(self):
        """Main interactive console"""
        print("=" * 60)
        print("CLAUDE AI GATEWAY v1.0")
        print("Amateur Radio Emergency Communications AI Assistant")
        print("=" * 60)
        print("\nType HELP for commands, QUIT to exit")
        
        # Check if default API key is configured
        if not self.config.get("default_api_key"):
            print("\nWARNING: No default API key configured!")
            print("Please edit claude_config.json and add your API key")
            print("Get your key at: https://console.anthropic.com/")
        
        while True:
            try:
                # Build prompt
                prompt_user = self.current_user or "ANON"
                prompt = f"\nCLAUDE[{prompt_user}]> "
                
                command = input(prompt).strip()
                
                if not command:
                    continue
                
                cmd_upper = command.upper()
                
                # Parse command
                if cmd_upper in ['QUIT', 'EXIT', 'Q']:
                    print("73! Gateway closing...")
                    break
                
                elif cmd_upper == 'HELP':
                    self.show_help()
                
                elif cmd_upper == 'STATUS':
                    self.show_status()
                
                elif cmd_upper == 'HISTORY':
                    if not self.session_history:
                        print("No conversation history")
                    else:
                        print("\n--- Conversation History ---")
                        for i, msg in enumerate(self.session_history):
                            role = msg['role'].upper()
                            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                            print(f"{i+1}. {role}: {content}")
                
                elif cmd_upper == 'CLEAR':
                    self.clear_history()
                
                elif cmd_upper.startswith('LOGIN '):
                    parts = command[6:].strip().split(None, 1)
                    if len(parts) != 2:
                        print("Usage: LOGIN <callsign> <password>")
                    else:
                        callsign, password = parts
                        if self.authenticate_user(callsign, password):
                            self.current_user = callsign.upper()
                            self.temp_key_mode = False
                            print(f"Logged in as {self.current_user}")
                        else:
                            print("Authentication failed")
                
                elif cmd_upper == 'LOGOUT':
                    if self.temp_key_mode:
                        self.current_api_key = None
                        self.temp_key_mode = False
                        print("Temporary key cleared")
                    self.current_user = None
                    self.clear_history()
                    print("Logged out")
                
                elif cmd_upper == 'REGISTER':
                    print("\n--- User Registration ---")
                    callsign = input("Callsign: ").strip().upper()
                    password = input("Password: ").strip()
                    
                    has_key = input("Do you have your own Claude API key? (y/n): ").strip().lower()
                    api_key = None
                    if has_key == 'y':
                        api_key = input("Enter your API key: ").strip()
                    
                    self.register_user(callsign, password, api_key)
                
                elif cmd_upper.startswith('TEMPKEY '):
                    api_key = command[8:].strip()
                    if len(api_key) < 20:
                        print("Invalid API key format")
                    else:
                        self.current_api_key = api_key
                        self.temp_key_mode = True
                        print("Temporary API key set for this session")
                        print("Key will be cleared when you logout")
                
                elif cmd_upper == 'CLEARKEY':
                    self.current_api_key = None
                    self.temp_key_mode = False
                    print("Temporary key cleared")
                
                elif cmd_upper.startswith('ASK '):
                    question = command[4:].strip()
                    if not question:
                        print("Usage: ASK <your question>")
                        continue
                    
                    print("\nQuerying Claude AI...")
                    print("-" * 60)
                    
                    response, tokens = self.query_claude(question)
                    
                    # Format and display response
                    lines = self.format_for_rf(response)
                    
                    line_count = 0
                    for line in lines:
                        print(line)
                        line_count += 1
                        
                        # Pagination for long responses
                        if line_count >= self.page_size and line_count < len(lines) - 1:
                            input("\n[Press ENTER to continue...]")
                            line_count = 0
                    
                    print("-" * 60)
                    print(f"Tokens used: {tokens}")
                
                else:
                    print(f"Unknown command: {command}")
                    print("Type HELP for available commands")
            
            except KeyboardInterrupt:
                print("\n\n73! Gateway closing...")
                break
            except Exception as e:
                print(f"Error: {e}")

def create_example_config():
    """Create example configuration file"""
    config = {
        "default_api_key": "YOUR_CLAUDE_API_KEY_HERE",
        "default_key_limits": {
            "queries_per_hour": 5,
            "queries_per_day": 20,
            "max_tokens_per_query": 1000
        },
        "registered_user_limits": {
            "queries_per_hour": 20,
            "queries_per_day": 100,
            "max_tokens_per_query": 2000
        },
        "temp_key_limits": {
            "queries_per_hour": 50,
            "queries_per_day": 200,
            "max_tokens_per_query": 4000
        },
        "model": "claude-sonnet-4-20250514",
        "system_prompt": "You are an AI assistant for amateur radio operators. Provide concise, accurate responses optimized for packet radio transmission (keep responses brief and clear). You help with technical questions, emergency communications, and general information. Always be helpful and accurate.",
        "enable_conversation_history": True,
        "max_history_turns": 5
    }
    
    with open('claude_config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    print("Example config created: claude_config.json")
    print("\nIMPORTANT: Edit the file and add your Claude API key!")
    print("Get your API key at: https://console.anthropic.com/")

def main():
    """Main entry point"""
    
    if len(sys.argv) > 1 and sys.argv[1] == '--create-config':
        create_example_config()
        return
    
    # Run the gateway
    gateway = ClaudeGateway()
    gateway.run_interactive()

if __name__ == "__main__":
    main()
