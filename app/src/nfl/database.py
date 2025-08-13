"""
Database utilities for creating and managing PostgreSQL tables from Pydantic models.

This module provides functionality to:
1. Generate SQL DDL from Pydantic models
2. Create tables in PostgreSQL
3. Insert data from Pydantic models
4. Query data and convert back to Pydantic models
"""

import logging
from typing import List, Dict, Any, Optional, Type
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from enum import Enum
import os

from .models import NFLTeamData, NFLConference, NFLGameLogData

logger = logging.getLogger(__name__)


class PostgreSQLManager:
    """
    Manager class for PostgreSQL operations with Pydantic models.
    """
    
    def __init__(self, connection_params: Optional[Dict[str, str]] = None):
        """
        Initialize PostgreSQL manager.
        
        Parameters
        ----------
        connection_params : dict, optional
            Database connection parameters. If None, uses environment variables.
        """
        if connection_params is None:
            connection_params = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'sportsdb'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', '')
            }
        
        self.connection_params = connection_params
        self._connection = None
    
    def connect(self):
        """Establish database connection."""
        try:
            self._connection = psycopg2.connect(**self.connection_params)
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Disconnected from PostgreSQL database")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def execute_sql(self, sql: str, params: Optional[tuple] = None) -> None:
        """
        Execute SQL statement.
        
        Parameters
        ----------
        sql : str
            SQL statement to execute
        params : tuple, optional
            Parameters for the SQL statement
        """
        if not self._connection:
            self.connect()
        
        cursor = self._connection.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            self._connection.commit()
        finally:
            cursor.close()
    
    def fetch_all(self, sql: str, params: Optional[tuple] = None) -> List[tuple]:
        """
        Fetch all results from a SELECT query.
        
        Parameters
        ----------
        sql : str
            SQL SELECT statement
        params : tuple, optional
            Parameters for the SQL statement
            
        Returns
        -------
        List[tuple]
            List of result tuples
        """
        if not self._connection:
            self.connect()
        
        cursor = self._connection.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()
    
    def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[tuple]:
        """
        Fetch one result from a SELECT query.
        
        Parameters
        ----------
        sql : str
            SQL SELECT statement
        params : tuple, optional
            Parameters for the SQL statement
            
        Returns
        -------
        tuple or None
            Single result tuple or None
        """
        if not self._connection:
            self.connect()
        
        cursor = self._connection.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchone()
        finally:
            cursor.close()
    
    @staticmethod
    def pydantic_to_sql_type(field_info, field_name: str) -> str:
        """
        Convert Pydantic field type to PostgreSQL SQL type.
        
        Parameters
        ----------
        field_info : FieldInfo
            Pydantic field information
        field_name : str
            Name of the field
            
        Returns
        -------
        str
            PostgreSQL SQL type
        """
        field_type = field_info.annotation
        
        # Handle Optional types
        if hasattr(field_type, '__origin__') and field_type.__origin__ is type(Optional[int].__origin__):
            field_type = field_type.__args__[0]
        
        # Map Python types to PostgreSQL types
        if field_type == str:
            # Check for constraints
            if hasattr(field_info, 'constraints'):
                max_length = getattr(field_info, 'max_length', None)
                if max_length:
                    return f"VARCHAR({max_length})"
            return "TEXT"
        elif field_type == int:
            return "INTEGER"
        elif field_type == float:
            return "DECIMAL(10,3)"  # Good precision for sports stats
        elif field_type == bool:
            return "BOOLEAN"
        elif issubclass(field_type, Enum):
            # For enum types, create a constraint
            enum_values = [f"'{value.value}'" for value in field_type]
            return f"VARCHAR(10) CHECK ({field_name} IN ({', '.join(enum_values)}))"
        else:
            # Default fallback
            return "TEXT"
    
    @staticmethod
    def generate_create_table_sql(model_class: Type[BaseModel], table_name: str, 
                                  schema: str = "public") -> str:
        """
        Generate CREATE TABLE SQL from Pydantic model.
        
        Parameters
        ----------
        model_class : Type[BaseModel]
            Pydantic model class
        table_name : str
            Name of the table to create
        schema : str
            Database schema name
            
        Returns
        -------
        str
            SQL CREATE TABLE statement
        """
        fields = []
        
        # Add ID field as primary key
        fields.append("id SERIAL PRIMARY KEY")
        
        # Process model fields
        for field_name, field_info in model_class.model_fields.items():
            sql_type = PostgreSQLManager.pydantic_to_sql_type(field_info, field_name)
            
            # Add NOT NULL constraint for required fields
            not_null = "NOT NULL" if field_info.is_required() else ""
            
            field_sql = f"{field_name} {sql_type} {not_null}".strip()
            fields.append(field_sql)
        
        # Add metadata fields
        fields.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        fields.append("updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        fields_sql = ",\n    ".join(fields)
        
        sql = f"""
CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
    {fields_sql}
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_{table_name}_abbrev ON {schema}.{table_name}(abbrev);
CREATE INDEX IF NOT EXISTS idx_{table_name}_conference ON {schema}.{table_name}(conference);
CREATE INDEX IF NOT EXISTS idx_{table_name}_wins ON {schema}.{table_name}(wins);

-- Create update trigger
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_{table_name}_modtime ON {schema}.{table_name};
CREATE TRIGGER update_{table_name}_modtime 
    BEFORE UPDATE ON {schema}.{table_name} 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
"""
        return sql
    
    def create_table_from_model(self, model_class: Type[BaseModel], table_name: str,
                                schema: str = "public", drop_if_exists: bool = False) -> bool:
        """
        Create table from Pydantic model.
        
        Parameters
        ----------
        model_class : Type[BaseModel]
            Pydantic model class
        table_name : str
            Name of the table to create
        schema : str
            Database schema name
        drop_if_exists : bool
            Whether to drop table if it exists
            
        Returns
        -------
        bool
            True if successful
        """
        if not self._connection:
            raise RuntimeError("Not connected to database")
        
        try:
            cursor = self._connection.cursor()
            
            # Drop table if requested
            if drop_if_exists:
                cursor.execute(f"DROP TABLE IF EXISTS {schema}.{table_name} CASCADE")
                logger.info(f"Dropped table {schema}.{table_name}")
            
            # Generate and execute CREATE TABLE SQL
            create_sql = self.generate_create_table_sql(model_class, table_name, schema)
            cursor.execute(create_sql)
            
            self._connection.commit()
            cursor.close()
            
            logger.info(f"Created table {schema}.{table_name} from {model_class.__name__}")
            return True
            
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Failed to create table {table_name}: {e}")
            raise
    
    def insert_models(self, models: List[BaseModel], table_name: str, 
                      schema: str = "public", on_conflict: str = "IGNORE") -> int:
        """
        Insert Pydantic models into database table.
        
        Parameters
        ----------
        models : List[BaseModel]
            List of Pydantic model instances
        table_name : str
            Name of the table
        schema : str
            Database schema name
        on_conflict : str
            How to handle conflicts ("IGNORE", "UPDATE", "ERROR")
            
        Returns
        -------
        int
            Number of rows inserted
        """
        if not models:
            return 0
        
        if not self._connection:
            raise RuntimeError("Not connected to database")
        
        try:
            cursor = self._connection.cursor()
            
            # Get field names from first model
            model_dict = models[0].model_dump()
            field_names = list(model_dict.keys())
            
            # Create INSERT SQL
            fields_sql = ", ".join(field_names)
            placeholders = ", ".join(["%s"] * len(field_names))
            
            conflict_clause = ""
            if on_conflict == "IGNORE":
                conflict_clause = "ON CONFLICT DO NOTHING"
            elif on_conflict == "UPDATE":
                update_fields = ", ".join([f"{field} = EXCLUDED.{field}" for field in field_names])
                conflict_clause = f"ON CONFLICT (abbrev) DO UPDATE SET {update_fields}"
            
            insert_sql = f"""
            INSERT INTO {schema}.{table_name} ({fields_sql})
            VALUES ({placeholders})
            {conflict_clause}
            """
            
            # Prepare data for insertion
            data_rows = []
            for model in models:
                model_dict = model.model_dump()
                row = [model_dict[field] for field in field_names]
                data_rows.append(row)
            
            # Execute batch insert
            cursor.executemany(insert_sql, data_rows)
            rows_affected = cursor.rowcount
            
            self._connection.commit()
            cursor.close()
            
            logger.info(f"Inserted {rows_affected} rows into {schema}.{table_name}")
            return rows_affected
            
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Failed to insert models into {table_name}: {e}")
            raise
    
    def query_to_models(self, model_class: Type[BaseModel], table_name: str,
                        where_clause: str = "", schema: str = "public") -> List[BaseModel]:
        """
        Query database and convert results to Pydantic models.
        
        Parameters
        ----------
        model_class : Type[BaseModel]
            Pydantic model class for conversion
        table_name : str
            Name of the table
        where_clause : str
            Optional WHERE clause (without WHERE keyword)
        schema : str
            Database schema name
            
        Returns
        -------
        List[BaseModel]
            List of Pydantic model instances
        """
        if not self._connection:
            raise RuntimeError("Not connected to database")
        
        try:
            cursor = self._connection.cursor(cursor_factory=RealDictCursor)
            
            # Build query
            query = f"SELECT * FROM {schema}.{table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            
            # Convert to Pydantic models
            models = []
            for row in rows:
                # Remove metadata fields that aren't in the model
                row_dict = dict(row)
                row_dict.pop('id', None)
                row_dict.pop('created_at', None)
                row_dict.pop('updated_at', None)
                
                try:
                    model = model_class(**row_dict)
                    models.append(model)
                except Exception as e:
                    logger.warning(f"Failed to create model from row: {e}")
            
            logger.info(f"Retrieved {len(models)} models from {schema}.{table_name}")
            return models
            
        except Exception as e:
            logger.error(f"Failed to query {table_name}: {e}")
            raise


def create_nfl_teams_table(drop_if_exists: bool = False) -> bool:
    """
    Create NFL teams table using the NFLTeamData Pydantic model.
    
    Parameters
    ----------
    drop_if_exists : bool
        Whether to drop the table if it already exists
        
    Returns
    -------
    bool
        True if successful
    """
    try:
        with PostgreSQLManager() as db:
            success = db.create_table_from_model(
                model_class=NFLTeamData,
                table_name="nfl_teams",
                schema="public",
                drop_if_exists=drop_if_exists
            )
            return success
    except Exception as e:
        logger.error(f"Failed to create NFL teams table: {e}")
        return False


def insert_nfl_teams(teams: List[NFLTeamData], on_conflict: str = "UPDATE") -> int:
    """
    Insert NFL team data into the database.
    
    Parameters
    ----------
    teams : List[NFLTeamData]
        List of NFL team Pydantic models
    on_conflict : str
        How to handle conflicts ("IGNORE", "UPDATE", "ERROR")
        
    Returns
    -------
    int
        Number of rows affected
    """
    try:
        with PostgreSQLManager() as db:
            rows_affected = db.insert_models(
                models=teams,
                table_name="nfl_teams",
                schema="public",
                on_conflict=on_conflict
            )
            return rows_affected
    except Exception as e:
        logger.error(f"Failed to insert NFL teams: {e}")
        return 0


def query_nfl_teams(where_clause: str = "") -> List[NFLTeamData]:
    """
    Query NFL teams from database and return as Pydantic models.
    
    Parameters
    ----------
    where_clause : str
        Optional WHERE clause (without WHERE keyword)
        
    Returns
    -------
    List[NFLTeamData]
        List of NFL team Pydantic models
    """
    try:
        with PostgreSQLManager() as db:
            teams = db.query_to_models(
                model_class=NFLTeamData,
                table_name="nfl_teams",
                where_clause=where_clause,
                schema="public"
            )
            return teams
    except Exception as e:
        logger.error(f"Failed to query NFL teams: {e}")
        return []


def create_nfl_game_log_table(schema: str = "nfl") -> str:
    """
    Generate specialized CREATE TABLE SQL for NFL game log data.
    
    This function creates a properly optimized table for game log data with:
    - boxscore_id as a unique key for linking related tables
    - Proper indexes for common query patterns
    - Foreign key relationships where applicable
    
    Parameters
    ----------
    schema : str
        Database schema name (default: "nfl")
        
    Returns
    -------
    str
        Complete SQL DDL for the game log table
    """
    sql = f"""
-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS {schema};

-- Create NFL game log table with boxscore_id as unique key
CREATE TABLE IF NOT EXISTS {schema}.game_logs (
    id SERIAL PRIMARY KEY,
    
    -- Unique game identifier (critical for linking tables)
    boxscore_id VARCHAR(20) UNIQUE NOT NULL,
    boxscore_url TEXT,
    boxscore_date DATE,
    boxscore_game_number INTEGER DEFAULT 0,
    boxscore_home_team VARCHAR(4),
    
    -- Game identification
    week VARCHAR(10),
    game_num INTEGER,
    date DATE,
    day_of_week VARCHAR(10),
    location VARCHAR(1), -- '@' for away, '' for home
    opponent VARCHAR(4),
    result VARCHAR(1), -- 'W', 'L', 'T'
    team VARCHAR(4) NOT NULL,
    season INTEGER NOT NULL,
    
    -- Score information
    team_score INTEGER,
    opp_score INTEGER,
    
    -- Passing statistics
    pass_cmp INTEGER,
    pass_att INTEGER,
    pass_cmp_pct DECIMAL(5,2),
    pass_yds INTEGER,
    pass_td INTEGER,
    pass_rate DECIMAL(6,2),
    pass_sk INTEGER,
    pass_sk_yds INTEGER,
    
    -- Rushing statistics
    rush_att INTEGER,
    rush_yds INTEGER,
    rush_td INTEGER,
    rush_ypc DECIMAL(4,2),
    
    -- Total offense
    tot_plays INTEGER,
    tot_yds INTEGER,
    tot_ypp DECIMAL(4,2),
    
    -- Turnovers
    to_fumble INTEGER,
    to_int INTEGER,
    
    -- Penalties
    penalty_count INTEGER,
    penalty_yds INTEGER,
    
    -- Down conversions
    third_down_success INTEGER,
    third_down_att INTEGER,
    fourth_down_success INTEGER,
    fourth_down_att INTEGER,
    
    -- Time of possession
    time_of_possession VARCHAR(10),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT game_logs_team_season_week UNIQUE (team, season, week),
    CONSTRAINT game_logs_valid_result CHECK (result IN ('W', 'L', 'T')),
    CONSTRAINT game_logs_valid_location CHECK (location IN ('', '@')),
    CONSTRAINT game_logs_scores_non_negative CHECK (team_score >= 0 AND opp_score >= 0)
);

-- Critical indexes for performance and linking
CREATE UNIQUE INDEX IF NOT EXISTS idx_game_logs_boxscore_id ON {schema}.game_logs(boxscore_id);
CREATE INDEX IF NOT EXISTS idx_game_logs_team_season ON {schema}.game_logs(team, season);
CREATE INDEX IF NOT EXISTS idx_game_logs_date ON {schema}.game_logs(date);
CREATE INDEX IF NOT EXISTS idx_game_logs_opponent ON {schema}.game_logs(opponent);
CREATE INDEX IF NOT EXISTS idx_game_logs_home_team ON {schema}.game_logs(boxscore_home_team);
CREATE INDEX IF NOT EXISTS idx_game_logs_season_week ON {schema}.game_logs(season, week);
CREATE INDEX IF NOT EXISTS idx_game_logs_result ON {schema}.game_logs(result);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_game_logs_modtime ON {schema}.game_logs;
CREATE TRIGGER update_game_logs_modtime
    BEFORE UPDATE ON {schema}.game_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- Create a view for easy game analysis
CREATE OR REPLACE VIEW {schema}.game_summary AS
SELECT 
    boxscore_id,
    date,
    season,
    week,
    team,
    opponent,
    CASE WHEN location = '@' THEN 'Away' ELSE 'Home' END AS home_away,
    result,
    team_score,
    opp_score,
    (team_score - opp_score) AS point_differential,
    pass_yds + rush_yds AS total_offense_yds,
    to_fumble + to_int AS total_turnovers,
    boxscore_url
FROM {schema}.game_logs
ORDER BY date, boxscore_id;

-- Comments for documentation
COMMENT ON TABLE {schema}.game_logs IS 'NFL team game log data with boxscore linking';
COMMENT ON COLUMN {schema}.game_logs.boxscore_id IS 'Unique identifier for linking to boxscore details (format: YYYYMMDD + game_num + home_team)';
COMMENT ON COLUMN {schema}.game_logs.boxscore_game_number IS 'Game sequence number (0=first/only game, 1+=doubleheader)';
COMMENT ON COLUMN {schema}.game_logs.boxscore_home_team IS 'Home team abbreviation from boxscore ID (lowercase)';
COMMENT ON INDEX {schema}.idx_game_logs_boxscore_id IS 'Primary linking key for boxscore-related tables';
COMMENT ON VIEW {schema}.game_summary IS 'Simplified view of game results for quick analysis';
"""
    
    return sql


def create_nfl_boxscore_details_table(schema: str = "nfl") -> str:
    """
    Generate CREATE TABLE SQL for detailed boxscore data.
    
    This table will store detailed game statistics that can be scraped
    using the boxscore_id as the key.
    
    Parameters
    ----------
    schema : str
        Database schema name (default: "nfl")
        
    Returns
    -------
    str
        Complete SQL DDL for the boxscore details table
    """
    sql = f"""
-- Create detailed boxscore data table
CREATE TABLE IF NOT EXISTS {schema}.boxscore_details (
    id SERIAL PRIMARY KEY,
    
    -- Link to game_logs table
    boxscore_id VARCHAR(20) UNIQUE NOT NULL,
    
    -- Game context
    home_team VARCHAR(4) NOT NULL,
    away_team VARCHAR(4) NOT NULL,
    game_date DATE NOT NULL,
    weather TEXT,
    surface VARCHAR(20),
    stadium VARCHAR(100),
    attendance INTEGER,
    
    -- Quarter-by-quarter scoring
    home_q1 INTEGER DEFAULT 0,
    home_q2 INTEGER DEFAULT 0,
    home_q3 INTEGER DEFAULT 0,
    home_q4 INTEGER DEFAULT 0,
    home_ot INTEGER DEFAULT 0,
    home_final INTEGER NOT NULL,
    
    away_q1 INTEGER DEFAULT 0,
    away_q2 INTEGER DEFAULT 0,
    away_q3 INTEGER DEFAULT 0,
    away_q4 INTEGER DEFAULT 0,
    away_ot INTEGER DEFAULT 0,
    away_final INTEGER NOT NULL,
    
    -- Team statistics (home team)
    home_first_downs INTEGER,
    home_total_yds INTEGER,
    home_pass_yds INTEGER,
    home_rush_yds INTEGER,
    home_penalties INTEGER,
    home_penalty_yds INTEGER,
    home_turnovers INTEGER,
    home_fumbles_lost INTEGER,
    home_time_of_possession VARCHAR(10),
    
    -- Team statistics (away team)
    away_first_downs INTEGER,
    away_total_yds INTEGER,
    away_pass_yds INTEGER,
    away_rush_yds INTEGER,
    away_penalties INTEGER,
    away_penalty_yds INTEGER,
    away_turnovers INTEGER,
    away_fumbles_lost INTEGER,
    away_time_of_possession VARCHAR(10),
    
    -- Advanced metrics
    home_third_down_pct DECIMAL(5,2),
    away_third_down_pct DECIMAL(5,2),
    home_red_zone_pct DECIMAL(5,2),
    away_red_zone_pct DECIMAL(5,2),
    
    -- Metadata
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    CONSTRAINT fk_boxscore_details_game_logs 
        FOREIGN KEY (boxscore_id) REFERENCES {schema}.game_logs(boxscore_id) 
        ON DELETE CASCADE
);

-- Indexes for boxscore details
CREATE UNIQUE INDEX IF NOT EXISTS idx_boxscore_details_id ON {schema}.boxscore_details(boxscore_id);
CREATE INDEX IF NOT EXISTS idx_boxscore_details_teams ON {schema}.boxscore_details(home_team, away_team);
CREATE INDEX IF NOT EXISTS idx_boxscore_details_date ON {schema}.boxscore_details(game_date);

-- Update trigger for boxscore details
DROP TRIGGER IF EXISTS update_boxscore_details_modtime ON {schema}.boxscore_details;
CREATE TRIGGER update_boxscore_details_modtime
    BEFORE UPDATE ON {schema}.boxscore_details
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- Comments
COMMENT ON TABLE {schema}.boxscore_details IS 'Detailed boxscore data linked by boxscore_id';
COMMENT ON COLUMN {schema}.boxscore_details.boxscore_id IS 'Links to game_logs.boxscore_id for comprehensive game data';
"""
    
    return sql


def setup_nfl_database_schema(schema: str = "nfl") -> List[str]:
    """
    Generate complete SQL setup for NFL database schema.
    
    Returns
    -------
    List[str]
        List of SQL statements to execute for complete setup
    """
    statements = [
        create_nfl_game_log_table(schema),
        create_nfl_boxscore_details_table(schema)
    ]
    
    return statements


# Convenience functions for inserting game log data
def insert_game_logs(game_logs: List[Dict[str, Any]], schema: str = "nfl") -> bool:
    """
    Insert game log data into the database.
    
    Parameters
    ----------
    game_logs : List[Dict[str, Any]]
        List of game log dictionaries
    schema : str
        Database schema name
        
    Returns
    -------
    bool
        True if successful, False otherwise
    """
    try:
        with PostgreSQLManager() as db:
            # Convert to proper format for insertion
            for game_log in game_logs:
                # Ensure boxscore_id is present and not None
                if not game_log.get('boxscore_id'):
                    logger.warning(f"Skipping game log without boxscore_id: {game_log}")
                    continue
                
                # Insert with ON CONFLICT handling for boxscore_id
                sql = f"""
                INSERT INTO {schema}.game_logs (
                    boxscore_id, boxscore_url, boxscore_date, boxscore_game_number, boxscore_home_team,
                    week, game_num, date, day_of_week, location, opponent, result, team, season,
                    team_score, opp_score, pass_cmp, pass_att, pass_cmp_pct, pass_yds, pass_td,
                    pass_rate, pass_sk, pass_sk_yds, rush_att, rush_yds, rush_td, rush_ypc,
                    tot_plays, tot_yds, tot_ypp, to_fumble, to_int, penalty_count, penalty_yds,
                    third_down_success, third_down_att, fourth_down_success, fourth_down_att,
                    time_of_possession
                ) VALUES (
                    %(boxscore_id)s, %(boxscore_url)s, %(boxscore_date)s, %(boxscore_game_number)s, 
                    %(boxscore_home_team)s, %(week)s, %(game_num)s, %(date)s, %(day_of_week)s,
                    %(location)s, %(opponent)s, %(result)s, %(team)s, %(season)s, %(team_score)s,
                    %(opp_score)s, %(pass_cmp)s, %(pass_att)s, %(pass_cmp_pct)s, %(pass_yds)s,
                    %(pass_td)s, %(pass_rate)s, %(pass_sk)s, %(pass_sk_yds)s, %(rush_att)s,
                    %(rush_yds)s, %(rush_td)s, %(rush_ypc)s, %(tot_plays)s, %(tot_yds)s,
                    %(tot_ypp)s, %(to_fumble)s, %(to_int)s, %(penalty_count)s, %(penalty_yds)s,
                    %(third_down_success)s, %(third_down_att)s, %(fourth_down_success)s,
                    %(fourth_down_att)s, %(time_of_possession)s
                ) ON CONFLICT (boxscore_id) DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP,
                    team_score = EXCLUDED.team_score,
                    opp_score = EXCLUDED.opp_score,
                    result = EXCLUDED.result
                """
                
                # Execute the insert
                db.execute_sql(sql, game_log)
                
        logger.info(f"Successfully inserted {len(game_logs)} game logs")
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert game logs: {e}")
        return False
