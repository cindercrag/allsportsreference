import pandas as pd






class Teams:
    """
    Class to handle NFL team data for a given season.
    
    This class is responsible for parsing and storing team data, including
    team names, abbreviations, and various statistics. It provides methods
    to retrieve all teams for a specified year and to parse team data from
    HTML content.
    """

    def __init__(self, year, season_page=None):
        self.year = year
        self.season_page = season_page
        self.team_data_dict = self._retrieve_all_teams(year, season_page)


