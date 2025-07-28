from . import constants
from ..utils.common import _curl_page, parse_table, _no_data_found
from .models import NFLColumnMapping
import pandas as pd


def _add_stats_data(teams_list, team_data_dict):
    """
    Add a team's stats row to a dictionary.

    Pass table contents and a stats dictionary of all teams to accumulate
    all stats for each team in a single variable.

    Parameters
    ----------
    teams_list : generator
        A generator of all row items in a given table.
    team_data_dict : {str: {'data': str, 'rank': int}} dictionary
        A dictionary where every key is the team's abbreviation and every
        value is another dictionary with a 'data' key which contains the
        string version of the row data for the matched team, and a 'rank'
        key which is the rank of the team.

    Returns
    -------
    dictionary
        An updated version of the team_data_dict with the passed table row
        information included.
    """
    # Teams are listed in terms of rank with the first team being #1
    rank = 1
    for team_data in teams_list:
        if 'class="thead onecell"' in str(team_data):
            continue
        abbr = utils._parse_field(PARSING_SCHEME, team_data, 'abbreviation')
        try:
            team_data_dict[abbr]['data'] += team_data
        except KeyError:
            team_data_dict[abbr] = {'data': team_data, 'rank': rank}
        rank += 1
    return team_data_dict


def _retrieve_all_teams(year, season_page=None):
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

