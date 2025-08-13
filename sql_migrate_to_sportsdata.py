#!/usr/bin/env python3
"""
Direct SQL Migration Script
Migrates data using direct SQL commands instead of pg_dump
"""

import psycopg2
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Database configurations
OLD_CONFIG = {
    'host': '172.17.0.3',
    'database': 'nfl',
    'user': 'nfl',
    'password': 'g4br13l!',
    'port': 5432
}

NEW_CONFIG = {
    'host': '172.17.0.3',
    'database': 'sportsdata',
    'user': 'sportsdata',
    'password': 'g4br13l!',
    'port': 5432
}

ADMIN_CONFIG = {
    'host': '172.17.0.3',
    'database': 'postgres',
    'user': 'root',
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
def get_admin_connection():
    """Get admin connection with autocommit"""
    conn = None
    try:
        conn = psycopg2.connect(**ADMIN_CONFIG)
        conn.autocommit = True
        yield conn
    finally:
        if conn:
            conn.close()

def create_new_database_and_user():
    """Create new database and user"""
    logger.info("🔨 Creating new database and user...")
    
    with get_admin_connection() as conn:
        with conn.cursor() as cursor:
            try:
                # Create user
                logger.info("👤 Creating user 'sportsdata'...")
                cursor.execute(f"""
                    CREATE USER sportsdata WITH PASSWORD '{NEW_CONFIG['password']}'
                """)
                logger.info("✅ User 'sportsdata' created")
                
                # Create database
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

def migrate_schemas_and_data():
    """Migrate schemas and data using direct SQL"""
    logger.info("📦 Migrating schemas and data...")
    
    # Sport schemas to migrate
    sport_schemas = ['nfl', 'nba', 'nhl', 'ncaaf', 'ncaab']
    
    try:
        # Get data from old database
        with get_db_connection(OLD_CONFIG) as old_conn:
            with old_conn.cursor() as old_cursor:
                
                # Connect to new database
                with get_db_connection(NEW_CONFIG) as new_conn:
                    with new_conn.cursor() as new_cursor:
                        
                        for schema in sport_schemas:
                            logger.info(f"🔄 Migrating schema: {schema}")
                            
                            # Create schema
                            new_cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                            
                            # Get tables in this schema
                            old_cursor.execute("""
                                SELECT table_name 
                                FROM information_schema.tables 
                                WHERE table_schema = %s
                            """, (schema,))
                            tables = [row[0] for row in old_cursor.fetchall()]
                            
                            for table in tables:
                                logger.info(f"📄 Migrating table: {schema}.{table}")
                                
                                # Get table definition
                                old_cursor.execute(f"""
                                    SELECT column_name, data_type, is_nullable, column_default
                                    FROM information_schema.columns 
                                    WHERE table_schema = %s AND table_name = %s
                                    ORDER BY ordinal_position
                                """, (schema, table))
                                columns = old_cursor.fetchall()
                                
                                # Create table
                                column_defs = []
                                for col_name, data_type, nullable, default in columns:
                                    col_def = f"{col_name} {data_type}"
                                    if nullable == 'NO':
                                        col_def += " NOT NULL"
                                    if default:
                                        col_def += f" DEFAULT {default}"
                                    column_defs.append(col_def)
                                
                                create_table_sql = f"""
                                    CREATE TABLE IF NOT EXISTS {schema}.{table} (
                                        {', '.join(column_defs)}
                                    )
                                """
                                new_cursor.execute(create_table_sql)
                                
                                # Copy data
                                old_cursor.execute(f"SELECT * FROM {schema}.{table}")
                                rows = old_cursor.fetchall()
                                
                                if rows:
                                    # Get column names
                                    col_names = [desc[0] for desc in old_cursor.description]
                                    placeholders = ', '.join(['%s'] * len(col_names))
                                    
                                    insert_sql = f"""
                                        INSERT INTO {schema}.{table} ({', '.join(col_names)})
                                        VALUES ({placeholders})
                                    """
                                    
                                    new_cursor.executemany(insert_sql, rows)
                                    logger.info(f"✅ Copied {len(rows)} rows to {schema}.{table}")
                                
                        new_conn.commit()
                        logger.info("✅ All data migrated successfully")
                        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

def verify_migration():
    """Verify migration was successful"""
    logger.info("🔍 Verifying migration...")
    
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
            
            # Check NFL data specifically
            if 'nfl' in schemas:
                cursor.execute("SELECT COUNT(*) FROM nfl.game_logs")
                count = cursor.fetchone()[0]
                logger.info(f"✅ NFL game_logs: {count} records")
                
                if count > 0:
                    cursor.execute("SELECT team, season, COUNT(*) FROM nfl.game_logs GROUP BY team, season")
                    team_data = cursor.fetchall()
                    for team, season, games in team_data:
                        logger.info(f"   📊 {team} {season}: {games} games")

def update_configuration_files():
    """Update all configuration files"""
    logger.info("📝 Updating configuration files...")
    
    # Update .env file
    env_file = "/allsportsreference/.env"
    with open(env_file, 'r') as f:
        content = f.read()
    
    content = content.replace('DB_NAME=nfl', 'DB_NAME=sportsdata')
    content = content.replace('DB_USER=nfl', 'DB_USER=sportsdata')
    
    with open(env_file, 'w') as f:
        f.write(content)
    
    logger.info("✅ Updated .env file")
    
    # Update script files
    script_files = [
        "/allsportsreference/multi_sport_database.py",
        "/allsportsreference/reset_and_rebuild.py",
        "/allsportsreference/cleanup_database.py",
        "/allsportsreference/example_data_collection.py"
    ]
    
    for file_path in script_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Update database configurations
            content = content.replace("'database': 'nfl'", "'database': 'sportsdata'")
            content = content.replace("'user': 'nfl'", "'user': 'sportsdata'")
            content = content.replace('"database": "nfl"', '"database": "sportsdata"')
            content = content.replace('"user": "nfl"', '"user": "sportsdata"')
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            logger.info(f"✅ Updated {file_path}")
            
        except FileNotFoundError:
            logger.warning(f"⚠️  File not found: {file_path}")

def main():
    """Main migration function"""
    logger.info("🚀 Database Migration: nfl → sportsdata")
    logger.info("=" * 50)
    
    try:
        # Step 1: Create new database and user
        create_new_database_and_user()
        
        # Step 2: Migrate data
        migrate_schemas_and_data()
        
        # Step 3: Verify migration
        verify_migration()
        
        # Step 4: Update configuration files
        update_configuration_files()
        
        logger.info("\n🎉 Migration completed successfully!")
        logger.info("📊 New configuration:")
        logger.info(f"   Database: {NEW_CONFIG['database']}")
        logger.info(f"   User: {NEW_CONFIG['user']}")
        logger.info(f"   Host: {NEW_CONFIG['host']}")
        
        logger.info("\n✅ Ready to use new 'sportsdata' database!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()
