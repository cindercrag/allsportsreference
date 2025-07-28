import pandas as pd
from .nfl_modules import _retrieve_team_schedule
from ..utils.common import export_dataframe_to_csv
from .models import NFLGameLogData, NFLGameLogColumnMapping, convert_nfl_gamelog_to_models


class Schedule:
    """
    Class to handle NFL team schedule/game log data for a given team and season.
    
    This class is responsible for parsing and storing game log data, including
    game details, scores, statistics, and performance metrics. It provides methods
    to retrieve the complete schedule for a specified team and year.

    A team abbreviation and year can be specified to pull data for that specific
    team's schedule. The `games` attribute will contain all game data as a list
    of dictionaries.
    """

    def __init__(self, team_abbrev, year):
        """
        Initialize Schedule with team abbreviation and year.
        
        Parameters
        ----------
        team_abbrev : str
            Team abbreviation (e.g., 'PHI', 'NE', 'KC')
        year : str or int
            The year to retrieve schedule data for
        """
        self.team_abbrev = team_abbrev.upper()
        self.year = str(year)
        self.games = _retrieve_team_schedule(self.team_abbrev, self.year)
    
    def get_game(self, week):
        """
        Get a specific game by week number.
        
        Parameters
        ----------
        week : int or str
            The week number to retrieve
            
        Returns
        -------
        dict or None
            Game data for the specified week, or None if not found
        """
        week_str = str(week)
        for game in self.games:
            if game.get('Week') == week_str:
                return game
        return None
    
    def get_regular_season_games(self):
        """
        Get only regular season games (excluding playoffs).
        
        Returns
        -------
        list
            List of regular season game dictionaries
        """
        regular_season = []
        for game in self.games:
            # Regular season weeks are typically 1-18
            week = game.get('Week', '')
            if week.isdigit() and 1 <= int(week) <= 18:
                regular_season.append(game)
        return regular_season
    
    def get_playoff_games(self):
        """
        Get only playoff games.
        
        Returns
        -------
        list
            List of playoff game dictionaries
        """
        playoff_games = []
        for game in self.games:
            # Playoff games typically have week > 18 or special indicators
            week = game.get('Week', '')
            if week.isdigit() and int(week) > 18:
                playoff_games.append(game)
        return playoff_games
    
    def get_wins(self):
        """
        Get all games where the team won.
        
        Returns
        -------
        list
            List of game dictionaries where team won
        """
        return [game for game in self.games if game.get('Result') == 'W']
    
    def get_losses(self):
        """
        Get all games where the team lost.
        
        Returns
        -------
        list
            List of game dictionaries where team lost
        """
        return [game for game in self.games if game.get('Result') == 'L']
    
    def get_home_games(self):
        """
        Get all home games (no '@' in location).
        
        Returns
        -------
        list
            List of home game dictionaries
        """
        return [game for game in self.games if game.get('Location', '') != '@']
    
    def get_away_games(self):
        """
        Get all away games ('@' in location).
        
        Returns
        -------
        list
            List of away game dictionaries
        """
        return [game for game in self.games if game.get('Location', '') == '@']
    
    def to_dataframe(self):
        """
        Convert schedule data to a pandas DataFrame.
        
        Returns
        -------
        pandas.DataFrame
            DataFrame containing all game log data
        """
        if not self.games:
            return pd.DataFrame()
        
        return pd.DataFrame(self.games)
    
    def to_csv(self, filename=None):
        """
        Export schedule data to CSV file.
        
        Parameters
        ----------
        filename : str, optional
            Custom filename for the CSV export. If not provided, auto-generates
            based on team and year.
            
        Returns
        -------
        str
            Path to the exported CSV file
        """
        import os
        from pathlib import Path
        
        df = self.to_dataframe()
        
        if filename is None:
            filename = f"{self.year}_{self.team_abbrev.lower()}_schedule.csv"
        
        try:
            return export_dataframe_to_csv(
                df, 
                filename, 
                sport=constants.SPORT, 
                season=self.year,
                team=self.team_abbrev,
                data_type='schedule'
            )
        except Exception as e:
            # Fallback to proper directory structure manually
            # Create the proper directory structure: data/nfl/2024/teams/BUF/
            base_dir = Path("data")
            full_dir = base_dir / constants.SPORT / self.year / "teams" / self.team_abbrev.upper()
            full_dir.mkdir(parents=True, exist_ok=True)
            
            fallback_filename = full_dir / f"{self.year}_{self.team_abbrev.lower()}_schedule.csv"
            df.to_csv(fallback_filename, index=False)
            print(f"DataFrame exported to '{fallback_filename}' (fallback)")
            return str(fallback_filename)
    
    def to_models(self):
        """
        Convert schedule data to Pydantic models for type safety.
        
        Returns
        -------
        list
            List of NFLGameLogData Pydantic models
        """
        return convert_nfl_gamelog_to_models(self.games)
    
    def __len__(self):
        """Return the number of games in the schedule."""
        return len(self.games)
    
    def __getitem__(self, index):
        """Allow indexing into the games list."""
        return self.games[index]
    
    def __iter__(self):
        """Allow iteration over games."""
        return iter(self.games)
    
    def __repr__(self):
        """String representation of the Schedule object."""
        return f"Schedule({self.team_abbrev}, {self.year}): {len(self.games)} games"


# Import constants after defining the class to avoid circular imports
from . import constants
