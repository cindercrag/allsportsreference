import pandas as pd
from .nfl_modules import _retrieve_team_stats
from ..utils.common import export_dataframe_to_csv


class TeamStats:
    """
    Class to handle NFL team offensive statistics for a given season.
    
    This class is responsible for parsing and storing team offensive stats, including
    total yards, passing stats, rushing stats, penalties, and efficiency metrics
    from the Team Offense table on the season page.

    A year can be specified to pull offensive stats for that specific season.
    The `team_stats_dict` attribute will contain all teams' offensive data.
    """

    def __init__(self, year):
        self.year = year
        self.team_stats_dict = _retrieve_team_stats(year)
        
        # Create a lookup dictionary by abbreviation for easy access
        self._stats_by_abbrev = {}
        if self.team_stats_dict:
            for team_stats in self.team_stats_dict:
                abbrev = team_stats.get('Abbrev')
                if abbrev:
                    self._stats_by_abbrev[abbrev] = team_stats
    
    def __getattr__(self, name):
        """
        Allow access to team stats by abbreviation like team_stats.PHI
        """
        # Convert to uppercase to handle both team_stats.phi and team_stats.PHI
        abbrev = name.upper()
        if abbrev in self._stats_by_abbrev:
            return self._stats_by_abbrev[abbrev]
        raise AttributeError(f"Team stats for '{name}' not found. Available teams: {list(self._stats_by_abbrev.keys())}")
    
    def get_team_stats(self, abbreviation):
        """
        Get offensive stats for a team by its abbreviation.
        
        Parameters
        ----------
        abbreviation : str
            The team abbreviation (e.g., 'PHI', 'BUF', 'DET')
        
        Returns
        -------
        dict
            Team offensive stats dictionary
        
        Examples
        --------
        >>> team_stats = TeamStats(2024)
        >>> lions_stats = team_stats.get_team_stats('DET')
        >>> print(lions_stats['PF'])  # Points For
        """
        abbrev = abbreviation.upper()
        if abbrev in self._stats_by_abbrev:
            return self._stats_by_abbrev[abbrev]
        raise KeyError(f"Team stats for '{abbreviation}' not found. Available teams: {list(self._stats_by_abbrev.keys())}")
    
    def list_abbreviations(self):
        """
        Get a list of all team abbreviations with stats.
        
        Returns
        -------
        list
            List of team abbreviations
        """
        return list(self._stats_by_abbrev.keys())
    
    def to_dataframe(self):
        """
        Convert team stats data to a pandas DataFrame.
        
        Returns
        -------
        pandas.DataFrame
            DataFrame containing all team offensive stats
        """
        if not self.team_stats_dict:
            return pd.DataFrame()
        
        return pd.DataFrame(self.team_stats_dict)
    
    def to_csv(self, filename=None, **kwargs):
        """
        Export team offensive stats data to a CSV file.
        
        Parameters
        ----------
        filename : str, optional
            Explicit filename to use. If not provided, auto-generates based on season
        **kwargs
            Additional arguments passed to export_dataframe_to_csv
        
        Returns
        -------
        str
            The filename of the exported CSV file
        
        Examples
        --------
        >>> team_stats = TeamStats(2024)
        >>> 
        >>> # Export with auto-generated filename
        >>> filename = team_stats.to_csv()
        >>> 
        >>> # Export with custom filename
        >>> filename = team_stats.to_csv(filename="nfl_team_offense_2024.csv")
        >>> 
        >>> # Export to specific directory
        >>> filename = team_stats.to_csv(base_dir="/path/to/custom/dir")
        """
        df = self.to_dataframe()
        
        if df.empty:
            raise ValueError("No team stats data available to export")
        
        # If filename is provided, handle it directly
        if filename:
            import os
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            df.to_csv(filename, index=False)
            print(f"Team stats DataFrame exported to '{filename}'")
            return filename
        
        # Otherwise, use auto-generation
        export_params = {
            'sport': 'nfl',
            'data_type': 'team_offense',
            'season': self.year,
            'include_index': False,
            'create_dirs': True
        }
        
        # Override with any user-provided parameters
        export_params.update(kwargs)
        
        return export_dataframe_to_csv(df, **export_params)
    
    def get_top_teams(self, stat_column, top_n=10, ascending=False):
        """
        Get the top N teams for a specific offensive statistic.
        
        Parameters
        ----------
        stat_column : str
            The column name to rank by (e.g., 'PF', 'Yds', 'Pass Yds')
        top_n : int, optional
            Number of top teams to return (default: 10)
        ascending : bool, optional
            Sort in ascending order (default: False for descending)
        
        Returns
        -------
        pandas.DataFrame
            DataFrame with top N teams for the specified stat
        
        Examples
        --------
        >>> team_stats = TeamStats(2024)
        >>> top_scorers = team_stats.get_top_teams('PF', top_n=5)
        >>> print(top_scorers[['Tm', 'PF']])
        """
        df = self.to_dataframe()
        
        if df.empty:
            return pd.DataFrame()
        
        if stat_column not in df.columns:
            available_cols = list(df.columns)
            raise ValueError(f"Column '{stat_column}' not found. Available columns: {available_cols}")
        
        # Convert to numeric if possible
        if df[stat_column].dtype == 'object':
            df[stat_column] = pd.to_numeric(df[stat_column], errors='coerce')
        
        # Sort and return top N
        return df.nlargest(top_n, stat_column) if not ascending else df.nsmallest(top_n, stat_column)
    
    def __str__(self):
        if not self.team_stats_dict:
            return f"No team offensive stats found for {self.year}"
        
        result = f"NFL Team Offensive Stats for {self.year}:\n"
        result += "=" * 80 + "\n"
        
        # Get dataframe for easier processing
        df = self.to_dataframe()
        
        if not df.empty:
            # Show top 5 in points scored
            result += "\nTop 5 Teams by Points Scored:\n"
            result += "-" * 40 + "\n"
            
            if 'PF' in df.columns and 'Tm' in df.columns:
                # Convert PF to numeric
                df_copy = df.copy()
                df_copy['PF'] = pd.to_numeric(df_copy['PF'], errors='coerce')
                top_scorers = df_copy.nlargest(5, 'PF')
                
                for i, (_, row) in enumerate(top_scorers.iterrows(), 1):
                    team_name = row.get('Tm', 'Unknown')
                    points = row.get('PF', 'N/A')
                    total_yards = row.get('Yds', 'N/A')
                    result += f"{i}. {team_name:<25} {points:>3} points ({total_yards:>4} yards)\n"
        
        return result
