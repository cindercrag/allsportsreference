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
    from bs4 import BeautifulSoup, Comment

    # Build the URL using the schedule constant
    url = constants.SCHEDULE_URL % (team_abbrev.lower(), year)
    html = _curl_page(url)
    if not html:
        _no_data_found()
        return []
    
    soup = BeautifulSoup(html, 'lxml')
    
    games_list = []
    
    # First try to find tables in the main HTML
    tables = soup.find_all('table')
    
    # If no tables found, look in HTML comments (common on sports-reference sites)
    if not tables:
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        
        for comment in comments:
            comment_str = str(comment)
            if '<table' in comment_str and ('game' in comment_str.lower() or team_abbrev.lower() in comment_str.lower()):
                # Parse the comment as HTML
                comment_soup = BeautifulSoup(comment_str, 'lxml')
                comment_tables = comment_soup.find_all('table')
                tables.extend(comment_tables)
    
    # Look for tables with game log data
    valid_tables = []
    for table in tables:
        table_id = table.get('id', '').lower()
        # Look for tables that likely contain game log data
        if any(keyword in table_id for keyword in ['game', 'log', team_abbrev.lower(), year]):
            valid_tables.append(table)
    
    # If we still don't have tables, try all tables that have date columns
    if not valid_tables:
        for table in tables:
            date_cells = table.find_all('td', {'data-stat': 'date'})
            if date_cells:
                valid_tables.append(table)
    
    for table in valid_tables:
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
                    # Use data-stat attribute if available, then aria-label, then text
                    data_stat = th.get('data-stat', '')
                    aria_label = th.get('aria-label', '')
                    text = th.text.strip()
                    
                    if data_stat:
                        headers.append(data_stat)
                    elif aria_label:
                        headers.append(aria_label)
                    elif text:
                        headers.append(text)
                    else:
                        headers.append(f'Column_{len(headers)}')
        
        # If no headers found, try to infer from data-stat attributes in first data row
        if not headers:
            tbody = table.find('tbody')
            if tbody:
                first_row = tbody.find('tr')
                if first_row:
                    for cell in first_row.find_all(['td', 'th']):
                        data_stat = cell.get('data-stat', '')
                        if data_stat:
                            headers.append(data_stat)
                        else:
                            headers.append(f'Column_{len(headers)}')
        
        # Fallback to generic headers if still nothing found
        if not headers:
            headers = ['week', 'game_num', 'game_date', 'day_of_week', 'location', 'opponent', 'result', 
                      'pts_off', 'pts_def', 'pass_cmp', 'pass_att', 'pass_cmp_pct',
                      'pass_yds', 'pass_td', 'pass_rate', 'pass_sacked', 'pass_sacked_yds',
                      'rush_att', 'rush_yds', 'rush_td', 'rush_ypc', 'total_plays',
                      'total_yds', 'total_ypp', 'turnovers_fumbles', 'turnovers_int', 'penalties_count',
                      'penalties_yds', 'third_down_success', 'third_down_att', 'fourth_down_success',
                      'fourth_down_att', 'time_of_possession']
        
        # Get data rows
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            
            for row in rows:
                # Skip rows that are section headers or dividers
                if 'thead' in row.get('class', []) or row.find('th', {'scope': 'col'}):
                    continue
                
                cells = []
                boxscore_id = None
                
                for cell in row.find_all(['td', 'th']):
                    data_stat = cell.get('data-stat', '')
                    
                    # Special handling for date column to extract boxscore ID
                    if data_stat == 'date' or data_stat == 'game_date':
                        # Look for a link in the Date cell
                        date_link = cell.find('a')
                        if date_link and date_link.get('href'):
                            href = date_link.get('href')
                            # Extract boxscore ID from href like "/boxscores/202409050kan.htm"
                            if '/boxscores/' in href:
                                # Extract the boxscore ID (e.g., "202409050kan" from "/boxscores/202409050kan.htm")
                                boxscore_id = href.split('/boxscores/')[-1].replace('.htm', '')
                            cells.append(date_link.text.strip())
                        else:
                            cells.append(cell.text.strip())
                    else:
                        # Get the text content, handling links for opponent names
                        if cell.find('a'):
                            # If there's a link, use the link text (opponent abbreviation)
                            cells.append(cell.find('a').text.strip())
                        else:
                            cells.append(cell.text.strip())
                
                # Only process rows that have data (skip empty or header rows)
                if len(cells) >= 6 and cells[0] and cells[0] not in ['Week', 'G#', 'Wk', 'week', '']:
                    # Create dictionary for this game, using available headers
                    game_data = {}
                    for i, value in enumerate(cells):
                        if i < len(headers):
                            game_data[headers[i]] = value
                        else:
                            # Handle extra columns that might not have headers
                            game_data[f'Column_{i}'] = value
                    
                    # Map data-stat attribute names to our expected names
                    data_stat_mapping = {
                        'week_num': 'Week',
                        'team_game_num_season': 'Game', 
                        'date': 'Date',
                        'game_day_of_week': 'Day',
                        'game_location': 'Location',
                        'opp_name_abbr': 'Opponent',
                        'team_game_result': 'Result',
                        'points': 'Team_Score',
                        'points_opp': 'Opp_Score',
                        'pass_cmp': 'Pass_Cmp',
                        'pass_att': 'Pass_Att',
                        'pass_cmp_pct': 'Pass_Cmp_Pct',
                        'pass_yds': 'Pass_Yds',
                        'pass_td': 'Pass_TD',
                        'pass_rating': 'Pass_Rate',
                        'pass_sacked': 'Pass_Sk',
                        'pass_sacked_yds': 'Pass_Sk_Yds',
                        'rush_att': 'Rush_Att',
                        'rush_yds': 'Rush_Yds',
                        'rush_td': 'Rush_TD',
                        'rush_yds_per_att': 'Rush_YPC',
                        'plays_offense': 'Tot_Plays',
                        'tot_yds': 'Tot_Yds',
                        'yds_per_play_offense': 'Tot_YPP',
                        'fumbles_lost': 'TO_Fumble',
                        'pass_int': 'TO_Int',
                        'penalties': 'Penalty_Count',
                        'penalty_yds': 'Penalty_Yds',
                        'third_down_success': 'Third_Down_Success',
                        'third_down_att': 'Third_Down_Att',
                        'fourth_down_success': 'Fourth_Down_Success',
                        'fourth_down_att': 'Fourth_Down_Att',
                        'time_of_poss': 'Time_of_Possession'
                    }
                    
                    # Legacy column mapping for backward compatibility
                    legacy_mapping = {
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
                    
                    # Apply both mappings
                    mapped_game_data = {}
                    for key, value in game_data.items():
                        # Try data-stat mapping first, then legacy mapping, then keep original
                        mapped_key = data_stat_mapping.get(key, legacy_mapping.get(key, key))
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
                    
                    # Add boxscore ID if found
                    if boxscore_id:
                        mapped_game_data['Boxscore_ID'] = boxscore_id
                        # Also construct the full boxscore URL for convenience
                        mapped_game_data['Boxscore_URL'] = f"https://www.pro-football-reference.com/boxscores/{boxscore_id}.htm"
                        
                        # Parse additional boxscore metadata using our utility
                        try:
                            from .boxscore_utils import parse_boxscore_id
                            boxscore_info = parse_boxscore_id(boxscore_id)
                            if boxscore_info:
                                mapped_game_data['Boxscore_Date'] = boxscore_info.date
                                mapped_game_data['Boxscore_Game_Number'] = boxscore_info.game_number
                                mapped_game_data['Boxscore_Home_Team'] = boxscore_info.home_team
                        except ImportError:
                            # If boxscore_utils is not available, skip the additional metadata
                            pass
                    
                    games_list.append(mapped_game_data)

    return games_list

