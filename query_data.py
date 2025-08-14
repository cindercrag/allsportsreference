#!/usr/bin/env python3
"""
Interactive database query script.
Use this to run your own custom queries against the NFL database.
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, 'app')

from src.nfl.database import PostgreSQLManager
from dotenv import load_dotenv

def run_query(query, description="Custom Query"):
    """Run a custom SQL query and display results."""
    
    # Load environment variables
    script_dir = Path('.').absolute()
    env_path = script_dir / '.env'
    load_dotenv(env_path, override=True)
    
    print(f"🔍 {description}")
    print("=" * 60)
    
    try:
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
                if results:
                    # Get column names
                    columns = [desc[0] for desc in cursor.description]
                    
                    # Print header
                    header = " | ".join(f"{col:15}" for col in columns)
                    print(header)
                    print("-" * len(header))
                    
                    # Print data
                    for row in results:
                        row_str = " | ".join(f"{str(val):15}" for val in row)
                        print(row_str)
                    
                    print(f"\n📊 Total records: {len(results)}")
                else:
                    print("No results found.")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function with example queries."""
    
    print("🎯 NFL DATABASE QUERY EXAMPLES")
    print("=" * 50)
    
    # Example 1: All games with scores
    query1 = """
        SELECT 
            gl.season,
            gl.week,
            gl.team,
            gl.opponent,
            gl.result,
            COUNT(bs.id) as scoring_plays
        FROM nfl.game_logs gl
        LEFT JOIN nfl.boxscore_scoring bs ON gl.boxscore_id = bs.boxscore_id
        GROUP BY gl.season, gl.week, gl.team, gl.opponent, gl.result, gl.boxscore_id
        ORDER BY gl.season DESC, gl.week
        LIMIT 10
    """
    run_query(query1, "Games with Scoring Data")
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Scoring by quarter
    query2 = """
        SELECT 
            quarter,
            COUNT(*) as total_scores,
            COUNT(CASE WHEN team LIKE '%Chiefs%' OR team = 'KAN' THEN 1 END) as chiefs_scores
        FROM nfl.boxscore_scoring
        GROUP BY quarter
        ORDER BY quarter
    """
    run_query(query2, "Scoring Events by Quarter")
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: Team stats summary
    query3 = """
        SELECT 
            team,
            COUNT(*) as games_with_stats,
            AVG(first_downs) as avg_first_downs,
            AVG(total_yards) as avg_total_yards,
            SUM(turnovers) as total_turnovers
        FROM nfl.boxscore_team_stats
        GROUP BY team
        ORDER BY team
    """
    run_query(query3, "Team Statistics Summary")

if __name__ == "__main__":
    main()
    
    print("\n💡 To run your own queries, use:")
    print("   python -c \"")
    print("   import sys; sys.path.insert(0, 'app')")
    print("   from src.nfl.database import PostgreSQLManager")
    print("   from dotenv import load_dotenv; load_dotenv('.env')")
    print("   with PostgreSQLManager() as db:")
    print("       cursor = db._connection.cursor()")
    print("       cursor.execute('YOUR SQL QUERY HERE')")
    print("       print(cursor.fetchall())")
    print("   \"")
