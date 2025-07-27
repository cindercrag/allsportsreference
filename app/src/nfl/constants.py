# NFL Constants and Configuration
# Structured as dictionaries for better organization and extensibility

# Basic sport configuration
SPORT_CONFIG = {
    'name': 'nfl',
    'display_name': 'NFL',
    'base_domain': 'pro-football-reference.com'
}

# URL templates for different data endpoints
URLS = {
    'season_page': 'https://www.pro-football-reference.com/years/{year}/',
    'schedule': 'https://www.pro-football-reference.com/teams/{team}/{year}/gamelog/',
    'boxscore': 'https://www.pro-football-reference.com/boxscores/{game_id}.htm',
    'boxscores_week': 'https://www.pro-football-reference.com/years/{year}/week_{week}.htm',
    'player': 'https://www.pro-football-reference.com/players/{first_letter}/{player_id}.htm',
    'roster': 'https://www.pro-football-reference.com/teams/{team}/{year}_roster.htm'
}


# Backward compatibility - keep original constants for existing code
SPORT = SPORT_CONFIG['name']
SEASON_PAGE_URL = URLS['season_page'].replace('{year}', '%s')
SCHEDULE_URL = URLS['schedule'].replace('{team}', '%s').replace('{year}', '%s')
BOXSCORE_URL = URLS['boxscore'].replace('{game_id}', '%s')
BOXSCORES_URL = URLS['boxscores_week'].replace('{year}', '%s').replace('{week}', '%s')
PLAYER_URL = URLS['player'].replace('{first_letter}', '%s').replace('{player_id}', '%s')
ROSTER_URL = URLS['roster'].replace('{team}', '%s').replace('{year}', '%s')


# Utility functions for working with the new structure
def get_url(endpoint, **kwargs):
    """
    Get a formatted URL for a specific endpoint.
    
    Args:
        endpoint (str): The endpoint key from URLS dictionary
        **kwargs: Parameters to format into the URL template
    
    Returns:
        str: Formatted URL
    
    Example:
        get_url('season_page', year=2024)
        get_url('schedule', team='NE', year=2024)
    """
    if endpoint not in URLS:
        raise ValueError(f"Unknown endpoint: {endpoint}. Available: {list(URLS.keys())}")
    
    return URLS[endpoint].format(**kwargs)
