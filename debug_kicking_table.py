#!/usr/bin/env python3
"""
Debug Kicking Table Structure
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
script_dir = Path(__file__).parent.absolute()
env_path = script_dir / '.env'
load_dotenv(env_path, override=True)

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from fixed_boxscore_scraper import FixedNFLBoxscoreScraper

print('🔍 DEBUGGING KICKING TABLE STRUCTURE')
print('=' * 42)

try:
    boxscore_id = '202411030buf'
    scraper = FixedNFLBoxscoreScraper()
    
    # Fetch HTML
    soup = scraper.fetch_boxscore_html(boxscore_id)
    if not soup:
        print("❌ Failed to fetch HTML")
        exit()
    
    # Find the kicking table
    kicking_div = soup.find('div', {'id': 'div_kicking'})
    if not kicking_div:
        print("❌ No div_kicking found")
        exit()
    
    kicking_table = kicking_div.find('table')
    if not kicking_table:
        print("❌ No table found in div_kicking")
        exit()
    
    print("✅ Found kicking table")
    
    # Get headers
    headers = []
    header_row = kicking_table.find('thead')
    if header_row:
        for th in header_row.find_all('th'):
            header_text = th.get_text(strip=True)
            headers.append(header_text)
    
    print(f"📋 Headers: {headers}")
    print()
    
    # Get all rows in tbody
    tbody = kicking_table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        print(f"📊 Found {len(rows)} rows in tbody:")
        print()
        
        for i, row in enumerate(rows):
            cells = []
            for cell in row.find_all(['td', 'th']):
                cell_text = cell.get_text(strip=True)
                cells.append(cell_text)
            
            print(f"Row {i+1}: {cells}")
            
            # Identify what type of row this is
            if len(cells) >= 4:
                potential_player = cells[3] if len(cells) > 3 else ""
                potential_team = cells[4] if len(cells) > 4 else ""
                
                row_type = "UNKNOWN"
                if not potential_player or potential_player == "Player":
                    row_type = "HEADER"
                elif potential_player in ["MIA", "BUF"] and not potential_team:
                    row_type = "TEAM TOTAL"
                elif potential_team in ["MIA", "BUF"]:
                    row_type = "PLAYER"
                elif "(" in potential_player and ")" in potential_player:
                    row_type = "SUMMARY/TOTAL"
                
                print(f"  → Type: {row_type} | Player: '{potential_player}' | Team: '{potential_team}'")
            print()

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
