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

from .models import NFLTeamData, NFLConference

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
