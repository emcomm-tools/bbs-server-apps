#!/usr/bin/env python3
"""
Canadian Amateur Radio Callsign Lookup Console Application
For linbpq BBS integration - searches ISED amateur radio database
"""

import os
import json
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

class CallsignLookup:
    """Console application for searching Canadian amateur radio callsigns"""
    
    def __init__(self):
        # Path to JSON files created by callsign_processor.py
        self.json_path = '/home/va2ops/.local/share/emcomm-tools/bbs-server/apps/isde/'
        
        # Province mappings
        self.provinces = {
            '1': {'code': 'qc', 'name': 'Quebec (VA2/VE2)'},
            '2': {'code': 'ont', 'name': 'Ontario (VA3/VE3)'},
            '3': {'code': 'nfl', 'name': 'Newfoundland and Labrador (VO1/VO2)'},
            '4': {'code': 'ns', 'name': 'Nova Scotia (VA1/VE1)'},
            '5': {'code': 'pei', 'name': 'Prince Edward Island (VY2)'},
            '6': {'code': 'nb', 'name': 'New Brunswick (VE9)'},
            '7': {'code': 'mb', 'name': 'Manitoba (VA4/VE4)'},
            '8': {'code': 'sk', 'name': 'Saskatchewan (VA5/VE5)'},
            '9': {'code': 'al', 'name': 'Alberta (VA6/VE6)'},
            '10': {'code': 'bc', 'name': 'British Columbia (VA7/VE7)'},
            '11': {'code': 'yk', 'name': 'Yukon (VY1)'},
            '12': {'code': 'tno', 'name': 'Northwest Territories (VE8)'},
            '13': {'code': 'nv', 'name': 'Nunavut (VY0)'},
            '14': {'code': 'others', 'name': 'Others/Unclassified'}
        }
        
        self.current_data = []
        self.current_province = ""
        self.last_search_results = []
    
    def show_banner(self):
        """Display application banner"""
        print("=" * 60)
        print("     Canadian Amateur Radio Callsign Lookup")
        print("         ISED Database Search Console")
        print("=" * 60)
        print()
    
    def show_province_menu(self) -> str:
        """Display province selection menu and get user choice"""
        print("Select Province/Territory to search:")
        print("-" * 40)
        
        for key, province in self.provinces.items():
            # Check if JSON file exists
            json_file = os.path.join(self.json_path, f"{province['code']}.json")
            status = "✓" if os.path.exists(json_file) else "✗"
            print(f"{key:2}. {status} {province['name']}")
        
        print()
        print("0. Exit")
        print()
        
        while True:
            choice = input("Enter your choice (0-14): ").strip()
            
            if choice == '0':
                return 'exit'
            
            if choice in self.provinces:
                return self.provinces[choice]['code']
            
            print("Invalid choice. Please enter a number between 0-14.")
    
    def load_province_data(self, province_code: str) -> bool:
        """Load JSON data for selected province"""
        json_file = os.path.join(self.json_path, f"{province_code}.json")
        
        try:
            if not os.path.exists(json_file):
                print(f"Error: Data file not found for {province_code}")
                print(f"Expected: {json_file}")
                return False
            
            with open(json_file, 'r', encoding='utf-8') as f:
                self.current_data = json.load(f)
            
            province_name = next(p['name'] for p in self.provinces.values() if p['code'] == province_code)
            self.current_province = province_name
            
            print(f"Loaded {len(self.current_data)} records for {province_name}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON file format: {e}")
            return False
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def search_records(self, query: str) -> List[Dict[str, Any]]:
        """Search records by callsign or name (partial matches)"""
        if not query:
            return []
        
        query_lower = query.lower().strip()
        results = []
        
        for record in self.current_data:
            # Combine the 3 search fields as mentioned
            callsign = record.get('callsign', '').lower()
            first_name = record.get('first_name', '').lower()
            surname = record.get('surname', '').lower()
            
            # Search in any of the three fields (partial match)
            if (query_lower in callsign or 
                query_lower in first_name or 
                query_lower in surname):
                results.append(record)
        
        return results
    
    def display_search_results(self, results: List[Dict[str, Any]]):
        """Display search results with numbers"""
        if not results:
            print("No records found.")
            return
        
        print(f"\nFound {len(results)} result(s):")
        print("-" * 60)
        
        for i, record in enumerate(results, 1):
            callsign = record.get('callsign', 'N/A')
            first_name = record.get('first_name', '')
            surname = record.get('surname', '')
            
            # Format name display
            name_parts = [first_name, surname]
            full_name = ' '.join(part for part in name_parts if part.strip())
            
            if full_name:
                display_line = f"{callsign} - {full_name}"
            else:
                display_line = callsign
            
            print(f"{i:3}. {display_line}")
        
        print()
        self.last_search_results = results
    
    def display_record_details(self, record: Dict[str, Any]):
        """Display full record details (only fields with data)"""
        print("\n" + "=" * 50)
        print("RECORD DETAILS")
        print("=" * 50)
        
        # Define display order and field labels
        field_labels = {
            'callsign': 'Callsign',
            'first_name': 'First Name',
            'surname': 'Surname', 
            'address_line': 'Address',
            'city': 'City',
            'prov_cd': 'Province',
            'postal_code': 'Postal Code',
            'qual_a': 'Qualification A',
            'qual_b': 'Qualification B', 
            'qual_c': 'Qualification C',
            'qual_d': 'Qualification D',
            'qual_e': 'Qualification E',
            'club_name': 'Club Name',
            'club_name_2': 'Club Name 2',
            'club_address': 'Club Address',
            'club_city': 'Club City',
            'club_prov_cd': 'Club Province',
            'club_postal_code': 'Club Postal Code'
        }
        
        # Display only fields with data
        for field, label in field_labels.items():
            value = record.get(field, '').strip()
            if value:  # Only show fields that have data
                print(f"{label:20}: {value}")
        
        print("=" * 50)
    
    def search_interface(self):
        """Main search interface for current province"""
        print(f"\nSearching in: {self.current_province}")
        print("Commands:")
        print("  <search term>  - Search by callsign or name (partial matches allowed)")
        print("  <number>       - View details for result number")
        print("  back           - Return to province selection")
        print("  quit           - Exit application")
        print()
        
        while True:
            try:
                user_input = input(f"Search [{self.current_province}]> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'quit':
                    return 'quit'
                
                if user_input.lower() == 'back':
                    return 'back'
                
                # Check if input is a number (for viewing details)
                if user_input.isdigit():
                    result_num = int(user_input)
                    
                    if not self.last_search_results:
                        print("No search results available. Please search first.")
                        continue
                    
                    if 1 <= result_num <= len(self.last_search_results):
                        record = self.last_search_results[result_num - 1]
                        self.display_record_details(record)
                    else:
                        print(f"Invalid number. Please enter 1-{len(self.last_search_results)}")
                    continue
                
                # Perform search
                results = self.search_records(user_input)
                self.display_search_results(results)
                
                if results:
                    print("Enter a number to view details, or search again.")
                
            except KeyboardInterrupt:
                return 'quit'
            except Exception as e:
                print(f"Error: {e}")
    
    def run(self):
        """Main application loop"""
        self.show_banner()
        
        while True:
            try:
                # Province selection
                province_choice = self.show_province_menu()
                
                if province_choice == 'exit':
                    print("73! Goodbye!")
                    break
                
                # Load province data
                if not self.load_province_data(province_choice):
                    input("Press Enter to continue...")
                    continue
                
                # Search interface
                result = self.search_interface()
                
                if result == 'quit':
                    print("73! Goodbye!")
                    break
                
                # If result is 'back', continue to province selection
                
            except KeyboardInterrupt:
                print("\n73! Goodbye!")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                input("Press Enter to continue...")

def main():
    """Main entry point"""
    # Check if data directory exists
    json_path = '/home/va2ops/.local/share/emcomm-tools/bbs-server/apps/isde/'
    
    if not os.path.exists(json_path):
        print(f"Error: Data directory not found: {json_path}")
        print("Please run callsign_processor.py first to download the data.")
        return 1
    
    try:
        app = CallsignLookup()
        app.run()
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
