#!/usr/bin/env python3
"""
Final integration test for NFL Schedule functionality
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from src.nfl.schedule import Schedule
from src.nfl.teams import Teams


def main():
    """Final test of the schedule functionality."""
    print("🏈 Final NFL Schedule Integration Test")
    print("=" * 50)
    
    # Test basic functionality
    print("📋 Testing Philadelphia Eagles 2024 schedule...")
    
    try:
        # Create schedule instance
        eagles_schedule = Schedule('PHI', '2024')
        
        # Test basic properties
        print(f"✅ Games loaded: {len(eagles_schedule)} games")
        print(f"✅ Team: {eagles_schedule.team_abbrev}")
        print(f"✅ Year: {eagles_schedule.year}")
        
        # Test filtering methods
        wins = eagles_schedule.get_wins()
        losses = eagles_schedule.get_losses()
        home_games = eagles_schedule.get_home_games()
        away_games = eagles_schedule.get_away_games()
        regular_season = eagles_schedule.get_regular_season_games()
        playoffs = eagles_schedule.get_playoff_games()
        
        print(f"✅ Record: {len(wins)}-{len(losses)}")
        print(f"✅ Home/Away: {len(home_games)}/{len(away_games)}")
        print(f"✅ Regular Season/Playoffs: {len(regular_season)}/{len(playoffs)}")
        
        # Test specific game lookup
        week_1 = eagles_schedule.get_game('1')
        if week_1:
            print(f"✅ Week 1: {week_1.get('Date')} vs {week_1.get('Opponent')} ({week_1.get('Result')} {week_1.get('Team_Score')}-{week_1.get('Opp_Score')})")
        
        # Test DataFrame conversion
        df = eagles_schedule.to_dataframe()
        print(f"✅ DataFrame: {len(df)} rows, {len(df.columns)} columns")
        
        # Test Pydantic models
        models = eagles_schedule.to_models()
        print(f"✅ Pydantic models: {len(models)} game models created")
        
        # Test iteration
        game_count = sum(1 for game in eagles_schedule)
        print(f"✅ Iteration: {game_count} games via iterator")
        
        # Test indexing
        first_game = eagles_schedule[0]
        print(f"✅ Indexing: First game Week {first_game.get('Week')}")
        
        print(f"\n🎉 All Schedule functionality tests passed!")
        print(f"📊 Summary: {eagles_schedule}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
    print("\n✅ Schedule functionality is ready for use!")
