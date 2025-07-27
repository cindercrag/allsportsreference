"""
NCAAF (College Football) constants and URL templates.

This module contains URL templates and configuration for college football
data scraping from sports-reference.com.
"""

# Sport configuration using the modernized dictionary structure
SPORT_CONFIG = {
    'name': 'ncaaf',
    'display_name': 'College Football',
    'full_name': 'NCAA Division I Football',
    'base_url': 'https://www.sports-reference.com/cfb',
    'reference_site': 'College Football Reference'
}

# URL templates for different data types
URLS = {
    'season_page': 'http://www.sports-reference.com/cfb/years/{year}-standings.html',
    'offensive_stats': 'https://www.sports-reference.com/cfb/years/{year}-team-offense.html',
    'defensive_stats': 'https://www.sports-reference.com/cfb/years/{year}-team-defense.html',
    'schedule': 'https://www.sports-reference.com/cfb/schools/{team}/{year}-schedule.html',
    'boxscore': 'https://www.sports-reference.com/cfb/boxscores/{game_id}.html',
    'boxscores_date': 'https://www.sports-reference.com/cfb/boxscores/index.cgi?month={month}&day={day}&year={year}&conf_id=',
    'conferences': 'https://www.sports-reference.com/cfb/years/{year}.html',
    'conference': 'https://www.sports-reference.com/cfb/conferences/{conf}/{year}.html',
    'cfp_rankings': 'https://www.sports-reference.com/cfb/years/{year}-polls.html',
    'rankings': 'https://www.sports-reference.com/cfb/years/{year}-polls.html',
    'player': 'https://www.sports-reference.com/cfb/players/{player_id}.html',
    'roster': 'https://www.sports-reference.com/cfb/schools/{team}/{year}-roster.html'
}

# Complete configuration dictionary
NCAAF_CONFIG = {
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
        Keyword arguments for URL formatting (year, team, etc.)
        
    Returns
    -------
    str
        Formatted URL
        
    Examples
    --------
    >>> get_url('season_page', year=2024)
    'http://www.sports-reference.com/cfb/years/2024-standings.html'
    
    >>> get_url('schedule', team='alabama', year=2024)
    'https://www.sports-reference.com/cfb/schools/alabama/2024-schedule.html'
    """
    if url_type not in URLS:
        available_types = ', '.join(URLS.keys())
        raise ValueError(f"Unknown URL type '{url_type}'. Available types: {available_types}")
    
    return URLS[url_type].format(**kwargs)


# Backward compatibility - keep old constants for existing code
SEASON_PAGE_URL = URLS['season_page']
OFFENSIVE_STATS_URL = URLS['offensive_stats']
DEFENSIVE_STATS_URL = URLS['defensive_stats']
SCHEDULE_URL = URLS['schedule']
BOXSCORE_URL = URLS['boxscore']
BOXSCORES_URL = URLS['boxscores_date']
CONFERENCES_URL = URLS['conferences']
CONFERENCE_URL = URLS['conference']
CFP_RANKINGS_URL = URLS['cfp_rankings']
RANKINGS_URL = URLS['rankings']
PLAYER_URL = URLS['player']
ROSTER_URL = URLS['roster']