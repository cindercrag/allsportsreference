#!/usr/bin/env python3
"""
Simple script to verify and explore the NFL database data.
Run this to see exactly what data we have collected.
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, 'app')

from src.nfl.database import PostgreSQLManager
from dotenv import load_dotenv

def main():
    """Main function to explore database data."""
    
    # Load environment variables
    script_dir = Path('.').absolute()
    env_path = script_dir / '.env'
    load_dotenv(env_path, override=True)
    
    print("🔍 NFL Database Data Verification")
    print("=" * 50)
    
    try:
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                
                # 1. Show available data summary
                print("\n📊 DATA SUMMARY:")
                tables = ['game_logs', 'game_summary', 'boxscore_scoring', 'boxscore_team_stats', 'boxscore_player_stats']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM nfl.{table}")
                    count = cursor.fetchone()[0]
                    print(f"   {table}: {count:,} records")
                
                # 2. Show seasons available
                print("\n📅 SEASONS AVAILABLE:")
                cursor.execute("""
                    SELECT season, COUNT(DISTINCT team) as teams, COUNT(*) as total_games
                    FROM nfl.game_logs 
                    GROUP BY season 
                    ORDER BY season DESC
                """)
                seasons = cursor.fetchall()
                
                for season in seasons:
                    print(f"   {season[0]}: {season[1]} teams, {season[2]} games")
                
                # 3. Show specific example - Chiefs 2024 games with scoring data
                print("\n🏈 CHIEFS 2024 GAMES WITH DETAILED SCORING:")
                cursor.execute("""
                    SELECT gl.week, gl.date, gl.opponent, gl.result, 
                           COUNT(bs.id) as scoring_events
                    FROM nfl.game_logs gl
                    LEFT JOIN nfl.boxscore_scoring bs ON gl.boxscore_id = bs.boxscore_id
                    WHERE gl.team = 'KAN' AND gl.season = 2024
                    GROUP BY gl.week, gl.date, gl.opponent, gl.result, gl.boxscore_id
                    ORDER BY gl.week
                """)
                games = cursor.fetchall()
                
                print("   Week | Date       | vs Opponent | Result | Scoring Events")
                print("   -----|------------|-------------|--------|---------------")
                for game in games:
                    week, date, opp, result, events = game
                    print(f"   {week:2}   | {date} | vs {opp:8} | {result:6} | {events:2} events")
                
                # 4. Show a specific game's detailed scoring
                print("\n🏆 SAMPLE GAME SCORING DETAILS (Chiefs vs Ravens Week 1):")
                cursor.execute("""
                    SELECT quarter, time_remaining, team, description, score_home, score_away
                    FROM nfl.boxscore_scoring 
                    WHERE boxscore_id = '202409050kan'
                    ORDER BY quarter, CASE 
                        WHEN time_remaining ~ '^[0-9]+:[0-9]+$' 
                        THEN CAST(SPLIT_PART(time_remaining, ':', 1) AS INT) * 60 + CAST(SPLIT_PART(time_remaining, ':', 2) AS INT)
                        ELSE 0 
                    END DESC
                """)
                scoring = cursor.fetchall()
                
                print("   Quarter | Time  | Team    | Play Description                        | Score")
                print("   --------|-------|---------|----------------------------------------|-------")
                for score in scoring:
                    q, time, team, desc, home, away = score
                    desc_short = desc[:35] + "..." if len(desc) > 35 else desc
                    print(f"   Q{q}      | {time:5} | {team:7} | {desc_short:38} | {home}-{away}")
                
                # 5. Show CSV export info
                print("\n📁 EXPORTED CSV FILES:")
                csv_dir = Path("data/nfl/2025")
                if csv_dir.exists():
                    for csv_file in csv_dir.glob("*.csv"):
                        size = csv_file.stat().st_size
                        print(f"   {csv_file.name}: {size:,} bytes")
                else:
                    print("   No CSV files found in data/nfl/2025/")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure PostgreSQL is running")
        print("   2. Check .env file for correct database credentials")
        print("   3. Verify the database schema exists")

if __name__ == "__main__":
    main()
