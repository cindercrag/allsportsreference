#!/usr/bin/env python3
"""
Database Reset and Rebuild Script for All Sports Reference

This script completely destroys and recreates the entire database structure
to ensure a clean, working system from scratch.

WARNING: This will DELETE ALL DATA in the sports schemas!

Usage:
    python reset_and_rebuild.py --confirm         # Full reset and rebuild
    python reset_and_rebuild.py --drop-only       # Only drop schemas
    python reset_and_rebuild.py --build-only      # Only build schemas
    python reset_and_rebuild.py --test            # Test connections first
"""

import sys
import os
import argparse
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv
from typing import List

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from src.nfl.database import PostgreSQLManager


def setup_logging():
    """Configure logging for the reset script."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level="INFO"
    )


def test_database_connection() -> bool:
    """Test if we can connect to the database."""
    try:
        with PostgreSQLManager() as db:
            result = db.fetch_one("SELECT version();")
            if result:
                logger.info(f"✅ Database connection successful!")
                logger.info(f"PostgreSQL version: {result[0]}")
                return True
            else:
                logger.error("❌ Database connection failed - no version info")
                return False
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def get_existing_schemas() -> List[str]:
    """Get list of existing sport schemas."""
    sport_schemas = ['nfl', 'nba', 'nhl', 'ncaaf', 'ncaab']
    existing_schemas = []
    
    try:
        with PostgreSQLManager() as db:
            for schema in sport_schemas:
                result = db.fetch_one(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                    (schema,)
                )
                if result:
                    existing_schemas.append(schema)
                    
    except Exception as e:
        logger.error(f"Failed to check existing schemas: {e}")
        
    return existing_schemas


def get_schema_stats(schema: str) -> dict:
    """Get statistics for a schema."""
    stats = {
        'tables': 0,
        'indexes': 0,
        'views': 0,
        'records': 0
    }
    
    try:
        with PostgreSQLManager() as db:
            # Count tables
            tables_result = db.fetch_all(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                """,
                (schema,)
            )
            stats['tables'] = len(tables_result) if tables_result else 0
            
            # Count views
            views_result = db.fetch_all(
                """
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = %s
                """,
                (schema,)
            )
            stats['views'] = len(views_result) if views_result else 0
            
            # Count indexes
            indexes_result = db.fetch_all(
                """
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = %s
                """,
                (schema,)
            )
            stats['indexes'] = len(indexes_result) if indexes_result else 0
            
            # Count records in game_logs table if it exists
            try:
                records_result = db.fetch_one(f"SELECT COUNT(*) FROM {schema}.game_logs")
                stats['records'] = records_result[0] if records_result else 0
            except:
                stats['records'] = 0
                
    except Exception as e:
        logger.warning(f"Failed to get stats for schema {schema}: {e}")
        
    return stats


def drop_all_sport_schemas() -> bool:
    """Drop all sport-related schemas."""
    sport_schemas = ['nfl', 'nba', 'nhl', 'ncaaf', 'ncaab']
    existing_schemas = get_existing_schemas()
    
    if not existing_schemas:
        logger.info("🔍 No sport schemas found to drop")
        return True
    
    logger.info(f"🗑️  Dropping {len(existing_schemas)} sport schemas...")
    
    try:
        with PostgreSQLManager() as db:
            for schema in existing_schemas:
                # Get stats before dropping
                stats = get_schema_stats(schema)
                logger.info(f"   📊 {schema.upper()}: {stats['tables']} tables, {stats['indexes']} indexes, {stats['records']} records")
                
                # Drop the schema
                logger.info(f"   🗑️  Dropping schema: {schema}")
                db.execute_sql(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
                logger.info(f"   ✅ Schema {schema} dropped successfully")
        
        logger.info(f"🎯 All {len(existing_schemas)} sport schemas dropped successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to drop schemas: {e}")
        return False


def build_all_sport_schemas() -> bool:
    """Build all sport schemas from scratch."""
    logger.info("🏗️  Building all sport schemas from scratch...")
    
    try:
        # Import the multi-sport manager
        from multi_sport_database import MultiSportDatabaseManager
        
        manager = MultiSportDatabaseManager()
        
        # Setup all sports
        success = manager.setup_all_sports()
        
        if success:
            logger.info("🎉 All sport schemas built successfully!")
            return True
        else:
            logger.error("❌ Failed to build some sport schemas")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to build sport schemas: {e}")
        return False


def verify_rebuild() -> bool:
    """Verify that the rebuild was successful."""
    logger.info("🔍 Verifying rebuild results...")
    
    sport_schemas = ['nfl', 'nba', 'nhl', 'ncaaf', 'ncaab']
    success_count = 0
    
    try:
        with PostgreSQLManager() as db:
            for schema in sport_schemas:
                # Check if schema exists
                schema_result = db.fetch_one(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                    (schema,)
                )
                
                if schema_result:
                    # Check if game_logs table exists
                    table_result = db.fetch_one(
                        """
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = 'game_logs'
                        """,
                        (schema,)
                    )
                    
                    if table_result:
                        # Get table stats
                        stats = get_schema_stats(schema)
                        logger.info(f"   ✅ {schema.upper()}: Schema ✓, Table ✓, {stats['indexes']} indexes, {stats['views']} views")
                        success_count += 1
                    else:
                        logger.error(f"   ❌ {schema.upper()}: Schema ✓, Table ✗")
                else:
                    logger.error(f"   ❌ {schema.upper()}: Schema ✗")
        
        if success_count == len(sport_schemas):
            logger.info(f"🎯 Verification successful! All {success_count} sports are ready")
            return True
        else:
            logger.warning(f"⚠️  Verification partial: {success_count}/{len(sport_schemas)} sports verified")
            return False
            
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


def show_final_status():
    """Show final status of all sports."""
    logger.info("📊 Final Database Status:")
    
    sport_configs = {
        'nfl': 'NFL',
        'nba': 'NBA', 
        'nhl': 'NHL',
        'ncaaf': 'NCAA Football',
        'ncaab': 'NCAA Basketball'
    }
    
    try:
        with PostgreSQLManager() as db:
            for schema, display_name in sport_configs.items():
                # Check schema
                schema_exists = db.fetch_one(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                    (schema,)
                ) is not None
                
                # Check table
                table_exists = False
                record_count = 0
                
                if schema_exists:
                    table_exists = db.fetch_one(
                        """
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = 'game_logs'
                        """,
                        (schema,)
                    ) is not None
                    
                    if table_exists:
                        count_result = db.fetch_one(f"SELECT COUNT(*) FROM {schema}.game_logs")
                        record_count = count_result[0] if count_result else 0
                
                schema_status = "✅" if schema_exists else "❌"
                table_status = "✅" if table_exists else "❌"
                
                logger.info(f"   {display_name}:")
                logger.info(f"      Schema: {schema_status} ({schema})")
                logger.info(f"      Table:  {table_status} (game_logs)")
                logger.info(f"      Records: {record_count}")
                
    except Exception as e:
        logger.error(f"Failed to show final status: {e}")


def main():
    """Main function for the reset and rebuild script."""
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Reset and rebuild All Sports Reference database from scratch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
⚠️  WARNING: This will DELETE ALL DATA in sport schemas!

Examples:
    python reset_and_rebuild.py --test              # Test connection only
    python reset_and_rebuild.py --confirm           # Full reset and rebuild
    python reset_and_rebuild.py --drop-only         # Drop schemas only
    python reset_and_rebuild.py --build-only        # Build schemas only
        """
    )
    
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm full reset and rebuild (DELETES ALL DATA!)'
    )
    
    parser.add_argument(
        '--drop-only',
        action='store_true',
        help='Only drop existing schemas'
    )
    
    parser.add_argument(
        '--build-only',
        action='store_true',
        help='Only build schemas (assumes clean database)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test database connection only'
    )
    
    args = parser.parse_args()
    
    logger.info("🏈🏀🏒 All Sports Reference - Database Reset & Rebuild")
    logger.info("=" * 60)
    
    # Test database connection first
    if not test_database_connection():
        logger.error("Cannot proceed without database connection")
        sys.exit(1)
    
    if args.test:
        logger.info("✅ Database connection test completed successfully!")
        show_final_status()
        return
    
    if args.drop_only:
        logger.warning("⚠️  DROP-ONLY MODE: This will delete all sport schema data!")
        input("Press Enter to continue or Ctrl+C to cancel...")
        
        if drop_all_sport_schemas():
            logger.info("🎯 Drop operation completed successfully!")
        else:
            logger.error("❌ Drop operation failed!")
            sys.exit(1)
        return
    
    if args.build_only:
        logger.info("🏗️  BUILD-ONLY MODE: Creating all sport schemas...")
        
        if build_all_sport_schemas():
            verify_rebuild()
            show_final_status()
            logger.info("🎯 Build operation completed successfully!")
        else:
            logger.error("❌ Build operation failed!")
            sys.exit(1)
        return
    
    if args.confirm:
        logger.warning("⚠️  FULL RESET MODE: This will DELETE ALL DATA and rebuild!")
        logger.warning("⚠️  All sport schemas and data will be permanently lost!")
        
        confirmation = input("Type 'DELETE ALL DATA' to confirm: ")
        if confirmation != "DELETE ALL DATA":
            logger.info("Operation cancelled by user")
            return
        
        logger.info("🚀 Starting full database reset and rebuild...")
        
        # Step 1: Drop all schemas
        logger.info("\n📍 Step 1: Dropping existing schemas...")
        if not drop_all_sport_schemas():
            logger.error("❌ Failed to drop schemas, aborting")
            sys.exit(1)
        
        # Step 2: Build all schemas
        logger.info("\n📍 Step 2: Building all sport schemas...")
        if not build_all_sport_schemas():
            logger.error("❌ Failed to build schemas, aborting")
            sys.exit(1)
        
        # Step 3: Verify rebuild
        logger.info("\n📍 Step 3: Verifying rebuild...")
        if verify_rebuild():
            logger.info("✅ Verification successful!")
        else:
            logger.warning("⚠️  Verification had issues")
        
        # Step 4: Show final status
        logger.info("\n📍 Step 4: Final status...")
        show_final_status()
        
        logger.info("\n🎉 Full database reset and rebuild completed!")
        logger.info("💡 You can now collect data using:")
        logger.info("   python example_data_collection.py --team KAN --year 2023")
        logger.info("   python multi_sport_database.py --status")
        
        return
    
    # Default action - show help
    parser.print_help()


if __name__ == "__main__":
    main()
