#!/usr/bin/env python3
"""
Multi-Sport Database Manager for All Sports Reference

This module provides unified database management for all sports including:
- NFL, NBA, NHL, NCAAF, NCAAB
- Sport-specific schema generation
- Cross-sport analytics capabilities
- Unified data collection interfaces

Usage:
    python multi_sport_database.py --setup-all           # Setup all sports schemas
    python multi_sport_database.py --setup-sport nba     # Setup specific sport
    python multi_sport_database.py --list-sports         # List available sports
    python multi_sport_database.py --collect nba LAL 2024 # Collect specific data
"""

import sys
import os
import argparse
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from src.nfl.database import PostgreSQLManager


@dataclass
class SportConfig:
    """Configuration for a sport's database structure."""
    name: str
    display_name: str
    schema_name: str
    primary_table: str
    boxscore_table: str
    has_boxscores: bool = True
    has_playoffs: bool = True
    season_structure: str = "fall"  # fall, winter, spring, split


class MultiSportDatabaseManager:
    """
    Unified database manager for all sports in the All Sports Reference system.
    """
    
    def __init__(self):
        """Initialize the multi-sport database manager."""
        self.sports_configs = {
            'nfl': SportConfig(
                name='nfl',
                display_name='NFL',
                schema_name='nfl',
                primary_table='game_logs',
                boxscore_table='boxscore_details',
                has_boxscores=True,
                has_playoffs=True,
                season_structure='fall'
            ),
            'nba': SportConfig(
                name='nba',
                display_name='NBA',
                schema_name='nba',
                primary_table='game_logs',
                boxscore_table='boxscore_details',
                has_boxscores=True,
                has_playoffs=True,
                season_structure='winter'
            ),
            'nhl': SportConfig(
                name='nhl',
                display_name='NHL',
                schema_name='nhl',
                primary_table='game_logs',
                boxscore_table='boxscore_details',
                has_boxscores=True,
                has_playoffs=True,
                season_structure='winter'
            ),
            'ncaaf': SportConfig(
                name='ncaaf',
                display_name='NCAA Football',
                schema_name='ncaaf',
                primary_table='game_logs',
                boxscore_table='boxscore_details',
                has_boxscores=True,
                has_playoffs=True,
                season_structure='fall'
            ),
            'ncaab': SportConfig(
                name='ncaab',
                display_name='NCAA Basketball',
                schema_name='ncaab',
                primary_table='game_logs',
                boxscore_table='boxscore_details',
                has_boxscores=True,
                has_playoffs=True,
                season_structure='winter'
            )
        }
    
    def get_sport_config(self, sport: str) -> SportConfig:
        """Get configuration for a specific sport."""
        if sport.lower() not in self.sports_configs:
            raise ValueError(f"Unsupported sport: {sport}. Available: {list(self.sports_configs.keys())}")
        return self.sports_configs[sport.lower()]
    
    def list_sports(self) -> List[SportConfig]:
        """List all configured sports."""
        return list(self.sports_configs.values())
    
    def create_nba_schema(self, schema: str = "nba") -> str:
        """
        Generate CREATE TABLE SQL for NBA game log data.
        
        NBA games have different statistics compared to NFL:
        - Points, rebounds, assists instead of passing/rushing yards
        - Field goals, three-pointers, free throws
        - Different game structure (4 quarters vs 4 quarters + OT)
        """
        sql = f"""
-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS {schema};

-- Create NBA game log table with basketball-specific statistics
CREATE TABLE IF NOT EXISTS {schema}.game_logs (
    id SERIAL PRIMARY KEY,
    
    -- Unique game identifier (critical for linking tables)
    boxscore_id VARCHAR(20) UNIQUE NOT NULL,
    boxscore_url TEXT,
    boxscore_date DATE,
    boxscore_game_number INTEGER DEFAULT 0,
    boxscore_home_team VARCHAR(4),
    
    -- Game identification
    game_num INTEGER,
    date DATE,
    day_of_week VARCHAR(10),
    location VARCHAR(1), -- '@' for away, '' for home
    opponent VARCHAR(4),
    result VARCHAR(1), -- 'W', 'L'
    team VARCHAR(4) NOT NULL,
    season INTEGER NOT NULL,
    
    -- Score information
    team_score INTEGER,
    opp_score INTEGER,
    
    -- Basketball-specific statistics
    fg_made INTEGER,
    fg_att INTEGER,
    fg_pct DECIMAL(5,3),
    fg3_made INTEGER,
    fg3_att INTEGER,
    fg3_pct DECIMAL(5,3),
    ft_made INTEGER,
    ft_att INTEGER,
    ft_pct DECIMAL(5,3),
    
    -- Rebounds
    oreb INTEGER,
    dreb INTEGER,
    treb INTEGER,
    
    -- Other basketball stats
    ast INTEGER,
    stl INTEGER,
    blk INTEGER,
    tov INTEGER,
    pf INTEGER,
    
    -- Advanced metrics
    pace DECIMAL(6,2),
    efg_pct DECIMAL(5,3),
    tov_pct DECIMAL(5,3),
    orb_pct DECIMAL(5,3),
    ft_rate DECIMAL(5,3),
    
    -- Game flow
    largest_lead INTEGER,
    minutes_with_lead INTEGER,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT nba_game_logs_team_season_date UNIQUE (team, season, date, opponent),
    CONSTRAINT nba_game_logs_valid_result CHECK (result IN ('W', 'L')),
    CONSTRAINT nba_game_logs_valid_location CHECK (location IN ('', '@')),
    CONSTRAINT nba_game_logs_scores_non_negative CHECK (team_score >= 0 AND opp_score >= 0)
);

-- Critical indexes for performance and linking
CREATE UNIQUE INDEX IF NOT EXISTS idx_nba_game_logs_boxscore_id ON {schema}.game_logs(boxscore_id);
CREATE INDEX IF NOT EXISTS idx_nba_game_logs_team_season ON {schema}.game_logs(team, season);
CREATE INDEX IF NOT EXISTS idx_nba_game_logs_date ON {schema}.game_logs(date);
CREATE INDEX IF NOT EXISTS idx_nba_game_logs_opponent ON {schema}.game_logs(opponent);
CREATE INDEX IF NOT EXISTS idx_nba_game_logs_home_team ON {schema}.game_logs(boxscore_home_team);
CREATE INDEX IF NOT EXISTS idx_nba_game_logs_result ON {schema}.game_logs(result);

-- Create update trigger for updated_at
DROP TRIGGER IF EXISTS update_nba_game_logs_modtime ON {schema}.game_logs;
CREATE TRIGGER update_nba_game_logs_modtime
    BEFORE UPDATE ON {schema}.game_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- Create a view for easy game analysis
CREATE OR REPLACE VIEW {schema}.game_summary AS
SELECT 
    boxscore_id,
    date,
    season,
    team,
    opponent,
    CASE WHEN location = '@' THEN 'Away' ELSE 'Home' END AS home_away,
    result,
    team_score,
    opp_score,
    (team_score - opp_score) AS point_differential,
    fg_made,
    fg_att,
    fg_pct,
    fg3_made,
    fg3_att,
    fg3_pct,
    treb as total_rebounds,
    ast as assists,
    tov as turnovers,
    boxscore_url
FROM {schema}.game_logs
ORDER BY date, boxscore_id;

-- Comments for documentation
COMMENT ON TABLE {schema}.game_logs IS 'NBA team game log data with boxscore linking';
COMMENT ON COLUMN {schema}.game_logs.boxscore_id IS 'Unique identifier for linking to boxscore details (basketball-reference format)';
COMMENT ON COLUMN {schema}.game_logs.fg_pct IS 'Field goal percentage (0.000-1.000)';
COMMENT ON COLUMN {schema}.game_logs.fg3_pct IS 'Three-point field goal percentage (0.000-1.000)';
COMMENT ON COLUMN {schema}.game_logs.ft_pct IS 'Free throw percentage (0.000-1.000)';
COMMENT ON INDEX {schema}.idx_nba_game_logs_boxscore_id IS 'Primary linking key for boxscore-related tables';
COMMENT ON VIEW {schema}.game_summary IS 'Simplified view of NBA game results for quick analysis';
"""
        return sql
    
    def create_nhl_schema(self, schema: str = "nhl") -> str:
        """
        Generate CREATE TABLE SQL for NHL game log data.
        
        NHL games have hockey-specific statistics:
        - Goals, assists, points
        - Shots on goal, saves, save percentage
        - Power play opportunities
        - Penalty minutes
        - Face-off wins
        """
        sql = f"""
-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS {schema};

-- Create NHL game log table with hockey-specific statistics
CREATE TABLE IF NOT EXISTS {schema}.game_logs (
    id SERIAL PRIMARY KEY,
    
    -- Unique game identifier (critical for linking tables)
    boxscore_id VARCHAR(20) UNIQUE NOT NULL,
    boxscore_url TEXT,
    boxscore_date DATE,
    boxscore_game_number INTEGER DEFAULT 0,
    boxscore_home_team VARCHAR(4),
    
    -- Game identification
    game_num INTEGER,
    date DATE,
    day_of_week VARCHAR(10),
    location VARCHAR(1), -- '@' for away, '' for home
    opponent VARCHAR(4),
    result VARCHAR(2), -- 'W', 'L', 'OTL', 'SOL' (overtime/shootout loss)
    team VARCHAR(4) NOT NULL,
    season INTEGER NOT NULL,
    
    -- Score information
    team_score INTEGER,
    opp_score INTEGER,
    
    -- Hockey-specific statistics
    goals INTEGER,
    assists INTEGER,
    points INTEGER,
    plus_minus INTEGER,
    
    -- Shooting
    shots INTEGER,
    shot_pct DECIMAL(5,3),
    
    -- Goaltending
    saves INTEGER,
    save_pct DECIMAL(5,3),
    goals_against INTEGER,
    
    -- Special teams
    pp_goals INTEGER,
    pp_opportunities INTEGER,
    pp_pct DECIMAL(5,3),
    sh_goals INTEGER,
    pk_opportunities INTEGER,
    pk_pct DECIMAL(5,3),
    
    -- Physical play
    hits INTEGER,
    blocks INTEGER,
    penalty_minutes INTEGER,
    
    -- Face-offs
    faceoff_wins INTEGER,
    faceoff_attempts INTEGER,
    faceoff_pct DECIMAL(5,3),
    
    -- Game flow
    periods INTEGER DEFAULT 3,
    overtime BOOLEAN DEFAULT FALSE,
    shootout BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT nhl_game_logs_team_season_date UNIQUE (team, season, date, opponent),
    CONSTRAINT nhl_game_logs_valid_result CHECK (result IN ('W', 'L', 'OTL', 'SOL')),
    CONSTRAINT nhl_game_logs_valid_location CHECK (location IN ('', '@')),
    CONSTRAINT nhl_game_logs_scores_non_negative CHECK (team_score >= 0 AND opp_score >= 0)
);

-- Critical indexes for performance and linking
CREATE UNIQUE INDEX IF NOT EXISTS idx_nhl_game_logs_boxscore_id ON {schema}.game_logs(boxscore_id);
CREATE INDEX IF NOT EXISTS idx_nhl_game_logs_team_season ON {schema}.game_logs(team, season);
CREATE INDEX IF NOT EXISTS idx_nhl_game_logs_date ON {schema}.game_logs(date);
CREATE INDEX IF NOT EXISTS idx_nhl_game_logs_opponent ON {schema}.game_logs(opponent);
CREATE INDEX IF NOT EXISTS idx_nhl_game_logs_home_team ON {schema}.game_logs(boxscore_home_team);
CREATE INDEX IF NOT EXISTS idx_nhl_game_logs_result ON {schema}.game_logs(result);

-- Create update trigger for updated_at
DROP TRIGGER IF EXISTS update_nhl_game_logs_modtime ON {schema}.game_logs;
CREATE TRIGGER update_nhl_game_logs_modtime
    BEFORE UPDATE ON {schema}.game_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- Create a view for easy game analysis
CREATE OR REPLACE VIEW {schema}.game_summary AS
SELECT 
    boxscore_id,
    date,
    season,
    team,
    opponent,
    CASE WHEN location = '@' THEN 'Away' ELSE 'Home' END AS home_away,
    result,
    team_score,
    opp_score,
    (team_score - opp_score) AS goal_differential,
    goals,
    assists,
    points,
    shots,
    shot_pct,
    pp_goals,
    pp_opportunities,
    penalty_minutes,
    CASE WHEN overtime THEN 'OT' 
         WHEN shootout THEN 'SO' 
         ELSE 'REG' END AS game_type,
    boxscore_url
FROM {schema}.game_logs
ORDER BY date, boxscore_id;

-- Comments for documentation
COMMENT ON TABLE {schema}.game_logs IS 'NHL team game log data with boxscore linking';
COMMENT ON COLUMN {schema}.game_logs.boxscore_id IS 'Unique identifier for linking to boxscore details (hockey-reference format)';
COMMENT ON COLUMN {schema}.game_logs.result IS 'Game result: W=Win, L=Loss, OTL=Overtime Loss, SOL=Shootout Loss';
COMMENT ON COLUMN {schema}.game_logs.plus_minus IS 'Team plus/minus rating for the game';
COMMENT ON INDEX {schema}.idx_nhl_game_logs_boxscore_id IS 'Primary linking key for boxscore-related tables';
COMMENT ON VIEW {schema}.game_summary IS 'Simplified view of NHL game results for quick analysis';
"""
        return sql
    
    def create_sport_schema(self, sport: str) -> str:
        """
        Create database schema for a specific sport.
        
        Parameters
        ----------
        sport : str
            Sport name (nfl, nba, nhl, etc.)
            
        Returns
        -------
        str
            SQL DDL for the sport's schema
        """
        config = self.get_sport_config(sport)
        
        if sport.lower() == 'nfl':
            # Use existing NFL schema from nfl.database
            from src.nfl.database import create_nfl_game_log_table
            return create_nfl_game_log_table(config.schema_name)
        elif sport.lower() == 'nba':
            return self.create_nba_schema(config.schema_name)
        elif sport.lower() == 'nhl':
            return self.create_nhl_schema(config.schema_name)
        elif sport.lower() in ['ncaaf', 'ncaab']:
            # NCAA sports can reuse NFL/NBA schemas with modifications
            if sport.lower() == 'ncaaf':
                # NCAA Football similar to NFL
                from src.nfl.database import create_nfl_game_log_table
                return create_nfl_game_log_table(config.schema_name)
            else:
                # NCAA Basketball similar to NBA
                return self.create_nba_schema(config.schema_name)
        else:
            raise ValueError(f"Schema generation not implemented for sport: {sport}")
    
    def setup_sport_database(self, sport: str) -> bool:
        """
        Setup database schema for a specific sport.
        
        Parameters
        ----------
        sport : str
            Sport name
            
        Returns
        -------
        bool
            True if successful
        """
        try:
            config = self.get_sport_config(sport)
            logger.info(f"🏒 Setting up {config.display_name} database schema...")
            
            # Generate schema SQL
            schema_sql = self.create_sport_schema(sport)
            
            # Execute the schema creation
            with PostgreSQLManager() as db:
                db.execute_sql(schema_sql)
            
            logger.info(f"✅ {config.display_name} schema created successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup {sport} database: {e}")
            return False
    
    def setup_all_sports(self) -> bool:
        """
        Setup database schemas for all configured sports.
        
        Returns
        -------
        bool
            True if all successful
        """
        logger.info("🏈🏀🏒 Setting up all sports database schemas...")
        
        success_count = 0
        total_sports = len(self.sports_configs)
        
        for sport_name in self.sports_configs.keys():
            if self.setup_sport_database(sport_name):
                success_count += 1
        
        if success_count == total_sports:
            logger.info(f"🎉 All {total_sports} sports schemas created successfully!")
            return True
        else:
            logger.warning(f"⚠️  Only {success_count}/{total_sports} sports schemas created successfully")
            return False
    
    def get_database_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all sport databases.
        
        Returns
        -------
        Dict[str, Dict[str, Any]]
            Status information for each sport
        """
        status = {}
        
        try:
            with PostgreSQLManager() as db:
                for sport_name, config in self.sports_configs.items():
                    sport_status = {
                        'schema_exists': False,
                        'tables': {},
                        'record_count': 0
                    }
                    
                    # Check if schema exists
                    schema_result = db.fetch_one(
                        "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                        (config.schema_name,)
                    )
                    sport_status['schema_exists'] = schema_result is not None
                    
                    if sport_status['schema_exists']:
                        # Check if primary table exists
                        table_result = db.fetch_one(
                            """
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = %s AND table_name = %s
                            """,
                            (config.schema_name, config.primary_table)
                        )
                        sport_status['tables'][config.primary_table] = table_result is not None
                        
                        # Get record count if table exists
                        if sport_status['tables'][config.primary_table]:
                            count_result = db.fetch_one(
                                f"SELECT COUNT(*) FROM {config.schema_name}.{config.primary_table}"
                            )
                            sport_status['record_count'] = count_result[0] if count_result else 0
                    
                    status[sport_name] = sport_status
                    
        except Exception as e:
            logger.error(f"Failed to get database status: {e}")
        
        return status


def setup_logging():
    """Configure logging for the multi-sport database manager."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )


def main():
    """Main function for the multi-sport database manager."""
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Multi-Sport Database Manager for All Sports Reference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python multi_sport_database.py --setup-all                    # Setup all sports
    python multi_sport_database.py --setup-sport nba              # Setup NBA only
    python multi_sport_database.py --setup-sport nhl              # Setup NHL only
    python multi_sport_database.py --list-sports                  # List sports
    python multi_sport_database.py --status                       # Show status
        """
    )
    
    parser.add_argument(
        '--setup-all',
        action='store_true',
        help='Setup database schemas for all sports'
    )
    
    parser.add_argument(
        '--setup-sport',
        type=str,
        help='Setup database schema for specific sport (nfl, nba, nhl, ncaaf, ncaab)'
    )
    
    parser.add_argument(
        '--list-sports',
        action='store_true',
        help='List all configured sports'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show database status for all sports'
    )
    
    args = parser.parse_args()
    
    # Initialize the manager
    manager = MultiSportDatabaseManager()
    
    logger.info("🏈🏀🏒 Multi-Sport Database Manager")
    logger.info("=" * 50)
    
    if args.list_sports:
        logger.info("📋 Configured Sports:")
        for config in manager.list_sports():
            logger.info(f"   {config.display_name} ({config.name}) - Schema: {config.schema_name}")
        return
    
    if args.status:
        logger.info("📊 Database Status:")
        status = manager.get_database_status()
        for sport_name, sport_status in status.items():
            config = manager.get_sport_config(sport_name)
            schema_status = "✅" if sport_status['schema_exists'] else "❌"
            table_status = "✅" if sport_status['tables'].get(config.primary_table, False) else "❌"
            record_count = sport_status['record_count']
            
            logger.info(f"   {config.display_name}:")
            logger.info(f"      Schema: {schema_status} ({config.schema_name})")
            logger.info(f"      Table:  {table_status} ({config.primary_table})")
            logger.info(f"      Records: {record_count}")
        return
    
    if args.setup_sport:
        success = manager.setup_sport_database(args.setup_sport)
        if success:
            logger.info(f"🎯 {args.setup_sport.upper()} database setup completed!")
        else:
            logger.error(f"❌ {args.setup_sport.upper()} database setup failed!")
            sys.exit(1)
        return
    
    if args.setup_all:
        success = manager.setup_all_sports()
        if success:
            logger.info("🎯 All sports database setup completed!")
        else:
            logger.error("❌ Some sports database setups failed!")
            sys.exit(1)
        return
    
    # Default action - show help
    parser.print_help()


if __name__ == "__main__":
    main()
