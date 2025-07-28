#!/usr/bin/env python3
"""
Demo script showing PostgreSQL integration with Pydantic NFL models.

This script demonstrates:
1. Creating PostgreSQL tables from Pydantic models
2. Inserting validated data into the database
3. Querying data back as Pydantic models
4. Advanced database operations
"""

import logging
from app.src.nfl.teams import Teams
from app.src.nfl.database import (
    PostgreSQLManager, 
    create_nfl_teams_table, 
    insert_nfl_teams,
    query_nfl_teams
)
from app.src.nfl.models import NFLTeamData

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    print("🏈 NFL PostgreSQL Integration Demo")
    print("=" * 50)
    
    try:
        # Step 1: Load NFL team data
        print("\n📊 Loading 2024 NFL team data...")
        teams = Teams('2024')
        models = teams.to_models()
        print(f"   Loaded {len(models)} teams with Pydantic validation")
        
        # Step 2: Create database table from Pydantic model
        print("\n🗄️  Creating PostgreSQL table from Pydantic model...")
        
        # Show the generated SQL first
        with PostgreSQLManager() as db:
            create_sql = db.generate_create_table_sql(NFLTeamData, "nfl_teams")
            print("   Generated SQL:")
            print("   " + "\n   ".join(create_sql.split('\n')[:10]) + "...")
        
        # Create the table
        success = create_nfl_teams_table(drop_if_exists=True)
        if success:
            print("   ✅ Table created successfully")
        else:
            print("   ❌ Failed to create table")
            return
        
        # Step 3: Insert data into database
        print("\n💾 Inserting NFL team data into PostgreSQL...")
        rows_inserted = insert_nfl_teams(models, on_conflict="UPDATE")
        print(f"   ✅ Inserted/updated {rows_inserted} team records")
        
        # Step 4: Query data back as Pydantic models
        print("\n📋 Querying data from PostgreSQL...")
        
        # Query all teams
        all_teams = query_nfl_teams()
        print(f"   Retrieved {len(all_teams)} teams from database")
        
        # Query specific teams
        afc_teams = query_nfl_teams("conference = 'AFC'")
        nfc_teams = query_nfl_teams("conference = 'NFC'")
        print(f"   AFC Teams: {len(afc_teams)}")
        print(f"   NFC Teams: {len(nfc_teams)}")
        
        # Query playoff contenders
        contenders = query_nfl_teams("wins >= 13")
        print(f"   Playoff Contenders (13+ wins): {len(contenders)}")
        
        # Step 5: Show some query results
        print("\n🏆 Top Teams from Database:")
        top_teams = query_nfl_teams("wins >= 13 ORDER BY simple_rating_system DESC")
        for i, team in enumerate(top_teams[:5], 1):
            print(f"   {i}. {team.team}: {team.wins}-{team.losses} | SRS: {team.simple_rating_system}")
        
        # Step 6: Show data validation working
        print("\n✅ Database Integration Benefits:")
        print("   ✓ Type-safe data storage and retrieval")
        print("   ✓ Automatic table generation from Pydantic models")
        print("   ✓ Data validation on insert and query")
        print("   ✓ Structured query capabilities")
        print("   ✓ Automatic timestamping and indexing")
        
        # Step 7: Advanced query example
        print("\n🔍 Advanced Query Example:")
        with PostgreSQLManager() as db:
            cursor = db._connection.cursor()
            cursor.execute("""
                SELECT conference, 
                       COUNT(*) as team_count,
                       AVG(wins) as avg_wins,
                       AVG(simple_rating_system) as avg_srs
                FROM nfl_teams 
                GROUP BY conference
                ORDER BY avg_srs DESC
            """)
            results = cursor.fetchall()
            cursor.close()
            
            print("   Conference Statistics:")
            for row in results:
                conf, count, avg_wins, avg_srs = row
                print(f"     {conf}: {count} teams, {avg_wins:.1f} avg wins, {avg_srs:.1f} avg SRS")
        
        print("\n🎉 Demo completed successfully!")
        print("\n📝 Key Features Demonstrated:")
        print("   • Automatic table creation from Pydantic schema")
        print("   • Type-safe data insertion with validation") 
        print("   • Seamless conversion between database and Pydantic models")
        print("   • Advanced querying with PostgreSQL features")
        print("   • Proper indexing and performance optimization")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        print("\n💡 Make sure PostgreSQL is running and configured correctly")
        print("   Check your database connection settings in environment variables:")
        print("   - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")


if __name__ == "__main__":
    main()
