#!/usr/bin/env python3
"""
Analyze Advanced Passing Table Structure
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

print('🎯 ANALYZING ADVANCED PASSING TABLE STRUCTURE')
print('=' * 50)

try:
    boxscore_id = '202411030buf'
    scraper = FixedNFLBoxscoreScraper()
    
    # Fetch HTML
    soup = scraper.fetch_boxscore_html(boxscore_id)
    if not soup:
        print("❌ Failed to fetch HTML")
        exit()
    
    # Find the advanced passing table
    advanced_div = soup.find('div', {'id': 'div_passing_advanced'})
    if not advanced_div:
        print("❌ No div_passing_advanced found")
        exit()
    
    advanced_table = advanced_div.find('table')
    if not advanced_table:
        print("❌ No table found in div_passing_advanced")
        exit()
    
    print("✅ Found advanced passing table")
    
    # Get headers
    headers = []
    header_row = advanced_table.find('thead')
    if header_row:
        for th in header_row.find_all('th'):
            header_text = th.get_text(strip=True)
            headers.append(header_text)
    
    print(f"📋 Headers: {headers}")
    print(f"📊 Total columns: {len(headers)}")
    print()
    
    # Get all rows in tbody
    tbody = advanced_table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        print(f"📈 Found {len(rows)} rows in tbody:")
        print()
        
        for i, row in enumerate(rows):
            cells = []
            for cell in row.find_all(['td', 'th']):
                cell_text = cell.get_text(strip=True)
                cells.append(cell_text)
            
            if len(cells) >= 3:  # Only show non-empty rows
                print(f"Row {i+1}: {cells}")
                
                # Identify player and team
                if len(cells) >= 2:
                    potential_player = cells[0] if len(cells) > 0 else ""
                    potential_team = cells[1] if len(cells) > 1 else ""
                    
                    if potential_player and potential_team and potential_player != "Player":
                        print(f"  → Player: '{potential_player}' | Team: '{potential_team}'")
                print()
    
    # Estimate table size impact
    print("🔍 TABLE STRUCTURE ANALYSIS:")
    print(f"  • Column count: {len(headers)}")
    print(f"  • Expected players per game: ~3-6 (QBs, backups, wildcat)")
    print()
    
    print("💭 RECOMMENDATION:")
    if len(headers) > 15:
        print("  📋 SEPARATE TABLE - Too many columns for main player_stats")
        print("     • Create dedicated 'boxscore_advanced_passing' table")
        print("     • Link via boxscore_id + player_name + team")
        print("     • Keeps main table manageable")
    else:
        print("  📋 EXTEND EXISTING TABLE - Manageable number of columns")
        print("     • Add columns to existing 'boxscore_player_stats'")
        print("     • Most columns will be NULL for non-QBs")
        print("     • Simpler queries, single table")

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
