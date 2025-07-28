"""
Data models for sports reference data using Pydantic for validation and type safety.

This module contains data models that correspond to the structure of data
from sports reference websites, with field names mapped to the actual
mouse-over descriptions (data-tip attributes) from the websites.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum


class NFLConference(str, Enum):
    """NFL Conference enumeration."""
    AFC = "AFC"
    NFC = "NFC"


class NFLTeamData(BaseModel):
    """
    NFL Team data model based on pro-football-reference.com team standings table.
    
    Field names correspond to the mouse-over descriptions (data-tip attributes)
    from the website for accurate mapping and better readability.
    """
    
    model_config = ConfigDict(
        populate_by_name=True,  # Enables using field aliases for model creation
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore'  # Allow extra fields that we might not have modeled yet
    )
    
    # Core team identification
    team: str = Field(
        ..., 
        description="Team name",
        alias="Team"
    )
    
    abbrev: str = Field(
        ..., 
        description="Team abbreviation (3-letter code)",
        alias="Abbrev",
        min_length=2,
        max_length=4
    )
    
    conference: NFLConference = Field(
        ..., 
        description="Conference (AFC or NFC)",
        alias="Conference"
    )
    
    # Win-Loss Record
    wins: int = Field(
        ..., 
        description="Games Won",
        alias="Wins",
        ge=0,
        le=17
    )
    
    losses: int = Field(
        ..., 
        description="Games Lost", 
        alias="Losses",
        ge=0,
        le=17
    )
    
    win_loss_percentage: float = Field(
        ...,
        description="Win-Loss Percentage of team. After 1972, ties are counted as half-wins and half-losses.",
        alias="Win-Loss Percentage",
        ge=0.0,
        le=1.0
    )
    
    # Scoring Statistics
    points_for: int = Field(
        ...,
        description="Points Scored by team",
        alias="Points For",
        ge=0
    )
    
    points_allowed: int = Field(
        ...,
        description="Points Scored by opposition",
        alias="Points Allowed", 
        ge=0
    )
    
    points_differential: int = Field(
        ...,
        description="Points Differential (Points Scored - Points Allowed)",
        alias="Points Differential"
    )
    
    margin_of_victory: float = Field(
        ...,
        description="Margin of Victory: (Points Scored - Points Allowed) / Games Played",
        alias="Margin of Victory"
    )
    
    # Advanced Metrics
    strength_of_schedule: float = Field(
        ...,
        description="Strength of Schedule: Average quality of opponent as measured by SRS (Simple Rating System)",
        alias="Strength of Schedule"
    )
    
    simple_rating_system: float = Field(
        ...,
        description="Simple Rating System: Team quality relative to average (0.0). SRS = MoV + SoS = OSRS + DSRS. The difference in SRS can be considered a point spread (add about 2 pt for HFA)",
        alias="Simple Rating System"
    )
    
    offensive_srs: float = Field(
        ...,
        description="Offensive SRS: Team offense quality relative to average (0.0) as measured by SRS",
        alias="Offensive SRS"
    )
    
    defensive_srs: float = Field(
        ...,
        description="Defensive SRS: Team defense quality relative to average (0.0) as measured by SRS", 
        alias="Defensive SRS"
    )
    
    @validator('points_differential')
    def validate_points_differential(cls, v, values):
        """Validate that points differential matches PF - PA."""
        if 'points_for' in values and 'points_allowed' in values:
            expected = values['points_for'] - values['points_allowed']
            if abs(v - expected) > 1:  # Allow for rounding differences
                raise ValueError(f"Points differential {v} doesn't match PF({values['points_for']}) - PA({values['points_allowed']}) = {expected}")
        return v
    
    @validator('team')
    def clean_team_name(cls, v):
        """Clean team name by removing asterisks and plus signs."""
        return v.replace('*', '').replace('+', '').strip()
    
    @validator('win_loss_percentage')
    def validate_win_loss_percentage(cls, v, values):
        """Validate that win-loss percentage is approximately correct."""
        if 'wins' in values and 'losses' in values:
            total_games = values['wins'] + values['losses']
            if total_games > 0:
                expected = values['wins'] / total_games
                if abs(v - expected) > 0.01:  # Allow for rounding/ties
                    raise ValueError(f"Win-loss percentage {v} doesn't match wins/total: {expected}")
        return v


class NFLColumnMapping:
    """
    Mapping between website column headers and our Pydantic model fields.
    
    This class provides utilities to map between the raw data from the website
    and our structured Pydantic models.
    """
    
    # Mapping from website column names to model field names
    WEBSITE_TO_MODEL = {
        'Tm': 'team',
        'Team': 'team', 
        'W': 'wins',
        'Wins': 'wins',
        'L': 'losses', 
        'Losses': 'losses',
        'W-L%': 'win_loss_percentage',
        'Win-Loss Percentage': 'win_loss_percentage',
        'PF': 'points_for',
        'Points For': 'points_for',
        'PA': 'points_allowed',
        'Points Allowed': 'points_allowed',
        'PD': 'points_differential',
        'Points Differential': 'points_differential',
        'MoV': 'margin_of_victory',
        'Margin of Victory': 'margin_of_victory',
        'SoS': 'strength_of_schedule',
        'Strength of Schedule': 'strength_of_schedule',
        'SRS': 'simple_rating_system',
        'Simple Rating System': 'simple_rating_system',
        'OSRS': 'offensive_srs',
        'Offensive SRS': 'offensive_srs',
        'DSRS': 'defensive_srs',
        'Defensive SRS': 'defensive_srs',
        'Abbrev': 'abbrev',
        'Conference': 'conference'
    }
    
    # Reverse mapping for converting back
    MODEL_TO_WEBSITE = {v: k for k, v in WEBSITE_TO_MODEL.items()}
    
    # Preferred column names (descriptive versions)
    PREFERRED_COLUMNS = {
        'team': 'Team',
        'wins': 'Wins',
        'losses': 'Losses', 
        'win_loss_percentage': 'Win-Loss Percentage',
        'points_for': 'Points For',
        'points_allowed': 'Points Allowed',
        'points_differential': 'Points Differential',
        'margin_of_victory': 'Margin of Victory',
        'strength_of_schedule': 'Strength of Schedule',
        'simple_rating_system': 'Simple Rating System',
        'offensive_srs': 'Offensive SRS',
        'defensive_srs': 'Defensive SRS',
        'abbrev': 'Abbrev',
        'conference': 'Conference'
    }
    
    @classmethod
    def map_raw_data_to_model(cls, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map raw scraped data to model field names.
        
        Parameters
        ----------
        raw_data : dict
            Raw data dictionary from website scraping
            
        Returns
        -------
        dict
            Data dictionary with model field names
        """
        mapped_data = {}
        for key, value in raw_data.items():
            model_field = cls.WEBSITE_TO_MODEL.get(key, key.lower().replace(' ', '_'))
            mapped_data[model_field] = value
        return mapped_data
    
    @classmethod
    def get_preferred_column_names(cls) -> List[str]:
        """
        Get list of preferred (descriptive) column names in order.
        
        Returns
        -------
        list
            List of descriptive column names
        """
        return list(cls.PREFERRED_COLUMNS.values())
    
    @classmethod
    def map_to_preferred_columns(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map model field names to preferred descriptive column names.
        
        Parameters
        ----------
        data : dict
            Data with model field names
            
        Returns
        -------
        dict
            Data with descriptive column names
        """
        mapped_data = {}
        for key, value in data.items():
            preferred_name = cls.PREFERRED_COLUMNS.get(key, key)
            mapped_data[preferred_name] = value
        return mapped_data


# Example usage and validation functions for teams
def create_nfl_team_from_raw_data(raw_data: Dict[str, Any]) -> NFLTeamData:
    """
    Create an NFLTeamData instance from raw scraped data.
    
    Parameters
    ----------
    raw_data : dict
        Raw data dictionary from website scraping
        
    Returns
    -------
    NFLTeamData
        Validated team data model
        
    Raises
    ------
    ValidationError
        If data doesn't meet model requirements
    """
    mapped_data = NFLColumnMapping.map_raw_data_to_model(raw_data)
    return NFLTeamData(**mapped_data)


def convert_nfl_teams_to_models(teams_data: List[Dict[str, Any]]) -> List[NFLTeamData]:
    """
    Convert a list of raw team data to validated NFLTeamData models.
    
    Parameters
    ----------
    teams_data : list
        List of raw team data dictionaries
        
    Returns
    -------
    list
        List of validated NFLTeamData instances
    """
    models = []
    for team_data in teams_data:
        try:
            model = create_nfl_team_from_raw_data(team_data)
            models.append(model)
        except Exception as e:
            print(f"Warning: Failed to create model for team data: {e}")
            # Could log the error or handle it differently
    return models


# Game result enumeration for NFL games
class NFLGameResult(str, Enum):
    """NFL Game Result enumeration."""
    WIN = "W"
    LOSS = "L"
    TIE = "T"


class NFLGameLogData(BaseModel):
    """
    NFL Game Log data model based on pro-football-reference.com team game log table.
    
    Field names correspond to the game log structure from team schedule pages.
    """
    
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore'
    )
    
    # Core game identification
    week: Optional[str] = Field(
        None,
        description="Week number or playoff identifier",
        alias="Week"
    )
    
    game: Optional[str] = Field(
        None,
        description="Game number in season",
        alias="Game"
    )
    
    date: Optional[str] = Field(
        None,
        description="Game date",
        alias="Date"
    )
    
    day: Optional[str] = Field(
        None,
        description="Day of week",
        alias="Day"
    )
    
    location: Optional[str] = Field(
        None,
        description="Home/Away indicator (@ for away games)",
        alias="Location"
    )
    
    opponent: Optional[str] = Field(
        None,
        description="Opponent team abbreviation",
        alias="Opponent"
    )
    
    result: Optional[NFLGameResult] = Field(
        None,
        description="Game result (W/L/T)",
        alias="Result"
    )
    
    team_score: Optional[int] = Field(
        None,
        description="Team's score",
        alias="Team_Score",
        ge=0
    )
    
    opp_score: Optional[int] = Field(
        None,
        description="Opponent's score", 
        alias="Opp_Score",
        ge=0
    )
    
    # Passing statistics
    pass_cmp: Optional[int] = Field(
        None,
        description="Pass completions",
        alias="Pass_Cmp",
        ge=0
    )
    
    pass_att: Optional[int] = Field(
        None,
        description="Pass attempts",
        alias="Pass_Att",
        ge=0
    )
    
    pass_cmp_pct: Optional[float] = Field(
        None,
        description="Pass completion percentage",
        alias="Pass_Cmp_Pct",
        ge=0.0,
        le=100.0
    )
    
    pass_yds: Optional[int] = Field(
        None,
        description="Passing yards",
        alias="Pass_Yds"
    )
    
    pass_td: Optional[int] = Field(
        None,
        description="Passing touchdowns",
        alias="Pass_TD",
        ge=0
    )
    
    pass_rate: Optional[float] = Field(
        None,
        description="Passer rating",
        alias="Pass_Rate",
        ge=0.0
    )
    
    pass_sk: Optional[int] = Field(
        None,
        description="Times sacked",
        alias="Pass_Sk",
        ge=0
    )
    
    pass_sk_yds: Optional[int] = Field(
        None,
        description="Sack yards lost",
        alias="Pass_Sk_Yds",
        ge=0
    )
    
    # Rushing statistics
    rush_att: Optional[int] = Field(
        None,
        description="Rushing attempts",
        alias="Rush_Att",
        ge=0
    )
    
    rush_yds: Optional[int] = Field(
        None,
        description="Rushing yards",
        alias="Rush_Yds"
    )
    
    rush_td: Optional[int] = Field(
        None,
        description="Rushing touchdowns", 
        alias="Rush_TD",
        ge=0
    )
    
    rush_ypc: Optional[float] = Field(
        None,
        description="Yards per carry",
        alias="Rush_YPC"
    )
    
    # Total offense
    tot_plays: Optional[int] = Field(
        None,
        description="Total offensive plays",
        alias="Tot_Plays",
        ge=0
    )
    
    tot_yds: Optional[int] = Field(
        None,
        description="Total yards",
        alias="Tot_Yds"
    )
    
    tot_ypp: Optional[float] = Field(
        None,
        description="Yards per play",
        alias="Tot_YPP"
    )
    
    # Turnovers
    to_fumble: Optional[int] = Field(
        None,
        description="Fumbles lost",
        alias="TO_Fumble",
        ge=0
    )
    
    to_int: Optional[int] = Field(
        None,
        description="Interceptions thrown",
        alias="TO_Int",
        ge=0
    )
    
    # Penalties
    penalty_count: Optional[int] = Field(
        None,
        description="Number of penalties",
        alias="Penalty_Count",
        ge=0
    )
    
    penalty_yds: Optional[int] = Field(
        None,
        description="Penalty yards",
        alias="Penalty_Yds",
        ge=0
    )
    
    # Down conversions
    third_down_success: Optional[int] = Field(
        None,
        description="Third down conversions",
        alias="Third_Down_Success",
        ge=0
    )
    
    third_down_att: Optional[int] = Field(
        None,
        description="Third down attempts",
        alias="Third_Down_Att",
        ge=0
    )
    
    fourth_down_success: Optional[int] = Field(
        None,
        description="Fourth down conversions",
        alias="Fourth_Down_Success",
        ge=0
    )
    
    fourth_down_att: Optional[int] = Field(
        None,
        description="Fourth down attempts",
        alias="Fourth_Down_Att",
        ge=0
    )
    
    # Game control
    time_of_possession: Optional[str] = Field(
        None,
        description="Time of possession (MM:SS format)",
        alias="Time_of_Possession"
    )
    
    # Team and season context
    team: Optional[str] = Field(
        None,
        description="Team abbreviation",
        alias="Team"
    )
    
    season: Optional[str] = Field(
        None,
        description="Season year",
        alias="Season"
    )
    
    @validator('team_score', 'opp_score', pre=True)
    def parse_score(cls, v):
        """Parse score values, handling empty strings."""
        if v == '' or v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None
    
    @validator('pass_cmp_pct', 'pass_rate', 'rush_ypc', 'tot_ypp', pre=True)
    def parse_float(cls, v):
        """Parse float values, handling empty strings."""
        if v == '' or v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None
    
    @validator('pass_cmp', 'pass_att', 'pass_td', 'pass_sk', 'pass_sk_yds', 
              'rush_att', 'rush_td', 'tot_plays', 'to_fumble', 'to_int',
              'penalty_count', 'penalty_yds', 'third_down_success', 'third_down_att',
              'fourth_down_success', 'fourth_down_att', pre=True)
    def parse_int(cls, v):
        """Parse integer values, handling empty strings."""
        if v == '' or v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None
    
    @validator('pass_yds', 'rush_yds', 'tot_yds', pre=True)
    def parse_yards(cls, v):
        """Parse yard values, which can be negative."""
        if v == '' or v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None


class NFLGameLogColumnMapping:
    """
    Column mapping for NFL Game Log data to standardize field names.
    """
    
    # Common variations of column names found on the website
    WEBSITE_TO_MODEL = {
        'Wk': 'Week',
        'G#': 'Game', 
        'Game_Number': 'Game',
        'Date': 'Date',
        'Day': 'Day',
        '@': 'Location',
        'Opp': 'Opponent',
        'Opponent': 'Opponent',
        'Result': 'Result',
        'Tm': 'Team_Score',
        'Team_Score': 'Team_Score',
        'Team_Points': 'Team_Score',
        'Opponent_Score': 'Opp_Score',
        'Opp_Score': 'Opp_Score',
        'Cmp': 'Pass_Cmp',
        'Pass_Completions': 'Pass_Cmp',
        'Att': 'Pass_Att', 
        'Pass_Attempts': 'Pass_Att',
        'Cmp%': 'Pass_Cmp_Pct',
        'Pass_Completion_Pct': 'Pass_Cmp_Pct',
        'Yds': 'Pass_Yds',
        'Pass_Yards': 'Pass_Yds',
        'TD': 'Pass_TD',
        'Pass_Touchdowns': 'Pass_TD',
        'Rate': 'Pass_Rate',
        'Passer_Rating': 'Pass_Rate',
        'Sk': 'Pass_Sk',
        'Times_Sacked': 'Pass_Sk',
        'Yds_Lost_Sacks': 'Pass_Sk_Yds',
        'Rush_Attempts': 'Rush_Att',
        'Rush_Yards': 'Rush_Yds',
        'Rush_Touchdowns': 'Rush_TD',
        'Y/A': 'Rush_YPC',
        'Yards_Per_Carry': 'Rush_YPC',
        'Plays': 'Tot_Plays',
        'Total_Plays': 'Tot_Plays',
        'Total_Yards': 'Tot_Yds',
        'Y/P': 'Tot_YPP',
        'Yards_Per_Play': 'Tot_YPP',
        'Fumbles_Lost': 'TO_Fumble',
        'FL': 'TO_Fumble',
        'Interceptions': 'TO_Int',
        'Int': 'TO_Int',
        'Penalties': 'Penalty_Count',
        'Penalty_Yards': 'Penalty_Yds',
        '3DConv': 'Third_Down_Success',
        'Third_Down_Conversions': 'Third_Down_Success',
        '3DAtt': 'Third_Down_Att',
        'Third_Down_Attempts': 'Third_Down_Att',
        '4DConv': 'Fourth_Down_Success',
        'Fourth_Down_Conversions': 'Fourth_Down_Success',
        '4DAtt': 'Fourth_Down_Att',
        'Fourth_Down_Attempts': 'Fourth_Down_Att',
        'ToP': 'Time_of_Possession',
        'Time_of_Possession': 'Time_of_Possession'
    }
    
    @classmethod
    def map_raw_data_to_model(cls, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map raw scraped data to model field names.
        
        Parameters
        ----------
        raw_data : dict
            Raw data dictionary from website scraping
            
        Returns
        -------
        dict
            Mapped data dictionary with model field names
        """
        mapped_data = {}
        
        for key, value in raw_data.items():
            # Use mapping if available, otherwise keep original key
            model_key = cls.WEBSITE_TO_MODEL.get(key, key)
            mapped_data[model_key] = value
        
        return mapped_data


def create_nfl_gamelog_from_raw_data(raw_data: Dict[str, Any]) -> NFLGameLogData:
    """
    Create an NFLGameLogData instance from raw scraped data.
    
    Parameters
    ----------
    raw_data : dict
        Raw data dictionary from website scraping
        
    Returns
    -------
    NFLGameLogData
        Validated game log data model
        
    Raises
    ------
    ValidationError
        If data doesn't meet model requirements
    """
    mapped_data = NFLGameLogColumnMapping.map_raw_data_to_model(raw_data)
    return NFLGameLogData(**mapped_data)


def convert_nfl_gamelog_to_models(games_data: List[Dict[str, Any]]) -> List[NFLGameLogData]:
    """
    Convert a list of raw game log data to validated NFLGameLogData models.
    
    Parameters
    ----------
    games_data : list
        List of raw game log data dictionaries
        
    Returns
    -------
    list
        List of validated NFLGameLogData instances
    """
    models = []
    for game_data in games_data:
        try:
            model = create_nfl_gamelog_from_raw_data(game_data)
            models.append(model)
        except Exception as e:
            print(f"Warning: Failed to create model for game data: {e}")
            # Could log the error or handle it differently
    return models
