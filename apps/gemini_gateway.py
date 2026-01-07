#!/usr/bin/env python3
"""
Gemini AI Gateway for LinBPQ BBS
Emergency Communications AI Assistant via Packet Radio

Three-tier API key system:
1. Default shared key (limited usage)
2. Registered users (callsign + verification)
3. Temporary personal key (session-based)

Author: VA2OPS & Claude
Based on Claude Gateway architecture
"""

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core._python_version_support")

import google.generativeai as genai
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
from typing import Optional, Dict, List, Tuple
import textwrap

class GeminiGateway:
    """Gemini AI Gateway for amateur radio BBS"""
    
    def __init__(self, config_file="gemini_config.json"):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.script_dir, config_file)
        self.users_db_path = os.path.join(self.script_dir, "gemini_users.json")
        self.usage_log_path = os.path.join(self.script_dir, "gemini_usage.json")
        
        self.config = self.load_config()
        self.users_db = self.load_users_db()
        self.usage_log = self.load_usage_log()
        
        # Current session state
        self.current_user = None
        self.current_api_key = None
        self.session_history = []
        self.temp_key_mode = False
        self.chat_session = None
        
        # RF optimization settings
        self.max_line_length = 79
        self.page_size = 20
    
    def load_config(self):
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
            "model": "models/gemini-2.5-flash",
            "system_instruction": "You are an AI assistant for amateur radio operators. Provide concise, accurate responses optimized for packet radio transmission (keep responses brief and clear). You help with technical questions, emergency communications, and general information. Always be helpful and accurate.",
            "enable_conversation_history": True,
            "safety_settings": {
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
            }
        }
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
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
    
    def save_config(self, config):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"Config saved to: {self.config_path}")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def load_users_db(self):
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
    
    def load_usage_log(self):
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
    
    def hash_password(self, password):
        """Simple password hashing"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, callsign, password, api_key=None):
        """Register a new user with optional personal API key"""
        callsign = callsign.upper().strip()
        
        if callsign in self.users_db:
            print(f"Callsign {callsign} already registered")
            return False
        
        self.users_db[callsign] = {
            "password_hash": self.hash_password(password),
            "api_key": api_key,
            "registered_date": datetime.now().isoformat(),
            "total_queries": 0,
            "last_used": None
        }
        
        self.save_users_db()
        print(f"User {callsign} registered successfully")
        return True
    
    def authenticate_user(self, callsign, password):
        """Authenticate a registered user"""
        callsign = callsign.upper().strip()
        
        if callsign not in self.users_db:
            return False
        
        password_hash = self.hash_password(password)
        return self.users_db[callsign]["password_hash"] == password_hash
    
    def check_rate_limit(self, user_type):
        """Check if user has exceeded rate limits"""
        now = datetime.now()
        
        if user_type == "default":
            limits = self.config["default_key_limits"]
        elif user_type == "registered":
            limits = self.config["registered_user_limits"]
        else:
            limits = self.config["temp_key_limits"]
        
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
        
        if hour_count >= limits["queries_per_hour"]:
            return False, f"Rate limit exceeded: {limits['queries_per_hour']} queries per hour"
        
        if day_count >= limits["queries_per_day"]:
            return False, f"Rate limit exceeded: {limits['queries_per_day']} queries per day"
        
        return True, f"OK - {hour_count}/{limits['queries_per_hour']} this hour, {day_count}/{limits['queries_per_day']} today"
    
    def log_query(self, query, response, tokens_used):
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
        
        if self.current_user and self.current_user in self.users_db:
            self.users_db[self.current_user]["total_queries"] += 1
            self.users_db[self.current_user]["last_used"] = datetime.now().isoformat()
            self.save_users_db()
        
        self.save_usage_log()
    
    def format_for_rf(self, text):
        """Format text for RF transmission with line wrapping"""
        lines = []
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                lines.append("")
                continue
            
            wrapped = textwrap.fill(
                paragraph,
                width=self.max_line_length,
                break_long_words=False,
                break_on_hyphens=False
            )
            lines.extend(wrapped.split('\n'))
        
        return lines
    
    def configure_gemini(self, api_key):
        """Configure Gemini API with key"""
        genai.configure(api_key=api_key)
    
    def get_safety_settings(self):
        """Get safety settings from config"""
        safety_config = self.config.get("safety_settings", {})
        
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        safety_map = {
            "BLOCK_NONE": HarmBlockThreshold.BLOCK_NONE,
            "BLOCK_LOW_AND_ABOVE": HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            "BLOCK_MEDIUM_AND_ABOVE": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            "BLOCK_ONLY_HIGH": HarmBlockThreshold.BLOCK_ONLY_HIGH
        }
        
        category_map = {
            "HARM_CATEGORY_HARASSMENT": HarmCategory.HARM_CATEGORY_HARASSMENT,
            "HARM_CATEGORY_HATE_SPEECH": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            "HARM_CATEGORY_DANGEROUS_CONTENT": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT
        }
        
        safety_settings = []
        for cat_name, threshold_name in safety_config.items():
            if cat_name in category_map and threshold_name in safety_map:
                safety_settings.append({
                    "category": category_map[cat_name],
                    "threshold": safety_map[threshold_name]
                })
        
        return safety_settings if safety_settings else None
    
    def query_gemini(self, user_message, use_history=True):
        """Send query to Gemini and get response"""
        
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
                user_type = "registered"
        else:
            api_key = self.config["default_api_key"]
            user_type = "default"
        
        if not api_key:
            return "ERROR: No API key configured", 0
        
        can_query, limit_msg = self.check_rate_limit(user_type)
        if not can_query:
            return f"ERROR: {limit_msg}", 0
        
        if user_type == "default":
            max_tokens = self.config["default_key_limits"]["max_tokens_per_query"]
        elif user_type == "registered":
            max_tokens = self.config["registered_user_limits"]["max_tokens_per_query"]
        else:
            max_tokens = self.config["temp_key_limits"]["max_tokens_per_query"]
        
        try:
            self.configure_gemini(api_key)
            
            model_name = self.config["model"]
            system_instruction = self.config.get("system_instruction", "")
            
            generation_config = {
                "max_output_tokens": max_tokens,
                "temperature": 0.7,
            }
            
            safety_settings = self.get_safety_settings()
            
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings,
                system_instruction=system_instruction
            )
            
            if use_history and self.config["enable_conversation_history"]:
                if not self.chat_session:
                    self.chat_session = model.start_chat(history=[])
                response = self.chat_session.send_message(user_message)
            else:
                response = model.generate_content(user_message)
            
            response_text = response.text
            tokens_used = (len(user_message) + len(response_text)) // 4
            
            self.log_query(user_message, response_text, tokens_used)
            
            return response_text, tokens_used
            
        except Exception as e:
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg:
                return "ERROR: Invalid API key", 0
            elif "QUOTA_EXCEEDED" in error_msg:
                return "ERROR: API quota exceeded", 0
            elif "blocked" in error_msg.lower():
                return "ERROR: Response blocked by safety filters. Try rephrasing your question.", 0
            else:
                return f"ERROR: {error_msg}", 0
    
    def show_status(self):
        """Show current gateway status"""
        print("\n" + "=" * 60)
        print("GEMINI AI GATEWAY STATUS")
        print("=" * 60)
        
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
        
        user_type = "temp" if self.temp_key_mode else ("registered" if self.current_user else "default")
        can_query, limit_msg = self.check_rate_limit(user_type)
        print(f"\nRate limit: {limit_msg}")
        
        print(f"\nModel: {self.config['model']}")
        print(f"Conversation history: {'Enabled' if self.config['enable_conversation_history'] else 'Disabled'}")
        print(f"Active chat session: {'Yes' if self.chat_session else 'No'}")
        
        print("=" * 60)
    
    def clear_history(self):
        """Clear conversation history"""
        self.chat_session = None
        print("Conversation history cleared")
    
    def show_help(self):
        """Show help information"""
        print("\n" + "=" * 60)
        print("GEMINI AI GATEWAY - HELP")
        print("=" * 60)
        print("""
COMMANDS:
  ASK <question>     Ask Gemini a question
  HISTORY            Show conversation status
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
  TEMPKEY AIzaSyAbc123...

Get your free API key at: https://aistudio.google.com/apikey

For emergency communications use only.
        """)
        print("=" * 60)
    
    def run_interactive(self):
        """Main interactive console"""
        print("=" * 60)
        print("GEMINI AI GATEWAY v1.0")
        print("Amateur Radio Emergency Communications AI Assistant")
        print("=" * 60)
        print("\nType HELP for commands, QUIT to exit")
        
        if not self.config.get("default_api_key"):
            print("\nWARNING: No default API key configured!")
            print("Please edit gemini_config.json and add your API key")
            print("Get your key at: https://aistudio.google.com/apikey")
        
        while True:
            try:
                prompt_user = self.current_user or "ANON"
                prompt = f"\nGEMINI[{prompt_user}]> "
                
                command = input(prompt).strip()
                
                if not command:
                    continue
                
                cmd_upper = command.upper()
                
                if cmd_upper in ['QUIT', 'EXIT', 'Q']:
                    print("73! Gateway closing...")
                    break
                
                elif cmd_upper == 'HELP':
                    self.show_help()
                
                elif cmd_upper == 'STATUS':
                    self.show_status()
                
                elif cmd_upper == 'HISTORY':
                    if self.chat_session:
                        print("Active chat session with conversation history")
                        print("Use CLEAR to start fresh conversation")
                    else:
                        print("No active chat session")
                
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
                    
                    has_key = input("Do you have your own Gemini API key? (y/n): ").strip().lower()
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
                    
                    print("\nQuerying Gemini AI...")
                    print("-" * 60)
                    
                    response, tokens = self.query_gemini(question)
                    
                    lines = self.format_for_rf(response)
                    
                    line_count = 0
                    for line in lines:
                        print(line)
                        line_count += 1
                        
                        if line_count >= self.page_size and line_count < len(lines) - 1:
                            input("\n[Press ENTER to continue...]")
                            line_count = 0
                    
                    print("-" * 60)
                    print(f"Estimated tokens: {tokens}")
                
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
        "default_api_key": "YOUR_GEMINI_API_KEY_HERE",
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
        "model": "models/gemini-2.5-flash",
        "system_instruction": "You are an AI assistant for amateur radio operators. Provide concise, accurate responses optimized for packet radio transmission (keep responses brief and clear). You help with technical questions, emergency communications, and general information. Always be helpful and accurate.",
        "enable_conversation_history": True,
        "safety_settings": {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
        }
    }
    
    with open('gemini_config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    print("Example config created: gemini_config.json")
    print("\nIMPORTANT: Edit the file and add your Gemini API key!")
    print("Get your API key at: https://aistudio.google.com/apikey")

def main():
    """Main entry point"""
    
    if len(sys.argv) > 1 and sys.argv[1] == '--create-config':
        create_example_config()
        return
    
    gateway = GeminiGateway()
    gateway.run_interactive()

if __name__ == "__main__":
    main()
