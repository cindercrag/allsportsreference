import pandas as pd
from .nfl_modules import _retrieve_all_teams
from ..utils.common import export_dataframe_to_csv
from .models import NFLTeamData, NFLColumnMapping, convert_nfl_teams_to_models



class Teams:
    """
    Class to handle NFL teams data for a given season.
    
    This class is responsible for parsing and storing team data, including
    team names, abbreviations, and various statistics. It provides methods
    to retrieve all teams for a specified year and to parse team data from
    HTML content.

    A year and an optional season page can be specified to pull data
    for that specific season. The `team_data_dict` attribute will contain
    all teams' data, where each key is the team's abbreviation and the value
    is a dictionary with the team's data and its rank in the league.
    """

    def __init__(self, year):
        self.year = year
        self.team_data_dict = _retrieve_all_teams(year)
        
        # Create a lookup dictionary by abbreviation for easy access
        self._teams_by_abbrev = {}
        if self.team_data_dict:
            for team in self.team_data_dict:
                abbrev = team.get('Abbrev')
                if abbrev:
                    self._teams_by_abbrev[abbrev] = team
    
    def __getattr__(self, name):
        """
        Allow access to teams by abbreviation like teams.PHI
        """
        # Convert to uppercase to handle both teams.phi and teams.PHI
        abbrev = name.upper()
        if abbrev in self._teams_by_abbrev:
            return self._teams_by_abbrev[abbrev]
        raise AttributeError(f"Team '{name}' not found. Available teams: {list(self._teams_by_abbrev.keys())}")
    
    def get_team(self, abbreviation):
        """
        Get a team by its abbreviation.
        
        Parameters
        ----------
        abbreviation : str
            The team abbreviation (e.g., 'PHI', 'BUF', 'NWE')
        
        Returns
        -------
        dict
            Team data dictionary
        
        Examples
        --------
        >>> teams = Teams(2024)
        >>> eagles = teams.get_team('PHI')
        >>> print(eagles['Tm'])  # Philadelphia Eagles
        """
        abbrev = abbreviation.upper()
        if abbrev in self._teams_by_abbrev:
            return self._teams_by_abbrev[abbrev]
        raise KeyError(f"Team '{abbreviation}' not found. Available teams: {list(self._teams_by_abbrev.keys())}")
    
    def list_abbreviations(self):
        """
        Get a list of all team abbreviations.
        
        Returns
        -------
        list
            List of team abbreviations
        """
        return list(self._teams_by_abbrev.keys())
    
    def get_teams_by_conference(self, conference):
        """
        Get all teams in a specific conference.
        
        Parameters
        ----------
        conference : str
            Conference name ('AFC' or 'NFC')
        
        Returns
        -------
        list
            List of team dictionaries in the specified conference
        """
        return [team for team in self.team_data_dict if team.get('Conference', '').upper() == conference.upper()]
    
    def to_dataframe(self):
        """
        Convert teams data to a pandas DataFrame.
        
        Returns
        -------
        pandas.DataFrame
            DataFrame containing all team data
        """
        if not self.team_data_dict:
            return pd.DataFrame()
        
        return pd.DataFrame(self.team_data_dict)
    
    def to_models(self):
        """
        Convert teams data to a list of validated Pydantic models.
        
        Returns
        -------
        list
            List of NFLTeamData Pydantic models
            
        Examples
        --------
        >>> teams = Teams(2024)
        >>> models = teams.to_models()
        >>> eagles = next(m for m in models if m.abbrev == 'PHI')
        >>> print(eagles.team)  # Philadelphia Eagles
        >>> print(eagles.wins)  # 14
        """
        if not self.team_data_dict:
            return []
        
        return convert_nfl_teams_to_models(self.team_data_dict)
    
    def get_model_by_abbrev(self, abbrev):
        """
        Get a specific team as a Pydantic model by abbreviation.
        
        Parameters
        ----------
        abbrev : str
            Team abbreviation (e.g., 'PHI', 'BUF')
            
        Returns
        -------
        NFLTeamData
            Validated team data model
            
        Examples
        --------
        >>> teams = Teams(2024)
        >>> eagles = teams.get_model_by_abbrev('PHI')
        >>> print(f"{eagles.team}: {eagles.wins}-{eagles.losses}")
        """
        team_dict = self.get_team(abbrev)
        from .models import create_nfl_team_from_raw_data
        return create_nfl_team_from_raw_data(team_dict)
    
    def to_csv(self, filename=None, **kwargs):
        """
        Export teams data to a CSV file.
        
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
        >>> teams = Teams(2024)
        >>> 
        >>> # Export with auto-generated filename
        >>> filename = teams.to_csv()
        >>> 
        >>> # Export with custom filename
        >>> filename = teams.to_csv(filename="nfl_teams_2024.csv")
        >>> 
        >>> # Export to specific directory
        >>> filename = teams.to_csv(base_dir="/path/to/custom/dir")
        """
        df = self.to_dataframe()
        
        if df.empty:
            raise ValueError("No team data available to export")
        
        # If filename is provided, handle it directly
        if filename:
            import os
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            df.to_csv(filename, index=False)
            print(f"DataFrame exported to '{filename}'")
            return filename
        
        # Otherwise, use auto-generation
        export_params = {
            'sport': 'nfl',
            'data_type': 'teams',
            'season': self.year,
            'include_index': False,
            'create_dirs': True
        }
        
        # Override with any user-provided parameters
        export_params.update(kwargs)
        
        return export_dataframe_to_csv(df, **export_params)
    
    def export_by_conference(self, base_dir=None):
        """
        Export separate CSV files for AFC and NFC teams.
        
        Parameters
        ----------
        base_dir : str, optional
            Base directory for exports (uses config.data_dir if None)
        
        Returns
        -------
        dict
            Dictionary with 'AFC' and 'NFC' keys containing the exported filenames
        
        Examples
        --------
        >>> teams = Teams(2024)
        >>> filenames = teams.export_by_conference()
        >>> print(f"AFC teams: {filenames['AFC']}")
        >>> print(f"NFC teams: {filenames['NFC']}")
        """
        filenames = {}
        
        for conference in ['AFC', 'NFC']:
            conference_teams = self.get_teams_by_conference(conference)
            if conference_teams:
                df = pd.DataFrame(conference_teams)
                filename = export_dataframe_to_csv(
                    df,
                    sport='nfl',
                    data_type=f'teams_{conference.lower()}',
                    season=self.year,
                    include_index=False,
                    create_dirs=True,
                    base_dir=base_dir
                )
                filenames[conference] = filename
        
        return filenames
        
    def __str__(self):
        if not self.team_data_dict:
            return f"No teams found for {self.year}"
        
        result = f"NFL Teams for {self.year}:\n"
        result += "=" * 80 + "\n"
        
        for i, team in enumerate(self.team_data_dict, 1):
            # Extract team name and other info with descriptive column names
            team_name = team.get('Team', team.get('Tm', 'Unknown'))
            abbrev = team.get('Abbrev', 'N/A')
            wins = team.get('Wins', team.get('W', 'N/A'))
            losses = team.get('Losses', team.get('L', 'N/A'))
            pf = team.get('Points For', team.get('PF', 'N/A'))
            pa = team.get('Points Allowed', team.get('PA', 'N/A'))
            conference = team.get('Conference', '')
            
            # Clean up team name (remove asterisks and plus signs)
            clean_name = team_name.replace('*', '').replace('+', '')
            
            result += f"{i:2d}. {clean_name:<25} ({abbrev}) {wins:>2}-{losses:<2} (PF: {pf:>3}, PA: {pa:>3}) [{conference}]\n"
            
        return result

    def _retrieve_team_data(self, year, team_name, season_page):
        """
        Pull all stats for a specific team.

        By first retrieving a dictionary containing all information for all
        teams in the league, only select the desired team for a specific year
        and return only their relevant results.

        Parameters
        ----------
        year : string
            A ``string`` of the requested year to pull stats from.
        team_name : string
            A ``string`` of the team's 3-letter abbreviation, such as 'DET' for
            the Detroit Red Wings.
        season_page : string (optional)
            Optionally specify the filename of a local file to use to pull data
            instead of downloading from sports-reference.com. This file should
            be of the Season page for the designated year.
        """
        # teams_list, year = _retrieve_all_teams(year, season_page)
        # self._year = year
        # # Teams are listed in terms of rank with the first team being #1
        # rank = 1
        # for team_data in teams_list:
        #     name = utils._parse_field(PARSING_SCHEME,
        #                                 team_data,
        #                                 'abbreviation')
        #     if name == team_name:
        #         self._rank = rank
        #         return team_data
        #     rank += 1


