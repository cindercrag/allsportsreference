#!/usr/bin/env python3
"""
Test script for NFL Schedule functionality
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from src.nfl.schedule import Schedule
from src.nfl.teams import Teams


def test_schedule_functionality():
    """Test the Schedule class functionality."""
    print("🏈 Testing NFL Schedule Functionality")
    print("=" * 50)
    
    # First, let's get a team abbreviation from our working Teams class
    print("📋 Loading teams for 2024...")
    teams = Teams('2024')
    print(f"✅ Teams loaded: {len(teams.team_data_dict)} teams found")
    
    # Get Eagles team abbreviation (we know this works)
    eagles_abbrev = 'PHI'
    print(f"\n🦅 Testing schedule for {eagles_abbrev} (Philadelphia Eagles)")
    
    try:
        # Test Schedule creation
        schedule = Schedule(eagles_abbrev, '2024')
        print(f"✅ Schedule loaded: {len(schedule)} games found")
        
        if len(schedule) > 0:
            print(f"\n📊 Schedule Details:")
            print(f"   Team: {schedule.team_abbrev}")
            print(f"   Year: {schedule.year}")
            print(f"   Total Games: {len(schedule)}")
            
            # Test some methods
            regular_season = schedule.get_regular_season_games()
            playoff_games = schedule.get_playoff_games()
            wins = schedule.get_wins()
            losses = schedule.get_losses()
            home_games = schedule.get_home_games()
            away_games = schedule.get_away_games()
            
            print(f"   Regular Season: {len(regular_season)} games")
            print(f"   Playoff Games: {len(playoff_games)} games")
            print(f"   Wins: {len(wins)} games")
            print(f"   Losses: {len(losses)} games")
            print(f"   Home Games: {len(home_games)} games")
            print(f"   Away Games: {len(away_games)} games")
            
            # Show first few games
            print(f"\n📅 First 3 games:")
            for i, game in enumerate(schedule[:3]):
                week = game.get('Week', 'N/A')
                date = game.get('Date', 'N/A')
                opp = game.get('Opponent', 'N/A')
                result = game.get('Result', 'N/A')
                team_score = game.get('Team_Score', 'N/A')
                opp_score = game.get('Opp_Score', 'N/A')
                location = game.get('Location', '')
                location_str = 'vs' if location != '@' else '@'
                print(f"   Week {week}: {date} {location_str} {opp} ({result} {team_score}-{opp_score})")
            
            # Test DataFrame conversion
            print(f"\n📊 Testing DataFrame conversion...")
            df = schedule.to_dataframe()
            print(f"✅ DataFrame: {len(df)} rows, {len(df.columns)} columns")
            if len(df.columns) > 0:
                print(f"   Columns: {list(df.columns)[:10]}{'...' if len(df.columns) > 10 else ''}")
            
            # Test CSV export
            print(f"\n💾 Testing CSV export...")
            csv_path = schedule.to_csv()
            print(f"✅ CSV export: {csv_path}")
            
            # Test Pydantic models
            print(f"\n🔧 Testing Pydantic models...")
            models = schedule.to_models()
            print(f"✅ Models created: {len(models)} models")
            
            if models:
                first_model = models[0]
                print(f"   First game model: Week {first_model.week}, {first_model.opponent}")
        
        else:
            print("❌ No games found in schedule")
            return False
        
    except Exception as e:
        print(f"❌ Error testing schedule: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Main test function."""
    try:
        success = test_schedule_functionality()
        
        print(f"\n📋 Test Results:")
        if success:
            print("✅ Passed: Schedule functionality working correctly")
            print("🎉 All tests passed! Schedule is working correctly.")
        else:
            print("❌ Failed: Schedule functionality has issues")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
