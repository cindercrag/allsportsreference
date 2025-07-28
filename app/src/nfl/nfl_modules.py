from . import constants
from ..utils.common import _curl_page, parse_table, _no_data_found
from .models import NFLColumnMapping
import pandas as pd


def _retrieve_all_teams(year):
    """
    Find and create Team instances for all teams in the given season.

    For a given season, parses the specified NFL stats table and finds all
    requested stats. Each team then has a Team instance created which
    includes all requested stats and a few identifiers, such as the team's
    name and abbreviation. All of the individual Team instances are added
    to a list.

    Note that this method is called directly once Teams is invoked and does
    not need to be called manually.

    Parameters
    ----------
    year : string
        The requested year to pull stats from.
    season_page : string (optional)
        Link with filename to the local season page.

    Returns
    -------
    list
        Returns a list of dictionaries representing all teams' stats.
    """
    from bs4 import BeautifulSoup

    html = _curl_page(constants.SEASON_PAGE_URL % year)
    if not html:
        _no_data_found()
        return []
    
    soup = BeautifulSoup(html, 'lxml')
    
    teams_list = []
    
    # Parse both AFC and NFC tables
    for conference in ['AFC', 'NFC']:
        table = soup.find('table', id=conference)
        if not table:
            continue
            
        # Get headers from the table with proper descriptions using our model mapping
        thead = table.find('thead')
        if thead:
            header_row = thead.find('tr')
            headers = []
            for th in header_row.find_all(['th', 'td']):
                # Use aria-label for proper column names, fall back to text
                label = th.get('aria-label', th.text.strip())
                # Use our model mapping to get the preferred descriptive name
                preferred_name = NFLColumnMapping.WEBSITE_TO_MODEL.get(label, label)
                final_name = NFLColumnMapping.PREFERRED_COLUMNS.get(preferred_name, label)
                headers.append(final_name)
        else:
            # Use preferred column names from our model
            headers = NFLColumnMapping.get_preferred_column_names()
        
        # Get data rows
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            
            for row in rows:
                cells = [td.text.strip() for td in row.find_all(['td', 'th'])]
                
                # Skip section headers (they only have 1 cell)
                if len(cells) == len(headers):
                    # Create dictionary for this team
                    team_data = dict(zip(headers, cells))
                    
                    # Extract team abbreviation from the team link
                    # The first cell contains the team name and link
                    first_cell = row.find(['td', 'th'])  # Get first cell (td or th)
                    if first_cell:
                        team_link = first_cell.find('a')
                        if team_link:
                            href = team_link.get('href', '')
                            if '/teams/' in href:
                                # Extract abbreviation from href like "/teams/buf/2024.htm"
                                parts = href.split('/teams/')
                                if len(parts) > 1:
                                    abbrev = parts[1].split('/')[0].upper()
                                    team_data['Abbrev'] = abbrev
                    
                    # Add conference information
                    team_data['Conference'] = conference
                    
                    teams_list.append(team_data)

    return teams_list


def _retrieve_team_schedule(team_abbrev, year):
    """
    Retrieve and parse team schedule/game log data for a given team and season.

    For a given team and season, parses the team's game log page and extracts
    all game data including scores, statistics, and performance metrics.

    Parameters
    ----------
    team_abbrev : str
        The team abbreviation (e.g., 'PHI', 'NE', 'KC')
    year : str
        The requested year to pull schedule data from.

    Returns
    -------
    list
        Returns a list of dictionaries representing all games in the schedule.
    """
    from bs4 import BeautifulSoup

    # Build the URL using the schedule constant
    url = constants.SCHEDULE_URL % (team_abbrev.lower(), year)
    html = _curl_page(url)
    if not html:
        _no_data_found()
        return []
    
    soup = BeautifulSoup(html, 'lxml')
    
    games_list = []
    
    # Look for tables with game log data
    # The main table has ID like "team-year-regular-season-game-log"
    table_id_patterns = [
        f"{team_abbrev.lower()}-{year}-regular-season-game-log",
        f"{team_abbrev.lower()}-{year}-playoffs-game-log",
        "team-year-regular-season-game-log",
        "team-year-playoffs-game-log"
    ]
    
    # Try to find tables by various ID patterns and also look for tables with "game" in the ID
    tables = []
    for pattern in table_id_patterns:
        table = soup.find('table', id=pattern)
        if table:
            tables.append(table)
    
    # Also look for any table with "game" in the ID as backup
    if not tables:
        all_tables = soup.find_all('table')
        for table in all_tables:
            table_id = table.get('id', '')
            if 'game' in table_id.lower() and 'log' in table_id.lower():
                tables.append(table)
    
    for table in tables:
        if not table:
            continue
            
        # Get headers from the table
        thead = table.find('thead')
        headers = []
        
        if thead:
            # Look for the last row in thead (sometimes there are multiple header rows)
            header_rows = thead.find_all('tr')
            if header_rows:
                header_row = header_rows[-1]  # Use the last header row
                for th in header_row.find_all(['th', 'td']):
                    # Use aria-label for proper column names, fall back to text
                    label = th.get('aria-label', th.text.strip())
                    if label:
                        headers.append(label)
        
        # If no headers found, create generic ones based on typical game log structure
        if not headers:
            # Common game log columns based on the webpage structure
            headers = ['Week', 'Game', 'Date', 'Day', 'Location', 'Opponent', 'Result', 
                      'Team_Score', 'Opp_Score', 'Pass_Cmp', 'Pass_Att', 'Pass_Cmp_Pct',
                      'Pass_Yds', 'Pass_TD', 'Pass_Rate', 'Pass_Sk', 'Pass_Sk_Yds',
                      'Rush_Att', 'Rush_Yds', 'Rush_TD', 'Rush_YPC', 'Tot_Plays',
                      'Tot_Yds', 'Tot_YPP', 'TO_Fumble', 'TO_Int', 'Penalty_Count',
                      'Penalty_Yds', 'Third_Down_Success', 'Third_Down_Att', 'Fourth_Down_Success',
                      'Fourth_Down_Att', 'Time_of_Possession']
        
        # Get data rows
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            
            for row in rows:
                # Skip rows that are section headers or dividers
                if 'thead' in row.get('class', []) or row.find('th', {'scope': 'col'}):
                    continue
                
                cells = []
                for cell in row.find_all(['td', 'th']):
                    # Get the text content, handling links for opponent names
                    if cell.find('a'):
                        # If there's a link, use the link text (opponent abbreviation)
                        cells.append(cell.find('a').text.strip())
                    else:
                        cells.append(cell.text.strip())
                
                # Only process rows that have data (skip empty or header rows)
                if len(cells) >= 6 and cells[0] and cells[0] not in ['Week', 'G#', '']:
                    # Create dictionary for this game, using available headers
                    game_data = {}
                    for i, value in enumerate(cells):
                        if i < len(headers):
                            game_data[headers[i]] = value
                        else:
                            # Handle extra columns that might not have headers
                            game_data[f'Column_{i}'] = value
                    
                    # Map common column names to our expected names
                    column_mapping = {
                        'Opp': 'Opponent',
                        'Rslt': 'Result', 
                        'Pts': 'Team_Score',
                        'PtsO': 'Opp_Score',
                        'Cmp': 'Pass_Cmp',
                        'Att': 'Pass_Att',
                        'Cmp%': 'Pass_Cmp_Pct',
                        'Yds': 'Pass_Yds',
                        'TD': 'Pass_TD',
                        'Y/A': 'Pass_YPA',
                        'AY/A': 'Pass_AY_A',
                        'Rate': 'Pass_Rate',
                        'Sk': 'Pass_Sk',
                        'Ply': 'Tot_Plays',
                        'Tot': 'Tot_Yds',
                        'Y/P': 'Tot_YPP',
                        'FL': 'TO_Fumble',
                        'Int': 'TO_Int',
                        'ToP': 'Time_of_Possession',
                        'Pen': 'Penalty_Count',
                        '3DConv': 'Third_Down_Success',
                        '3DAtt': 'Third_Down_Att',
                        '4DConv': 'Fourth_Down_Success',
                        '4DAtt': 'Fourth_Down_Att',
                        'Gtm': 'Game',
                        ' ': 'Location'  # This column indicates @ for away games
                    }
                    
                    # Apply column mapping
                    mapped_game_data = {}
                    for key, value in game_data.items():
                        mapped_key = column_mapping.get(key, key)
                        mapped_game_data[mapped_key] = value
                    
                    # Clean up some common field names and values
                    if 'Date' in mapped_game_data:
                        # Keep date as-is for now
                        pass
                    
                    if 'Result' in mapped_game_data:
                        # Ensure Result is just W/L/T
                        result = mapped_game_data['Result'].upper()
                        if result.startswith('W'):
                            mapped_game_data['Result'] = 'W'
                        elif result.startswith('L'):
                            mapped_game_data['Result'] = 'L'
                        elif result.startswith('T'):
                            mapped_game_data['Result'] = 'T'
                    
                    # Handle the location field (empty means home, @ means away)
                    if 'Location' in mapped_game_data:
                        location = mapped_game_data['Location'].strip()
                        if location == '@' or location.lower() == 'away':
                            mapped_game_data['Location'] = '@'
                        else:
                            mapped_game_data['Location'] = ''  # Home game
                    
                    # Add team abbreviation for reference
                    mapped_game_data['Team'] = team_abbrev.upper()
                    mapped_game_data['Season'] = year
                    
                    games_list.append(mapped_game_data)

    return games_list

