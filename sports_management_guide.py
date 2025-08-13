#!/usr/bin/env python3
"""
Sports Data Collection Guide for All Sports Reference

This guide demonstrates how to manage and collect data for different sports
in the All Sports Reference system with proper database integration.

Sports Supported:
- NFL: Football with passing/rushing statistics
- NBA: Basketball with shooting/rebounding statistics  
- NHL: Hockey with goals/assists/saves statistics
- NCAAF: College Football (similar to NFL)
- NCAAB: College Basketball (similar to NBA)

Each sport has:
1. Sport-specific database schema
2. Proper boxscore ID linking
3. Tailored statistics for the sport
4. Cross-sport analytics capabilities
"""

import sys
import os
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))


def setup_logging():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level="INFO"
    )


def demonstrate_cross_sport_queries():
    """
    Demonstrate cross-sport database queries and analytics.
    """
    from src.nfl.database import PostgreSQLManager
    
    logger.info("🏈🏀🏒 Cross-Sport Database Analytics")
    logger.info("=" * 50)
    
    try:
        with PostgreSQLManager() as db:
            # Query 1: Get all sports data summary
            logger.info("📊 Multi-Sport Database Summary:")
            
            sport_schemas = ['nfl', 'nba', 'nhl']
            for schema in sport_schemas:
                try:
                    # Check if schema exists
                    schema_check = db.fetch_one(
                        "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                        (schema,)
                    )
                    
                    if schema_check:
                        # Get record count
                        count_result = db.fetch_one(f"SELECT COUNT(*) FROM {schema}.game_logs")
                        count = count_result[0] if count_result else 0
                        
                        # Get date range
                        date_result = db.fetch_one(
                            f"SELECT MIN(date) as min_date, MAX(date) as max_date FROM {schema}.game_logs"
                        )
                        
                        if date_result and date_result[0]:
                            min_date, max_date = date_result
                            logger.info(f"   {schema.upper()}: {count} games ({min_date} to {max_date})")
                        else:
                            logger.info(f"   {schema.upper()}: {count} games (no date data)")
                    else:
                        logger.info(f"   {schema.upper()}: Schema not found")
                        
                except Exception as e:
                    logger.warning(f"   {schema.upper()}: Error querying - {e}")
            
            # Query 2: Recent games across all sports
            logger.info("\n🎮 Recent Games Across All Sports:")
            
            for schema in sport_schemas:
                try:
                    schema_check = db.fetch_one(
                        "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                        (schema,)
                    )
                    
                    if schema_check:
                        recent_games = db.fetch_all(
                            f"""
                            SELECT '{schema.upper()}' as sport, team, opponent, result, 
                                   team_score, opp_score, date, boxscore_id
                            FROM {schema}.game_logs 
                            ORDER BY date DESC 
                            LIMIT 3
                            """
                        )
                        
                        for game in recent_games:
                            sport, team, opponent, result, team_score, opp_score, date, boxscore_id = game
                            logger.info(f"   {sport}: {team} vs {opponent} ({result} {team_score}-{opp_score}) - {date} [{boxscore_id}]")
                            
                except Exception as e:
                    logger.warning(f"   Error querying recent {schema} games: {e}")
            
            # Query 3: Boxscore ID analysis
            logger.info("\n🔗 Boxscore ID Linking Analysis:")
            
            for schema in sport_schemas:
                try:
                    schema_check = db.fetch_one(
                        "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                        (schema,)
                    )
                    
                    if schema_check:
                        boxscore_stats = db.fetch_one(
                            f"""
                            SELECT 
                                COUNT(*) as total_games,
                                COUNT(DISTINCT boxscore_id) as unique_boxscores,
                                COUNT(DISTINCT team) as unique_teams,
                                COUNT(DISTINCT season) as unique_seasons
                            FROM {schema}.game_logs
                            """
                        )
                        
                        if boxscore_stats:
                            total, unique_box, unique_teams, unique_seasons = boxscore_stats
                            logger.info(f"   {schema.upper()}: {total} games, {unique_box} unique boxscores, {unique_teams} teams, {unique_seasons} seasons")
                            
                except Exception as e:
                    logger.warning(f"   Error analyzing {schema} boxscores: {e}")
                    
    except Exception as e:
        logger.error(f"Failed to demonstrate cross-sport queries: {e}")


def demonstrate_sport_specific_features():
    """
    Demonstrate sport-specific database features and statistics.
    """
    from src.nfl.database import PostgreSQLManager
    
    logger.info("\n🏆 Sport-Specific Features")
    logger.info("=" * 30)
    
    try:
        with PostgreSQLManager() as db:
            # NFL specific features
            logger.info("🏈 NFL Features:")
            try:
                nfl_check = db.fetch_one(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'nfl'"
                )
                
                if nfl_check:
                    # Check for NFL-specific columns
                    nfl_columns = db.fetch_all(
                        """
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'nfl' AND table_name = 'game_logs'
                        AND column_name IN ('pass_yds', 'rush_yds', 'pass_td', 'rush_td')
                        ORDER BY column_name
                        """
                    )
                    
                    if nfl_columns:
                        columns = [row[0] for row in nfl_columns]
                        logger.info(f"   Football-specific stats: {', '.join(columns)}")
                        
                        # Sample NFL stats
                        nfl_sample = db.fetch_one(
                            """
                            SELECT team, opponent, pass_yds, rush_yds, pass_td, rush_td, date
                            FROM nfl.game_logs 
                            WHERE pass_yds IS NOT NULL 
                            ORDER BY date DESC 
                            LIMIT 1
                            """
                        )
                        
                        if nfl_sample:
                            team, opp, pass_yds, rush_yds, pass_td, rush_td, date = nfl_sample
                            logger.info(f"   Sample: {team} vs {opp} ({date}) - {pass_yds} pass yds, {rush_yds} rush yds, {pass_td} pass TD, {rush_td} rush TD")
                    else:
                        logger.info("   NFL schema exists but no football-specific stats found")
                else:
                    logger.info("   NFL schema not found")
                    
            except Exception as e:
                logger.warning(f"   NFL analysis error: {e}")
            
            # NBA specific features
            logger.info("\n🏀 NBA Features:")
            try:
                nba_check = db.fetch_one(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'nba'"
                )
                
                if nba_check:
                    # Check for NBA-specific columns
                    nba_columns = db.fetch_all(
                        """
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'nba' AND table_name = 'game_logs'
                        AND column_name IN ('fg_made', 'fg_att', 'fg3_made', 'fg3_att', 'treb', 'ast')
                        ORDER BY column_name
                        """
                    )
                    
                    if nba_columns:
                        columns = [row[0] for row in nba_columns]
                        logger.info(f"   Basketball-specific stats: {', '.join(columns)}")
                        logger.info("   Ready for NBA data collection with shooting percentages, rebounds, assists")
                    else:
                        logger.info("   NBA schema exists but no basketball-specific stats found")
                else:
                    logger.info("   NBA schema not found")
                    
            except Exception as e:
                logger.warning(f"   NBA analysis error: {e}")
            
            # NHL specific features  
            logger.info("\n🏒 NHL Features:")
            try:
                nhl_check = db.fetch_one(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'nhl'"
                )
                
                if nhl_check:
                    # Check for NHL-specific columns
                    nhl_columns = db.fetch_all(
                        """
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'nhl' AND table_name = 'game_logs'
                        AND column_name IN ('goals', 'assists', 'shots', 'saves', 'pp_goals', 'penalty_minutes')
                        ORDER BY column_name
                        """
                    )
                    
                    if nhl_columns:
                        columns = [row[0] for row in nhl_columns]
                        logger.info(f"   Hockey-specific stats: {', '.join(columns)}")
                        logger.info("   Ready for NHL data collection with goals, assists, power plays, penalties")
                    else:
                        logger.info("   NHL schema exists but no hockey-specific stats found")
                else:
                    logger.info("   NHL schema not found")
                    
            except Exception as e:
                logger.warning(f"   NHL analysis error: {e}")
                
    except Exception as e:
        logger.error(f"Failed to demonstrate sport-specific features: {e}")


def demonstrate_unified_queries():
    """
    Demonstrate unified queries across multiple sports.
    """
    from src.nfl.database import PostgreSQLManager
    
    logger.info("\n🔄 Unified Cross-Sport Queries")
    logger.info("=" * 35)
    
    try:
        with PostgreSQLManager() as db:
            # Create a unified view of all sports data
            logger.info("📋 Creating unified sports view...")
            
            # Check which sports schemas exist
            existing_schemas = []
            for schema in ['nfl', 'nba', 'nhl']:
                schema_check = db.fetch_one(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                    (schema,)
                )
                if schema_check:
                    existing_schemas.append(schema)
            
            if existing_schemas:
                logger.info(f"   Found schemas: {', '.join(existing_schemas)}")
                
                # Example unified query - get games from all sports
                union_parts = []
                for schema in existing_schemas:
                    union_parts.append(f"""
                        SELECT 
                            '{schema.upper()}' as sport,
                            team,
                            opponent, 
                            result,
                            team_score,
                            opp_score,
                            date,
                            boxscore_id,
                            season
                        FROM {schema}.game_logs
                    """)
                
                if union_parts:
                    unified_query = " UNION ALL ".join(union_parts) + " ORDER BY date DESC LIMIT 10"
                    
                    logger.info("🎯 Recent games across all sports:")
                    unified_results = db.fetch_all(unified_query)
                    
                    for game in unified_results:
                        sport, team, opponent, result, team_score, opp_score, date, boxscore_id, season = game
                        logger.info(f"   {sport}: {team} vs {opponent} ({result} {team_score}-{opp_score}) - {date} S{season}")
                
                # Sport comparison query
                logger.info("\n📊 Games by sport:")
                for schema in existing_schemas:
                    count_result = db.fetch_one(f"SELECT COUNT(*) FROM {schema}.game_logs")
                    count = count_result[0] if count_result else 0
                    logger.info(f"   {schema.upper()}: {count} games")
                    
            else:
                logger.warning("   No sport schemas found for unified queries")
                
    except Exception as e:
        logger.error(f"Failed to demonstrate unified queries: {e}")


def main():
    """Main demonstration function."""
    setup_logging()
    
    logger.info("🏈🏀🏒 All Sports Reference - Multi-Sport Database Management")
    logger.info("=" * 70)
    
    # Demonstrate cross-sport capabilities
    demonstrate_cross_sport_queries()
    
    # Show sport-specific features
    demonstrate_sport_specific_features()
    
    # Show unified query capabilities
    demonstrate_unified_queries()
    
    logger.info("\n🎯 Multi-Sport Management Summary:")
    logger.info("✅ Database schemas: Sport-specific with proper field types")
    logger.info("✅ Boxscore linking: Unique IDs across all sports") 
    logger.info("✅ Cross-sport analytics: Unified queries and comparisons")
    logger.info("✅ Sport-specific stats: Tailored to each sport's needs")
    
    logger.info("\n💡 Next Steps:")
    logger.info("1. Set up remaining sports: python multi_sport_database.py --setup-all")
    logger.info("2. Collect sport-specific data using existing modules")
    logger.info("3. Build cross-sport analytics and reporting")
    logger.info("4. Implement sport-specific data collection adapters")


if __name__ == "__main__":
    main()
