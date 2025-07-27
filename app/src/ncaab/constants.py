"""
NCAAB (NCAA Basketball) constants and URL templates.

This module contains URL templates and configuration for college basketball
data scraping from sports-reference.com for both men's and women's leagues.
"""

# Sport configuration using the modernized dictionary structure
SPORT_CONFIG = {
    'name': 'ncaab',
    'display_name': 'NCAA Basketball',
    'full_name': 'NCAA Division I Basketball',
    'base_url': 'https://www.sports-reference.com/cbb',
    'reference_site': 'College Basketball Reference',
    'leagues': {
        'men': {
            'name': 'men',
            'display_name': 'NCAA Men\'s Basketball',
            'path_segment': 'men'
        },
        'women': {
            'name': 'women',
            'display_name': 'NCAA Women\'s Basketball',
            'path_segment': 'women'
        }
    }
}

# URL templates for different data types (supports both men's and women's leagues)
URLS = {
    'basic_stats': 'https://www.sports-reference.com/cbb/seasons/{league}/{year}-school-stats.html',
    'basic_opponent_stats': 'https://www.sports-reference.com/cbb/seasons/{league}/{year}-opponent-stats.html',
    'advanced_stats': 'https://www.sports-reference.com/cbb/seasons/{league}/{year}-advanced-school-stats.html',
    'advanced_opponent_stats': 'https://www.sports-reference.com/cbb/seasons/{league}/{year}-advanced-opponent-stats.html',
    'schedule': 'https://www.sports-reference.com/cbb/schools/{team}/{year}-schedule.html',
    'boxscore': 'https://www.sports-reference.com/cbb/boxscores/{game_id}.html',
    'boxscores_date': 'https://www.sports-reference.com/cbb/boxscores/index.cgi?month={month}&day={day}&year={year}',
    'rankings': 'https://www.sports-reference.com/cbb/seasons/{league}/{year}-polls-old.html',
    'conferences': 'https://www.sports-reference.com/cbb/seasons/{league}/{year}.html',
    'conference': 'https://www.sports-reference.com/cbb/conferences/{conf}/{year}.html',
    'player': 'https://www.sports-reference.com/cbb/players/{player_id}.html',
    'roster': 'https://www.sports-reference.com/cbb/schools/{team}/{year}.html',
    'season_page': 'https://www.sports-reference.com/cbb/seasons/{league}/{year}.html',
    'standings': 'https://www.sports-reference.com/cbb/seasons/{league}/{year}.html',
    'tournament': 'https://www.sports-reference.com/cbb/postseason/{league}/{year}-ncaa-tournament.html'
}

# Complete configuration dictionary
NCAAB_CONFIG = {
    **SPORT_CONFIG,
    'urls': URLS
}


def get_url(url_type, league='men', **kwargs):
    """
    Get a formatted URL for the specified type and league.
    
    Parameters
    ----------
    url_type : str
        Type of URL to retrieve (e.g., 'season_page', 'schedule', 'roster')
    league : str, default 'men'
        League type - 'men' or 'women'
    **kwargs
        Keyword arguments for URL formatting (year, team, etc.)
        
    Returns
    -------
    str
        Formatted URL
        
    Examples
    --------
    >>> get_url('season_page', league='men', year=2024)
    'https://www.sports-reference.com/cbb/seasons/men/2024.html'
    
    >>> get_url('season_page', league='women', year=2024)
    'https://www.sports-reference.com/cbb/seasons/women/2024.html'
    
    >>> get_url('schedule', team='duke', year=2024)
    'https://www.sports-reference.com/cbb/schools/duke/2024-schedule.html'
    
    >>> get_url('basic_stats', league='women', year=2024)
    'https://www.sports-reference.com/cbb/seasons/women/2024-school-stats.html'
    """
    if url_type not in URLS:
        available_types = ', '.join(URLS.keys())
        raise ValueError(f"Unknown URL type '{url_type}'. Available types: {available_types}")
    
    if league not in SPORT_CONFIG['leagues']:
        available_leagues = ', '.join(SPORT_CONFIG['leagues'].keys())
        raise ValueError(f"Unknown league '{league}'. Available leagues: {available_leagues}")
    
    # Add league to kwargs for URL formatting
    kwargs['league'] = league
    
    return URLS[url_type].format(**kwargs)


# Convenience functions for specific leagues
def get_mens_url(url_type, **kwargs):
    """Get a URL for men's basketball."""
    return get_url(url_type, league='men', **kwargs)


def get_womens_url(url_type, **kwargs):
    """Get a URL for women's basketball."""
    return get_url(url_type, league='women', **kwargs)


def get_league_config(league='men'):
    """
    Get configuration for a specific league.
    
    Parameters
    ----------
    league : str, default 'men'
        League type - 'men' or 'women'
        
    Returns
    -------
    dict
        League configuration
    """
    if league not in SPORT_CONFIG['leagues']:
        available_leagues = ', '.join(SPORT_CONFIG['leagues'].keys())
        raise ValueError(f"Unknown league '{league}'. Available leagues: {available_leagues}")
    
    return SPORT_CONFIG['leagues'][league]


# Backward compatibility - keep old constants for existing code
BASIC_STATS_URL = URLS['basic_stats']
BASIC_OPPONENT_STATS_URL = URLS['basic_opponent_stats']
ADVANCED_STATS_URL = URLS['advanced_stats']
ADVANCED_OPPONENT_STATS_URL = URLS['advanced_opponent_stats']
SCHEDULE_URL = URLS['schedule']
BOXSCORE_URL = URLS['boxscore']
BOXSCORES_URL = URLS['boxscores_date']
RANKINGS_URL = URLS['rankings']
CONFERENCES_URL = URLS['conferences']
CONFERENCE_URL = URLS['conference']
PLAYER_URL = URLS['player']
ROSTER_URL = URLS['roster']
