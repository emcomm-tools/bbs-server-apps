#!/usr/bin/env python3

import urllib.request
import xml.etree.ElementTree as ET
import re
import sys
import unicodedata

ALERT = False

LANG = "e"

CITIES = {
    "Montréal": "45.529_-73.562_",
    "Québec": "46.811_-71.225_",
    "Trois-Rivières":"46.346_-72.561_",
    "Sherbrooke":"45.403_-71.901_",
    "LaTuque":"47.436_-72.779_",
    "Rivière-du-loup":"47.827_-69.533_",
    "Saguenay":"48.417_-71.067_",
    "Baie Comeau":"49.209_-68.175_",
    "Cap-Chat":"49.089_-66.685_",
    "Sept-Ile":"50.218_-66.373_",
    "Blanc Sablon":"51.427_-57.132_",
    "Maniwaki":"46.373_-75.977_",
    "Val-d'Or":"48.105_-77.796_",
    "Chibougamau":"49.915_-74.373_"
}

def display_menu():
    """Display the city selection menu"""
    print("\n=== Weather Quebec Forecast Menu ===")
    print("Select a city to view the alert and weather forecast:")
    
    # Display numbered options
    for i, city in enumerate(CITIES.keys(), 1):
        print(f"{i}. {city}")
    
    print("0. Exit")
    print("===========================")

def get_menu_choice():
    """Get user choice from the menu"""
    while True:
        try:
            choice = input("Enter your choice (0-{}): ".format(len(CITIES)))
            choice = int(choice)
            
            if 0 <= choice <= len(CITIES):
                return choice
            else:
                print(f"Please enter a number between 0 and {len(CITIES)}.")
        except ValueError:
            print("Please enter a valid number.")

def convert_to_ascii(text):
    """Convert Unicode text with accents to ASCII equivalent"""
    if text is None:
        return ""
        
    # Normalize to decomposed form (separate base characters from accents)
    normalized = unicodedata.normalize('NFKD', text)
    
    # Remove the non-ASCII characters (the accent marks)
    ascii_text = normalized.encode('ASCII', 'ignore').decode('ASCII')
    return ascii_text

def parse_weather_rss(info, lang, url, city_name):
    """
    Fetches weather data from the provided RSS URL and returns it as plain text.
    Converts all text to ASCII for compatibility with limited terminals.
    """
    try:
        print(f"\nFetching {info} forecast for {city_name}...")
        
        # Fetch the RSS contentprint(f"The lang selected is : {LANG}")
        fullurl = f"https://meteo.gc.ca/rss/{info}/{url}{lang}.xml";
        
        with urllib.request.urlopen(fullurl) as response:
            rss_content = response.read()
        
        # Parse the XML
        root = ET.fromstring(rss_content)
        
        # Find items regardless of structure
        items = []
        
        # Try to find channel first (standard RSS)
        channel = root.find('.//channel')
        
        if channel is not None:
            title_elem = channel.find('title')
            desc_elem = channel.find('description')
            
            if title_elem is not None:
                print(f"\n{title_elem.text}\n")
            
            if desc_elem is not None:
                print(f"{desc_elem.text}\n")
            
            print("-" * 60)
            
            # Get items from channel
            items = channel.findall('item')
        else:
            # If no channel, try to find items directly
            # Try with namespace
            items = root.findall('.//{*}item')
            if not items:
                # Try without namespace
                items = root.findall('.//item')
            
            # If still no items, try entries (for Atom feeds)
            if not items:
                items = root.findall('.//{*}entry')
                if not items:
                    items = root.findall('.//entry')
        
        # Process each found item
        for item in items:
            # Try different possible tag names for title and description
            title = None
            for title_tag in ['title', '{*}title']:
                title_elem = item.find(title_tag)
                if title_elem is not None and title_elem.text:
                    title = title_elem.text
                    break
            
            description = None
            for desc_tag in ['description', 'summary', 'content', '{*}description', '{*}summary', '{*}content']:
                desc_elem = item.find(desc_tag)
                if desc_elem is not None and desc_elem.text:
                    description = desc_elem.text
                    break
            
            if title or description:
                if title:
                    print(f"\n{title}")
                
                if description:
                    # Clean HTML tags
                    clean_description = re.sub(r'<[^>]+>', ' ', description)
                    # Remove extra whitespace
                    clean_description = ' '.join(clean_description.split())
                    # Convert to ASCII
                    # clean_description = convert_to_ascii(clean_description)
                    print(f"{clean_description}")
                
                print("-" * 40)
        
        if not items:
            print("No weather items found in the feed.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def SetLang():
    
    while True:
       try:
            print("\nSelect the weather report language: 'E' for English or 'F' for Français")

            lang = input("\nLanguage Report: ")
            lang = lang.strip().lower()
            
            #print(f"\nThe lang selected is : {lang}")
            
            #print(f"ASCII values: {[ord(c) for c in lang]}")
            
            if lang == "f" or lang == "e":
                return lang
            elif "f" in lang:
                print("Found 'f' in input, returning 'f'")
                return "f"
            elif "e" in lang:
                print("Found 'e' in input, returning 'e'")
                return "e"
            else:
                print(f"\nNot good letter '{lang}' ...")
                
       except ValueError:
            print("Please enter a valid letter.")
            
def IsAlertOnly():                
    while True:
       try:
            print("\nDo you want to read the Alerts only ? 'Y' for YES or 'N' for No")

            alert = input("\nAlert only: ")
            alert = alert.strip().lower()
            
            if alert == "y":
                return True
            elif alert == "n":
                return False
            elif "y" in alert:
                return True
            elif "n" in alert:
                return False
            else:
                print(f"\nNot good answer '{lang}' ...")
                
       except ValueError:
            print("Please enter a valid letter.")   
   
   
def main():
    """Main function to run the weather app"""
    
    LANG = SetLang()
    ALERT = IsAlertOnly()
    
    while True:
        # Display menu and get choice
        display_menu()
        choice = get_menu_choice()
        
        if choice == 0:
            print("Exiting the weather forecast application. Goodbye!")
            sys.exit(0)
        
        # Get the selected city and URL
        city_name = list(CITIES.keys())[choice - 1]
        city_url = CITIES[city_name]
        
        # Parse and display the weather for the selected city
        if ALERT == True:
            parse_weather_rss("alerts", LANG, city_url, city_name)
        else:
            parse_weather_rss("weather", LANG, city_url, city_name)
        
        # Wait for user to press Enter before showing menu again
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    print("Weather Quebec Forecast Application")
    print("----------------------------")
    main()
