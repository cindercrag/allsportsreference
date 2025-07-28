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


# Example usage and validation functions
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
