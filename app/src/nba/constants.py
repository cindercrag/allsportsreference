# NBA Constants and Configuration
# Structured as dictionaries for better organization and extensibility

# Basic sport configuration
SPORT_CONFIG = {
    'name': 'nba',
    'display_name': 'NBA',
    'base_domain': 'basketball-reference.com'
}

# URL templates for different data endpoints
URLS = {
    'season_page': 'http://www.basketball-reference.com/leagues/NBA_{year}.html',
    'schedule': 'http://www.basketball-reference.com/teams/{team}/{year}_games.html',
    'boxscore': 'https://www.basketball-reference.com/boxscores/{game_id}.html',
    'boxscores_date': 'https://www.basketball-reference.com/boxscores/?month={month}&day={day}&year={year}',
    'player': 'https://www.basketball-reference.com/players/{first_letter}/{player_id}.html',
    'roster': 'https://www.basketball-reference.com/teams/{team}/{year}.html'
}

# Backward compatibility - keep original constants for existing code
SEASON_PAGE_URL = URLS['season_page'].replace('{year}', '%s')
SCHEDULE_URL = URLS['schedule'].replace('{team}', '%s').replace('{year}', '%s')
BOXSCORE_URL = URLS['boxscore'].replace('{game_id}', '%s')
BOXSCORES_URL = URLS['boxscores_date'].replace('{month}', '%s').replace('{day}', '%s').replace('{year}', '%s')
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
        get_url('schedule', team='LAL', year=2024)
        get_url('boxscores_date', month=12, day=25, year=2024)
    """
    if endpoint not in URLS:
        raise ValueError(f"Unknown endpoint: {endpoint}. Available: {list(URLS.keys())}")
    
    return URLS[endpoint].format(**kwargs)