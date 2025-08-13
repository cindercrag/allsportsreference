#!/usr/bin/env python3
"""
Simple Database Rename Script
Renames 'nfl' database to 'sportsdata' and updates configuration
"""

import psycopg2
import logging
from contextlib import contextmanager
import subprocess
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': '172.17.0.3',
    'user': 'nfl',
    'password': 'g4br13l!',
    'port': 5432
}

@contextmanager
def get_postgres_connection():
    """Get connection to postgres database for admin operations"""
    admin_config = {**DB_CONFIG, 'database': 'postgres'}
    conn = None
    try:
        conn = psycopg2.connect(**admin_config)
        conn.autocommit = True
        yield conn
    finally:
        if conn:
            conn.close()

def check_database_exists(db_name):
    """Check if a database exists"""
    with get_postgres_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM pg_database WHERE datname = %s
            """, (db_name,))
            return cursor.fetchone() is not None

def rename_database():
    """Rename 'nfl' database to 'sportsdata'"""
    logger.info("🔄 Renaming database from 'nfl' to 'sportsdata'...")
    
    if check_database_exists('sportsdata'):
        logger.warning("⚠️  Database 'sportsdata' already exists")
        return True
    
    if not check_database_exists('nfl'):
        logger.error("❌ Source database 'nfl' does not exist")
        return False
    
    try:
        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                # Terminate any active connections to the database
                logger.info("🔌 Terminating active connections to 'nfl' database...")
                cursor.execute("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = 'nfl' AND pid <> pg_backend_pid()
                """)
                
                # Rename the database
                logger.info("📝 Renaming database...")
                cursor.execute('ALTER DATABASE nfl RENAME TO sportsdata')
                
        logger.info("✅ Database renamed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to rename database: {e}")
        return False

def verify_rename():
    """Verify the database was renamed successfully"""
    logger.info("🔍 Verifying database rename...")
    
    try:
        # Check new database exists and has our data
        config = {**DB_CONFIG, 'database': 'sportsdata'}
        conn = psycopg2.connect(**config)
        
        with conn.cursor() as cursor:
            # Check schemas
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name IN ('nfl', 'nba', 'nhl', 'ncaaf', 'ncaab')
                ORDER BY schema_name
            """)
            schemas = [row[0] for row in cursor.fetchall()]
            logger.info(f"✅ Found {len(schemas)} sport schemas: {schemas}")
            
            # Check NFL data
            if 'nfl' in schemas:
                cursor.execute("SELECT COUNT(*) FROM nfl.game_logs")
                count = cursor.fetchone()[0]
                logger.info(f"✅ NFL game_logs: {count} records")
        
        conn.close()
        
        # Verify old database no longer exists
        if not check_database_exists('nfl'):
            logger.info("✅ Old 'nfl' database no longer exists")
        else:
            logger.warning("⚠️  Old 'nfl' database still exists")
        
        logger.info("✅ Verification successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def update_env_file():
    """Update the .env file with new database name"""
    logger.info("📝 Updating .env file...")
    
    env_file = "/allsportsreference/.env"
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Update database name (keep user as 'nfl' for now)
        content = content.replace('DB_NAME=nfl', 'DB_NAME=sportsdata')
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        logger.info("✅ .env file updated")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to update .env file: {e}")
        return False

def update_scripts():
    """Update database configuration in our scripts"""
    logger.info("🔧 Updating script configurations...")
    
    files_to_update = [
        "/allsportsreference/multi_sport_database.py",
        "/allsportsreference/reset_and_rebuild.py",
        "/allsportsreference/cleanup_database.py",
        "/allsportsreference/example_data_collection.py"
    ]
    
    for file_path in files_to_update:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Update database name in configuration dictionaries
            content = content.replace("'database': 'nfl'", "'database': 'sportsdata'")
            content = content.replace('"database": "nfl"', '"database": "sportsdata"')
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            logger.info(f"✅ Updated {file_path}")
            
        except FileNotFoundError:
            logger.warning(f"⚠️  File not found: {file_path}")
        except Exception as e:
            logger.error(f"❌ Failed to update {file_path}: {e}")
    
    return True

def main():
    """Main rename function"""
    logger.info("🚀 Database Rename: nfl → sportsdata")
    logger.info("=" * 45)
    
    try:
        # Step 1: Rename database
        if not rename_database():
            logger.error("❌ Database rename failed")
            return False
        
        # Step 2: Verify rename
        if not verify_rename():
            logger.error("❌ Rename verification failed")
            return False
        
        # Step 3: Update .env file
        if not update_env_file():
            logger.error("❌ Failed to update .env file")
            return False
        
        # Step 4: Update scripts
        update_scripts()
        
        logger.info("\n🎉 Database rename completed successfully!")
        logger.info("📊 New configuration:")
        logger.info("   Database: sportsdata")
        logger.info("   User: nfl (unchanged)")
        logger.info("   Host: 172.17.0.3")
        
        logger.info("\n✅ Next steps:")
        logger.info("   1. Test connection with new database name")
        logger.info("   2. Verify data collection still works")
        logger.info("   3. All sport schemas preserved")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Rename failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
