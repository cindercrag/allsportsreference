import pandas as pd
from .nfl_modules import _retrieve_all_teams



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
        
    def __str__(self):
        if not self.team_data_dict:
            return f"No teams found for {self.year}"
        
        result = f"NFL Teams for {self.year}:\n"
        result += "=" * 80 + "\n"
        
        for i, team in enumerate(self.team_data_dict, 1):
            # Extract team name and other info if available
            team_name = team.get('Tm', 'Unknown')
            abbrev = team.get('Abbrev', 'N/A')
            wins = team.get('W', 'N/A')
            losses = team.get('L', 'N/A')
            pf = team.get('PF', 'N/A')  # Points For
            pa = team.get('PA', 'N/A')  # Points Against
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


