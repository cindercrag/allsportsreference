#!/usr/bin/env python3
"""
Database Setup Script for All Sports Reference

This script sets up the PostgreSQL database schemas and tables
required for storing NFL game log and boxscore data.

Usage:
    python setup_database.py                # Setup with default schema (nfl)
    python setup_database.py --schema=nfl   # Setup with custom schema
    python setup_database.py --reset        # Drop and recreate tables
    python setup_database.py --test         # Test database connection
"""

import sys
import os
import argparse
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load environment variables from the correct .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from src.nfl.database import (
    PostgreSQLManager, 
    setup_nfl_database_schema,
    create_nfl_game_log_table,
    create_nfl_boxscore_details_table
)


def setup_logging():
    """Configure logging for the setup script."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )


def test_database_connection():
    """Test if we can connect to the database."""
    try:
        with PostgreSQLManager() as db:
            result = db.fetch_all("SELECT version();")
            if result:
                logger.info(f"✅ Database connection successful!")
                logger.info(f"PostgreSQL version: {result[0][0]}")
                return True
            else:
                logger.error("❌ Database connection failed - no version info")
                return False
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def check_schema_exists(schema_name: str = "nfl") -> bool:
    """Check if the schema already exists."""
    try:
        with PostgreSQLManager() as db:
            result = db.fetch_all(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                (schema_name,)
            )
            return len(result) > 0
    except Exception as e:
        logger.error(f"Failed to check schema existence: {e}")
        return False


def check_tables_exist(schema_name: str = "nfl") -> dict:
    """Check which tables already exist in the schema."""
    tables = {
        'game_logs': False,
        'boxscore_details': False
    }
    
    try:
        with PostgreSQLManager() as db:
            for table_name in tables.keys():
                result = db.fetch_all(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = %s
                    """,
                    (schema_name, table_name)
                )
                tables[table_name] = len(result) > 0
                
    except Exception as e:
        logger.error(f"Failed to check table existence: {e}")
        
    return tables


def drop_schema(schema_name: str = "nfl"):
    """Drop the entire schema and all its contents."""
    try:
        with PostgreSQLManager() as db:
            logger.warning(f"🗑️  Dropping schema '{schema_name}' and all its contents...")
            db.execute_sql(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE;")
            logger.info(f"✅ Schema '{schema_name}' dropped successfully")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to drop schema: {e}")
        return False


def setup_database_schema(schema_name: str = "nfl", reset: bool = False):
    """Setup the complete database schema."""
    logger.info(f"🚀 Setting up database schema: {schema_name}")
    
    # Check if reset is requested
    if reset:
        if check_schema_exists(schema_name):
            drop_schema(schema_name)
    
    # Check current state
    schema_exists = check_schema_exists(schema_name)
    tables = check_tables_exist(schema_name) if schema_exists else {}
    
    logger.info(f"📊 Current state:")
    logger.info(f"   Schema '{schema_name}' exists: {schema_exists}")
    for table_name, exists in tables.items():
        logger.info(f"   Table '{table_name}' exists: {exists}")
    
    try:
        # Get all setup statements
        setup_statements = setup_nfl_database_schema(schema_name)
        
        # Execute each statement
        with PostgreSQLManager() as db:
            for i, sql_statement in enumerate(setup_statements, 1):
                logger.info(f"📝 Executing statement {i}/{len(setup_statements)}...")
                db.execute_sql(sql_statement)
                logger.info(f"✅ Statement {i} executed successfully")
        
        # Verify the setup
        logger.info("🔍 Verifying setup...")
        final_tables = check_tables_exist(schema_name)
        
        success = True
        for table_name, exists in final_tables.items():
            if exists:
                logger.info(f"✅ Table '{schema_name}.{table_name}' created successfully")
            else:
                logger.error(f"❌ Table '{schema_name}.{table_name}' was not created")
                success = False
        
        if success:
            logger.info(f"🎉 Database schema '{schema_name}' setup completed successfully!")
            
            # Show some additional info
            with PostgreSQLManager() as db:
                # Count indexes
                index_result = db.fetch_all(
                    """
                    SELECT COUNT(*) as index_count
                    FROM pg_indexes 
                    WHERE schemaname = %s
                    """,
                    (schema_name,)
                )
                
                if index_result:
                    index_count = index_result[0][0]
                    logger.info(f"📈 Created {index_count} indexes for optimal performance")
                
                # List views
                view_result = db.fetch_all(
                    """
                    SELECT table_name
                    FROM information_schema.views 
                    WHERE table_schema = %s
                    """,
                    (schema_name,)
                )
                
                if view_result:
                    views = [row[0] for row in view_result]
                    logger.info(f"👁️  Created views: {', '.join(views)}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Failed to setup database schema: {e}")
        return False


def show_schema_info(schema_name: str = "nfl"):
    """Show detailed information about the current schema."""
    logger.info(f"📋 Schema information for '{schema_name}':")
    
    try:
        with PostgreSQLManager() as db:
            # Get tables
            tables_result = db.fetch_all(
                """
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_schema = %s
                ORDER BY table_name
                """,
                (schema_name,)
            )
            
            if tables_result:
                logger.info(f"📦 Tables and Views:")
                for table_name, table_type in tables_result:
                    logger.info(f"   - {table_name} ({table_type})")
            
            # Get indexes
            indexes_result = db.fetch_all(
                """
                SELECT indexname, tablename
                FROM pg_indexes 
                WHERE schemaname = %s
                ORDER BY tablename, indexname
                """,
                (schema_name,)
            )
            
            if indexes_result:
                logger.info(f"🔍 Indexes:")
                current_table = None
                for index_name, table_name in indexes_result:
                    if table_name != current_table:
                        logger.info(f"   {table_name}:")
                        current_table = table_name
                    logger.info(f"     - {index_name}")
            
            # Get constraints
            constraints_result = db.fetch_all(
                """
                SELECT constraint_name, table_name, constraint_type
                FROM information_schema.table_constraints 
                WHERE table_schema = %s
                ORDER BY table_name, constraint_type
                """,
                (schema_name,)
            )
            
            if constraints_result:
                logger.info(f"🔗 Constraints:")
                current_table = None
                for constraint_name, table_name, constraint_type in constraints_result:
                    if table_name != current_table:
                        logger.info(f"   {table_name}:")
                        current_table = table_name
                    logger.info(f"     - {constraint_name} ({constraint_type})")
                    
    except Exception as e:
        logger.error(f"Failed to get schema info: {e}")


def main():
    """Main function for the database setup script."""
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Setup PostgreSQL database schema for All Sports Reference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python setup_database.py                    # Setup default schema
    python setup_database.py --schema custom    # Setup custom schema
    python setup_database.py --reset            # Reset and recreate
    python setup_database.py --test             # Test connection only
    python setup_database.py --info             # Show schema info
        """
    )
    
    parser.add_argument(
        '--schema',
        type=str,
        default='nfl',
        help='Database schema name (default: nfl)'
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Drop and recreate the schema'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test database connection only'
    )
    
    parser.add_argument(
        '--info',
        action='store_true',
        help='Show information about existing schema'
    )
    
    args = parser.parse_args()
    
    logger.info("🏈 All Sports Reference - Database Setup")
    logger.info("=" * 50)
    
    # Test database connection first
    if not test_database_connection():
        logger.error("Cannot proceed without database connection")
        sys.exit(1)
    
    # Handle different modes
    if args.test:
        logger.info("✅ Database connection test completed successfully!")
        return
    
    if args.info:
        show_schema_info(args.schema)
        return
    
    # Setup the schema
    success = setup_database_schema(args.schema, args.reset)
    
    if success:
        logger.info("🎯 Setup completed! You can now:")
        logger.info("   1. Run the main application to collect data")
        logger.info("   2. Use the database functions to insert game logs")
        logger.info("   3. Query the database for analysis")
        logger.info("")
        logger.info("Example queries:")
        logger.info(f"   SELECT * FROM {args.schema}.game_logs LIMIT 5;")
        logger.info(f"   SELECT * FROM {args.schema}.game_summary WHERE season = 2024;")
        sys.exit(0)
    else:
        logger.error("❌ Setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
