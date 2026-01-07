#!/usr/bin/env python3
"""
Fixed Kiwix ZIM File Interface - Main Entry Point
Designed for console, telnet, and RF/linbpq integration
"""

import sys
import os

# Add the current directory to Python path to find our wiki module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wiki.config import load_config, validate_zim_files, display_zim_menu, create_example_config
from wiki.zim_reader import WikiZimReader
from wiki.console_interface import WikiConsoleInterface

def main():
    """Main entry point"""
    print("Starting Multi-ZIM Wikipedia Reader...")
    print("=" * 50)
    
    # Try to load configuration
    config = load_config()
    
    if not config:
        print("No configuration file found!")
        print("Creating example configuration...")
        config = create_example_config()
        print("\nPlease edit wiki_config.json and restart the program.")
        return
    
    # Handle legacy single-file config format
    if 'zim_file_path' in config:
        print("Found legacy single-file configuration.")
        print("Converting to new multi-file format...")
        
        # Convert old format to new format
        legacy_path = config['zim_file_path']
        config['zim_files'] = [{
            'name': 'Default ZIM File',
            'description': f'Legacy ZIM file: {os.path.basename(legacy_path)}',
            'path': legacy_path
        }]
        
        # Save updated config
        try:
            import json
            config_path = os.path.join(os.path.dirname(__file__), 'wiki_config.json')
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"Updated configuration saved to: {config_path}")
        except Exception as e:
            print(f"Warning: Could not save updated config: {e}")
    
    # Check for ZIM files configuration
    if 'zim_files' not in config:
        print("Error: No 'zim_files' section found in configuration!")
        print("Please check your wiki_config.json file.")
        return
    
    # Validate ZIM files
    zim_files = validate_zim_files(config['zim_files'])
    
    if not zim_files:
        print("Error: No valid ZIM files found!")
        print("Please check your file paths in wiki_config.json")
        return
    
    # Handle command line argument for direct file selection
    selected_index = None
    if len(sys.argv) == 2:
        try:
            # Try as index first
            selected_index = int(sys.argv[1]) - 1
            if selected_index < 0 or selected_index >= len(zim_files):
                raise ValueError("Index out of range")
        except ValueError:
            # Try as file path
            arg_path = sys.argv[1]
            for i, zim_config in enumerate(zim_files):
                if zim_config['path'] == arg_path:
                    selected_index = i
                    break
            else:
                print(f"Error: ZIM file not found in config: {arg_path}")
                return
    
    # Display menu and get selection if not provided via command line
    if selected_index is None:
        selected_index = display_zim_menu(zim_files)
        
    if selected_index is None:
        print("No ZIM file selected. Exiting.")
        return
    
    # Get selected ZIM file configuration
    selected_zim = zim_files[selected_index]
    zim_file_path = selected_zim['path']
    
    print(f"\nSelected: {selected_zim['name']}")
    print(f"Description: {selected_zim['description']}")
    print(f"Loading ZIM file: {zim_file_path}")
    print("=" * 50)
    
    try:
        # Initialize ZIM reader
        zim_reader = WikiZimReader(zim_file_path)
        
        # Get configuration settings
        default_max_chars = config.get('default_max_chars', 2000)
        rf_callsign = config.get('rf_callsign', 'VA2OPS')
        
        # Start console interface with configuration
        console = WikiConsoleInterface(zim_reader, default_max_chars, rf_callsign, selected_zim)
        console.start_interactive_session()
        
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        sys.exit(1)
    except ImportError as e:
        print(f"Import error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
