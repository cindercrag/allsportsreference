#!/usr/bin/env python3
"""
Database Migration Script
Migrates from 'nfl' user/database to 'sportsdata' user/database
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

# Current database configuration
OLD_CONFIG = {
    'host': '172.17.0.3',
    'database': 'nfl',
    'user': 'nfl',
    'password': 'g4br13l!',
    'port': 5432
}

# New database configuration
NEW_CONFIG = {
    'host': '172.17.0.3',
    'database': 'sportsdata',
    'user': 'sportsdata',
    'password': 'g4br13l!',
    'port': 5432
}

@contextmanager
def get_db_connection(config):
    """Get database connection context manager"""
    conn = None
    try:
        conn = psycopg2.connect(**config)
        yield conn
    finally:
        if conn:
            conn.close()

@contextmanager
def get_postgres_connection():
    """Get connection to postgres database for admin operations"""
    admin_config = {
        'host': '172.17.0.3',
        'database': 'postgres',
        'user': 'root',  # Using root superuser for admin operations
        'password': 'g4br13l!',
        'port': 5432
    }
    conn = None
    try:
        conn = psycopg2.connect(**admin_config)
        conn.autocommit = True  # Required for CREATE DATABASE/USER
        yield conn
    finally:
        if conn:
            conn.close()

def create_new_user_and_database():
    """Create new sportsdata user and database"""
    logger.info("🔨 Creating new user and database...")
    
    with get_postgres_connection() as conn:
        with conn.cursor() as cursor:
            try:
                # Create new user
                logger.info("👤 Creating user 'sportsdata'...")
                cursor.execute(f"""
                    CREATE USER sportsdata WITH PASSWORD '{NEW_CONFIG['password']}'
                """)
                logger.info("✅ User 'sportsdata' created")
                
                # Create new database
                logger.info("🗄️  Creating database 'sportsdata'...")
                cursor.execute("""
                    CREATE DATABASE sportsdata 
                    WITH OWNER sportsdata 
                    ENCODING 'UTF8'
                """)
                logger.info("✅ Database 'sportsdata' created")
                
            except psycopg2.Error as e:
                if "already exists" in str(e):
                    logger.warning(f"⚠️  Resource already exists: {e}")
                else:
                    raise

def dump_and_restore_data():
    """Dump data from old database and restore to new database"""
    logger.info("📦 Migrating data from 'nfl' to 'sportsdata'...")
    
    dump_file = "/tmp/nfl_data_dump.sql"
    
    try:
        # Dump existing data
        logger.info("📤 Dumping data from 'nfl' database...")
        dump_cmd = [
            "pg_dump",
            f"--host={OLD_CONFIG['host']}",
            f"--port={OLD_CONFIG['port']}",
            f"--username={OLD_CONFIG['user']}",
            f"--dbname={OLD_CONFIG['database']}",
            "--no-password",
            "--verbose",
            "--clean",
            "--if-exists",
            f"--file={dump_file}"
        ]
        
        env = {"PGPASSWORD": OLD_CONFIG['password']}
        result = subprocess.run(dump_cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ Dump failed: {result.stderr}")
            return False
        
        logger.info("✅ Data dumped successfully")
        
        # Restore to new database
        logger.info("📥 Restoring data to 'sportsdata' database...")
        restore_cmd = [
            "psql",
            f"--host={NEW_CONFIG['host']}",
            f"--port={NEW_CONFIG['port']}",
            f"--username={NEW_CONFIG['user']}",
            f"--dbname={NEW_CONFIG['database']}",
            "--no-password",
            f"--file={dump_file}"
        ]
        
        env = {"PGPASSWORD": NEW_CONFIG['password']}
        result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.warning(f"⚠️  Restore warnings: {result.stderr}")
            # Check if critical errors occurred
            if "FATAL" in result.stderr or "ERROR" in result.stderr:
                logger.error("❌ Critical restore errors occurred")
                return False
        
        logger.info("✅ Data restored successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False
    finally:
        # Clean up dump file
        try:
            import os
            if os.path.exists(dump_file):
                os.remove(dump_file)
                logger.info("🧹 Cleaned up dump file")
        except:
            pass

def verify_migration():
    """Verify the migration was successful"""
    logger.info("🔍 Verifying migration...")
    
    try:
        with get_db_connection(NEW_CONFIG) as conn:
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
                
                # Check all sport tables
                for schema in schemas:
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                    """, (schema,))
                    table_count = cursor.fetchone()[0]
                    logger.info(f"✅ {schema}: {table_count} tables")
                
        logger.info("✅ Migration verification successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def update_env_file():
    """Update the .env file with new database configuration"""
    logger.info("📝 Updating .env file...")
    
    env_file = "/allsportsreference/.env"
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Update database configuration
        content = content.replace('DB_NAME=nfl', 'DB_NAME=sportsdata')
        content = content.replace('DB_USER=nfl', 'DB_USER=sportsdata')
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        logger.info("✅ .env file updated")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to update .env file: {e}")
        return False

def main():
    """Main migration function"""
    logger.info("🚀 Database Migration: nfl → sportsdata")
    logger.info("=" * 50)
    
    try:
        # Step 1: Create new user and database
        create_new_user_and_database()
        
        # Step 2: Migrate data
        if not dump_and_restore_data():
            logger.error("❌ Data migration failed")
            return False
        
        # Step 3: Verify migration
        if not verify_migration():
            logger.error("❌ Migration verification failed")
            return False
        
        # Step 4: Update .env file
        if not update_env_file():
            logger.error("❌ Failed to update configuration")
            return False
        
        logger.info("\n🎉 Migration completed successfully!")
        logger.info("📊 New database configuration:")
        logger.info(f"   Database: {NEW_CONFIG['database']}")
        logger.info(f"   User: {NEW_CONFIG['user']}")
        logger.info(f"   Host: {NEW_CONFIG['host']}")
        
        logger.info("\n⚠️  Next steps:")
        logger.info("   1. Update all scripts to use new database config")
        logger.info("   2. Test data collection with new setup")
        logger.info("   3. Consider dropping old 'nfl' database when confident")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
