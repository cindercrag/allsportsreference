"""
NHL (National Hockey League) constants and URL templates.

This module contains URL templates and configuration for NHL
data scraping from hockey-reference.com.
"""

# Sport configuration using the modernized dictionary structure
SPORT_CONFIG = {
    'name': 'nhl',
    'display_name': 'NHL',
    'full_name': 'National Hockey League',
    'base_url': 'https://www.hockey-reference.com',
    'reference_site': 'Hockey Reference'
}

# URL templates for different data types
URLS = {
    'season_page': 'http://www.hockey-reference.com/leagues/NHL_{year}.html',
    'schedule': 'https://www.hockey-reference.com/teams/{team}/{year}_gamelog.html',
    'boxscore': 'https://www.hockey-reference.com/boxscores/{game_id}.html',
    'boxscores_date': 'https://www.hockey-reference.com/boxscores/index.fcgi?month={month}&day={day}&year={year}',
    'player': 'https://www.hockey-reference.com/players/{letter}/{player_id}.html',
    'roster': 'https://www.hockey-reference.com/teams/{team}/{year}.html',
    'standings': 'https://www.hockey-reference.com/leagues/NHL_{year}.html',
    'team_stats': 'https://www.hockey-reference.com/teams/{team}/{year}.html',
    'playoffs': 'https://www.hockey-reference.com/playoffs/NHL_{year}.html'
}

# Complete configuration dictionary
NHL_CONFIG = {
    **SPORT_CONFIG,
    'urls': URLS
}


def get_url(url_type, **kwargs):
    """
    Get a formatted URL for the specified type.
    
    Parameters
    ----------
    url_type : str
        Type of URL to retrieve (e.g., 'season_page', 'schedule', 'roster')
    **kwargs
        Keyword arguments for URL formatting (year, team, letter, etc.)
        
    Returns
    -------
    str
        Formatted URL
        
    Examples
    --------
    >>> get_url('season_page', year=2024)
    'http://www.hockey-reference.com/leagues/NHL_2024.html'
    
    >>> get_url('schedule', team='BOS', year=2024)
    'https://www.hockey-reference.com/teams/BOS/2024_gamelog.html'
    
    >>> get_url('player', letter='c', player_id='crosbsi01')
    'https://www.hockey-reference.com/players/c/crosbsi01.html'
    """
    if url_type not in URLS:
        available_types = ', '.join(URLS.keys())
        raise ValueError(f"Unknown URL type '{url_type}'. Available types: {available_types}")
    
    return URLS[url_type].format(**kwargs)


# Backward compatibility - keep old constants for existing code
SEASON_PAGE_URL = URLS['season_page']
SCHEDULE_URL = URLS['schedule']
BOXSCORE_URL = URLS['boxscore']
BOXSCORES_URL = URLS['boxscores_date']
PLAYER_URL = URLS['player']
ROSTER_URL = URLS['roster']