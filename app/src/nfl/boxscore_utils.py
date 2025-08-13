"""
Utility functions for working with NFL boxscore IDs and data.

This module provides functions to parse and work with boxscore IDs from
pro-football-reference.com, which follow a specific format.
"""

from typing import NamedTuple, Optional
from datetime import datetime


class BoxscoreInfo(NamedTuple):
    """
    Parsed information from a boxscore ID.
    
    Attributes
    ----------
    boxscore_id : str
        The full boxscore ID (e.g., '202309070kan')
    date : str
        The game date in YYYY-MM-DD format
    game_number : int
        The game number (0 for first/only game, 1+ for doubleheaders)
    home_team : str
        The home team abbreviation (lowercase)
    url : str
        The full URL to the boxscore page
    """
    boxscore_id: str
    date: str
    game_number: int
    home_team: str
    url: str


def parse_boxscore_id(boxscore_id: str) -> Optional[BoxscoreInfo]:
    """
    Parse a boxscore ID into its components.
    
    The boxscore ID format is:
    - Positions 1-8: Date (YYYYMMDD)
    - Position 9: Game number (0 for first/only game, 1+ for doubleheaders)
    - Position 10+: Home team abbreviation (lowercase)
    
    Parameters
    ----------
    boxscore_id : str
        The boxscore ID to parse (e.g., '202309070kan')
        
    Returns
    -------
    BoxscoreInfo or None
        Parsed boxscore information, or None if the ID is invalid
        
    Examples
    --------
    >>> info = parse_boxscore_id('202309070kan')
    >>> info.date
    '2023-09-07'
    >>> info.game_number
    0
    >>> info.home_team
    'kan'
    """
    if not boxscore_id or len(boxscore_id) < 10:
        return None
    
    try:
        # Extract components
        date_part = boxscore_id[:8]        # YYYYMMDD
        game_num_char = boxscore_id[8:9]   # Game number
        home_team = boxscore_id[9:]        # Home team abbreviation
        
        # Parse and validate date
        try:
            date_obj = datetime.strptime(date_part, '%Y%m%d')
            formatted_date = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            return None
        
        # Parse game number
        try:
            game_number = int(game_num_char)
        except ValueError:
            return None
        
        # Validate home team (should be alphabetic and 2-4 characters)
        if not home_team.isalpha() or len(home_team) < 2 or len(home_team) > 4:
            return None
        
        # Construct URL
        url = f"https://www.pro-football-reference.com/boxscores/{boxscore_id}.htm"
        
        return BoxscoreInfo(
            boxscore_id=boxscore_id,
            date=formatted_date,
            game_number=game_number,
            home_team=home_team,
            url=url
        )
        
    except (IndexError, ValueError):
        return None


def is_doubleheader(boxscore_id: str) -> bool:
    """
    Check if a boxscore ID represents a doubleheader game.
    
    Parameters
    ----------
    boxscore_id : str
        The boxscore ID to check
        
    Returns
    -------
    bool
        True if this is a doubleheader (game number > 0), False otherwise
    """
    info = parse_boxscore_id(boxscore_id)
    return info is not None and info.game_number > 0


def get_game_date(boxscore_id: str) -> Optional[str]:
    """
    Extract the game date from a boxscore ID.
    
    Parameters
    ----------
    boxscore_id : str
        The boxscore ID
        
    Returns
    -------
    str or None
        The game date in YYYY-MM-DD format, or None if invalid
    """
    info = parse_boxscore_id(boxscore_id)
    return info.date if info else None


def get_home_team(boxscore_id: str) -> Optional[str]:
    """
    Extract the home team from a boxscore ID.
    
    Parameters
    ----------
    boxscore_id : str
        The boxscore ID
        
    Returns
    -------
    str or None
        The home team abbreviation (lowercase), or None if invalid
    """
    info = parse_boxscore_id(boxscore_id)
    return info.home_team if info else None


def construct_boxscore_id(date: str, home_team: str, game_number: int = 0) -> str:
    """
    Construct a boxscore ID from components.
    
    Parameters
    ----------
    date : str
        The game date in YYYY-MM-DD format
    home_team : str
        The home team abbreviation
    game_number : int, optional
        The game number (default: 0 for first/only game)
        
    Returns
    -------
    str
        The constructed boxscore ID
        
    Examples
    --------
    >>> construct_boxscore_id('2023-09-07', 'kan')
    '202309070kan'
    >>> construct_boxscore_id('2023-09-07', 'kan', 1)
    '202309071kan'
    """
    try:
        # Parse date and convert to YYYYMMDD format
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        date_part = date_obj.strftime('%Y%m%d')
        
        # Ensure home team is lowercase
        home_team_lower = home_team.lower()
        
        # Construct boxscore ID
        return f"{date_part}{game_number}{home_team_lower}"
        
    except ValueError:
        raise ValueError(f"Invalid date format: {date}. Expected YYYY-MM-DD")


# Example usage and testing
if __name__ == "__main__":
    # Test with some real boxscore IDs
    test_ids = [
        '202309070kan',  # Kansas City home game
        '202309170jax',  # Jacksonville home game
        '202309240kan',  # Kansas City home game
    ]
    
    print("Testing boxscore ID parsing:")
    print("=" * 50)
    
    for boxscore_id in test_ids:
        info = parse_boxscore_id(boxscore_id)
        if info:
            print(f"ID: {boxscore_id}")
            print(f"  Date: {info.date}")
            print(f"  Game #: {info.game_number}")
            print(f"  Home team: {info.home_team}")
            print(f"  Doubleheader: {is_doubleheader(boxscore_id)}")
            print(f"  URL: {info.url}")
            print()
        else:
            print(f"Invalid boxscore ID: {boxscore_id}")
