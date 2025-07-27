"""
Database utilities for loading sports data into PostgreSQL.

This module provides functions to:
- Create sport-specific schemas
- Create season-partitioned tables
- Load CSV files into PostgreSQL
- Manage database connections
"""

import os
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from loguru import logger
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import configuration
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import config


class SportsDatabase:
    """
    Main class for managing sports data in PostgreSQL.
    """
    
    def __init__(self, host=None, port=None, database=None, 
                 user=None, password=None):
        """
        Initialize database connection parameters.
        Uses configuration from config.py if parameters are not provided.
        
        Parameters
        ----------
        host : str, optional
            Database host (uses config.db_host if None)
        port : int, optional
            Database port (uses config.db_port if None)
        database : str, optional
            Database name (uses config.db_name if None)
        user : str, optional
            Database user (uses config.db_user if None)
        password : str, optional
            Database password (uses config.db_password if None)
        """
        # Use provided parameters or fall back to configuration
        self.connection_params = {
            'host': host or config.db_host,
            'port': port or config.db_port,
            'database': database or config.db_name,
            'user': user or config.db_user,
            'password': password or config.db_password
        }
        logger.info(f"Initialized SportsDatabase connection to {self.connection_params['host']}:{self.connection_params['port']}/{self.connection_params['database']}")
    
    @classmethod
    def from_config(cls):
        """
        Create SportsDatabase instance using configuration values.
        
        Returns
        -------
        SportsDatabase
            Database instance configured from environment
        """
        return cls(**config.database_config)
    
    def get_connection(self):
        """Get a database connection."""
        try:
            logger.debug("Attempting to connect to database")
            conn = psycopg2.connect(**self.connection_params)
            logger.success("Database connection established")
            return conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def create_schema(self, sport: str) -> bool:
        """
        Create a schema for a specific sport.
        
        Parameters
        ----------
        sport : str
            Sport name (e.g., 'nfl', 'nba')
            
        Returns
        -------
        bool
            True if schema was created successfully
        """
        schema_name = sport.lower()
        logger.info(f"Creating schema for sport: {schema_name}")
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create schema if it doesn't exist
                    cursor.execute(
                        sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                            sql.Identifier(schema_name)
                        )
                    )
                    conn.commit()
                    logger.success(f"Schema '{schema_name}' created successfully")
                    return True
        except psycopg2.Error as e:
            logger.error(f"Failed to create schema '{schema_name}': {e}")
            return False
    
    def create_partitioned_table(self, sport: str, table_name: str, 
                                columns: Dict[str, str], partition_column: str = 'season') -> bool:
        """
        Create a partitioned table for season-based data.
        
        Parameters
        ----------
        sport : str
            Sport name for schema
        table_name : str
            Base table name (e.g., 'schedule', 'roster')
        columns : Dict[str, str]
            Column definitions {'column_name': 'data_type'}
        partition_column : str
            Column to partition on (default: 'season')
            
        Returns
        -------
        bool
            True if table was created successfully
        """
        schema_name = sport.lower()
        logger.info(f"Creating partitioned table: {schema_name}.{table_name}")
        logger.debug(f"Table columns: {columns}")
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Build column definitions
                    column_defs = []
                    for col_name, col_type in columns.items():
                        column_defs.append(f"{col_name} {col_type}")
                    
                    # Create partitioned table
                    create_sql = f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (
                        {', '.join(column_defs)}
                    ) PARTITION BY RANGE ({partition_column})
                    """
                    
                    cursor.execute(create_sql)
                    conn.commit()
                    logger.success(f"Partitioned table '{schema_name}.{table_name}' created successfully")
                    return True
        except psycopg2.Error as e:
            logger.error(f"Failed to create partitioned table '{schema_name}.{table_name}': {e}")
            return False
    
    def create_season_partition(self, sport: str, table_name: str, season: str) -> bool:
        """
        Create a partition for a specific season.
        
        Parameters
        ----------
        sport : str
            Sport name for schema
        table_name : str
            Base table name
        season : str
            Season to create partition for (e.g., '2024')
            
        Returns
        -------
        bool
            True if partition was created successfully
        """
        schema_name = sport.lower()
        partition_name = f"{table_name}_{season}"
        logger.info(f"Creating partition: {schema_name}.{partition_name}")
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create partition for specific season
                    next_season = str(int(season) + 1)
                    create_partition_sql = f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.{partition_name}
                    PARTITION OF {schema_name}.{table_name}
                    FOR VALUES FROM ('{season}') TO ('{next_season}')
                    """
                    
                    cursor.execute(create_partition_sql)
                    conn.commit()
                    logger.success(f"Partition '{schema_name}.{partition_name}' created successfully")
                    return True
        except psycopg2.Error as e:
            logger.error(f"Failed to create partition '{schema_name}.{partition_name}': {e}")
            return False
    
    def load_csv_to_table(self, csv_path: str, sport: str, table_name: str, 
                         season: str = None, create_table: bool = True) -> bool:
        """
        Load a CSV file into a PostgreSQL table.
        
        Parameters
        ----------
        csv_path : str
            Path to the CSV file
        sport : str
            Sport name for schema
        table_name : str
            Table name to load data into
        season : str, optional
            Season for partitioned tables
        create_table : bool
            Whether to create table automatically (default: True)
            
        Returns
        -------
        bool
            True if data was loaded successfully
        """
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return False
            
        schema_name = sport.lower()
        logger.info(f"Loading CSV data from {csv_path} to {schema_name}.{table_name}")
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_path)
            logger.debug(f"CSV loaded with {len(df)} rows and {len(df.columns)} columns")
            
            if df.empty:
                logger.warning(f"CSV file is empty: {csv_path}")
                return True
            
            # Auto-create table if requested
            if create_table:
                self._auto_create_table_from_df(df, sport, table_name, season)
            
            # Load data using pandas to_sql
            table_full_name = f"{schema_name}.{table_name}"
            if season:
                table_full_name = f"{schema_name}.{table_name}_{season}"
            
            with self.get_connection() as conn:
                df.to_sql(
                    name=table_name if not season else f"{table_name}_{season}",
                    con=conn,
                    schema=schema_name,
                    if_exists='append',
                    index=False,
                    method='multi'
                )
                logger.success(f"Successfully loaded {len(df)} rows to {table_full_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to load CSV to table: {e}")
            return False
    
    def _auto_create_table_from_df(self, df: pd.DataFrame, sport: str, 
                                  table_name: str, season: str = None) -> bool:
        """
        Automatically create table based on DataFrame structure.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to analyze for table structure
        sport : str
            Sport name for schema
        table_name : str
            Table name to create
        season : str, optional
            Season for partitioned tables
            
        Returns
        -------
        bool
            True if table was created successfully
        """
        logger.debug(f"Auto-creating table structure for {sport}.{table_name}")
        
        # Map pandas dtypes to PostgreSQL types
        dtype_mapping = {
            'object': 'TEXT',
            'int64': 'INTEGER',
            'float64': 'REAL',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'TIMESTAMP'
        }
        
        columns = {}
        for col_name, dtype in df.dtypes.items():
            pg_type = dtype_mapping.get(str(dtype), 'TEXT')
            columns[col_name] = pg_type
        
        # Add season column if not present and season is specified
        if season and 'season' not in columns:
            columns['season'] = 'TEXT'
        
        # Create schema first
        self.create_schema(sport)
        
        # Create partitioned table or regular table
        if season:
            success = self.create_partitioned_table(sport, table_name, columns, 'season')
            if success:
                success = self.create_season_partition(sport, table_name, season)
            return success
        else:
            return self.create_regular_table(sport, table_name, columns)
    
    def create_regular_table(self, sport: str, table_name: str, 
                           columns: Dict[str, str]) -> bool:
        """
        Create a regular (non-partitioned) table.
        
        Parameters
        ----------
        sport : str
            Sport name for schema
        table_name : str
            Table name to create
        columns : Dict[str, str]
            Column definitions {'column_name': 'data_type'}
            
        Returns
        -------
        bool
            True if table was created successfully
        """
        schema_name = sport.lower()
        logger.info(f"Creating regular table: {schema_name}.{table_name}")
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Build column definitions
                    column_defs = []
                    for col_name, col_type in columns.items():
                        column_defs.append(f"{col_name} {col_type}")
                    
                    # Create regular table
                    create_sql = f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (
                        {', '.join(column_defs)}
                    )
                    """
                    
                    cursor.execute(create_sql)
                    conn.commit()
                    logger.success(f"Regular table '{schema_name}.{table_name}' created successfully")
                    return True
        except psycopg2.Error as e:
            logger.error(f"Failed to create regular table '{schema_name}.{table_name}': {e}")
            return False
    
    def infer_column_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Infer PostgreSQL column types from pandas DataFrame.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to analyze
            
        Returns
        -------
        Dict[str, str]
            Column name to PostgreSQL type mapping
        """
        type_mapping = {
            'object': 'TEXT',
            'int64': 'INTEGER',
            'float64': 'DECIMAL',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'TIMESTAMP'
        }
        
        columns = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            # Handle special cases
            if dtype == 'object':
                # Check if it might be a date
                if col.lower() in ['date', 'game_date', 'created_at', 'updated_at']:
                    columns[col] = 'DATE'
                else:
                    # Check max length for VARCHAR vs TEXT
                    max_len = df[col].astype(str).str.len().max()
                    if pd.isna(max_len) or max_len > 255:
                        columns[col] = 'TEXT'
                    else:
                        columns[col] = f'VARCHAR({min(int(max_len * 1.5), 255)})'
            else:
                columns[col] = type_mapping.get(dtype, 'TEXT')
        
        # Always add season column if not present
        if 'season' not in columns:
            columns['season'] = 'INTEGER'
        
        return columns
    
    def load_csv_to_table(self, csv_file_path: str, sport: str, table_name: str, 
                         season: int, create_table: bool = True) -> bool:
        """
        Load a CSV file into a PostgreSQL table.
        
        Parameters
        ----------
        csv_file_path : str
            Path to the CSV file
        sport : str
            Sport name for schema
        table_name : str
            Table name
        season : int
            Season year
        create_table : bool
            Whether to create table and partition if they don't exist
            
        Returns
        -------
        bool
            True if data was loaded successfully
        """
        if not os.path.exists(csv_file_path):
            self.logger.error(f"CSV file not found: {csv_file_path}")
            return False
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            
            # Add season column if not present
            if 'season' not in df.columns:
                df['season'] = season
            
            # Create schema if needed
            if create_table:
                self.create_schema(sport)
                
                # Infer column types
                columns = self.infer_column_types(df)
                
                # Create partitioned table
                self.create_partitioned_table(sport, table_name, columns)
                
                # Create season partition
                self.create_season_partition(sport, table_name, season)
            
            # Load data using pandas to_sql
            schema_name = sport.lower()
            
            # Create engine for pandas
            from sqlalchemy import create_engine
            engine_url = f"postgresql://{self.connection_params['user']}:{self.connection_params['password']}@{self.connection_params['host']}:{self.connection_params['port']}/{self.connection_params['database']}"
            engine = create_engine(engine_url)
            
            # Insert data into the specific partition
            partition_name = f"{table_name}_{season}"
            df.to_sql(partition_name, engine, schema=schema_name, 
                     if_exists='append', index=False, method='multi')
            
            self.logger.info(f"Successfully loaded {len(df)} rows from '{csv_file_path}' to '{schema_name}.{partition_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load CSV '{csv_file_path}': {e}")
            return False
    
    def load_organized_data(self, data_dir: str = 'data') -> Dict[str, List[str]]:
        """
        Load all CSV files from the organized directory structure.
        
        Parameters
        ----------
        data_dir : str
            Base data directory (default: 'data')
            
        Returns
        -------
        Dict[str, List[str]]
            Summary of loaded files by sport
        """
        loaded_files = {}
        
        if not os.path.exists(data_dir):
            self.logger.error(f"Data directory not found: {data_dir}")
            return loaded_files
        
        # Walk through the organized directory structure
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    
                    # Parse the directory structure to extract metadata
                    # Expected: data/sport/season/teams/team/file.csv
                    path_parts = os.path.relpath(file_path, data_dir).split(os.sep)
                    
                    if len(path_parts) >= 3:
                        sport = path_parts[0]
                        season = int(path_parts[1])
                        
                        # Extract table name from filename
                        # e.g., "NE_2024_schedule.csv" -> "schedule"
                        filename_parts = file.replace('.csv', '').split('_')
                        if len(filename_parts) >= 3:
                            table_name = '_'.join(filename_parts[2:])  # Everything after team_season_
                        else:
                            table_name = filename_parts[-1] if filename_parts else 'unknown'
                        
                        # Load the file
                        if self.load_csv_to_table(file_path, sport, table_name, season):
                            if sport not in loaded_files:
                                loaded_files[sport] = []
                            loaded_files[sport].append(file_path)
        
        return loaded_files


def create_database_config() -> Dict[str, str]:
    """
    Create database configuration from environment variables or defaults.
    
    Returns
    -------
    Dict[str, str]
        Database configuration
    """
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'sportsdb'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password')
    }


def load_csv_files(data_dir: str = 'data', **db_config) -> bool:
    """
    Convenience function to load all CSV files from organized structure.
    
    Parameters
    ----------
    data_dir : str
        Data directory path
    **db_config
        Database connection parameters
        
    Returns
    -------
    bool
        True if all files loaded successfully
    """
    # Setup logging
    logger.info("Loading CSV files from organized data structure")
    
    # Use provided config or defaults
    config = create_database_config()
    config.update(db_config)
    
    # Create database instance and load files
    db = SportsDatabase(**config)
    loaded_files = db.load_organized_data(data_dir)
    
    # Print summary
    print("Database Load Summary:")
    print("=" * 40)
    total_files = 0
    for sport, files in loaded_files.items():
        print(f"{sport.upper()}: {len(files)} files loaded")
        total_files += len(files)
    
    print(f"\nTotal: {total_files} files loaded successfully")
    return total_files > 0