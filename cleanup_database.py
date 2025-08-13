#!/usr/bin/env python3
"""
Database Cleanup Script
Removes extra schemas and keeps only the 5 sport schemas we need
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

# Database configuration
DB_CONFIG = {
    'host': '172.17.0.3',
    'database': 'nfl',
    'user': 'nfl',
    'password': 'g4br13l!',
    'port': 5432
}

# Sport schemas we want to keep
SPORT_SCHEMAS = {'nfl', 'nba', 'nhl', 'ncaaf', 'ncaab'}

@contextmanager
def get_db_connection():
    """Get database connection context manager"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    finally:
        if conn:
            conn.close()

def get_current_schemas():
    """Get list of current schemas (excluding system schemas)"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'public')
                ORDER BY schema_name
            """)
            return [row[0] for row in cursor.fetchall()]

def drop_extra_schemas():
    """Drop all schemas except the 5 sport schemas"""
    current_schemas = get_current_schemas()
    extra_schemas = [schema for schema in current_schemas if schema not in SPORT_SCHEMAS]
    
    if not extra_schemas:
        logger.info("✅ No extra schemas found - database is clean")
        return
    
    logger.info(f"🗑️  Found {len(extra_schemas)} extra schemas to remove:")
    for schema in extra_schemas:
        logger.info(f"   - {schema}")
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            for schema in extra_schemas:
                try:
                    logger.info(f"🗑️  Dropping schema: {schema}")
                    cursor.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
                    conn.commit()
                    logger.info(f"✅ Successfully dropped schema: {schema}")
                except Exception as e:
                    logger.error(f"❌ Error dropping schema {schema}: {e}")
                    conn.rollback()

def verify_cleanup():
    """Verify only sport schemas remain"""
    current_schemas = get_current_schemas()
    logger.info(f"📊 Current schemas after cleanup: {len(current_schemas)}")
    
    for schema in sorted(current_schemas):
        if schema in SPORT_SCHEMAS:
            logger.info(f"   ✅ {schema} (sport schema)")
        else:
            logger.warning(f"   ⚠️  {schema} (unexpected schema)")
    
    # Check table counts
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            for schema in sorted(current_schemas):
                if schema in SPORT_SCHEMAS:
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                    """, (schema,))
                    table_count = cursor.fetchone()[0]
                    logger.info(f"   📊 {schema}: {table_count} tables")

def main():
    """Main cleanup function"""
    logger.info("🧹 Database Cleanup - Removing Extra Schemas")
    logger.info("=" * 50)
    
    try:
        # Show current state
        current_schemas = get_current_schemas()
        logger.info(f"📊 Current schemas: {len(current_schemas)}")
        logger.info(f"🎯 Target schemas: {sorted(SPORT_SCHEMAS)}")
        
        # Clean up extra schemas
        drop_extra_schemas()
        
        # Verify cleanup
        logger.info("\n🔍 Verification:")
        verify_cleanup()
        
        logger.info("\n✅ Database cleanup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database cleanup failed: {e}")
        raise

if __name__ == "__main__":
    main()
