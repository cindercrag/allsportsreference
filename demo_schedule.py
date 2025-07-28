#!/usr/bin/env python3
"""
Demo script showing how to use the NFL Schedule functionality
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from src.nfl.schedule import Schedule
from src.nfl.teams import Teams


def demo_schedule_usage():
    """Demonstrate the Schedule class usage."""
    print("🏈 NFL Schedule Functionality Demo")
    print("=" * 50)
    
    # Get some team abbreviations
    teams = Teams('2024')
    team_abbrevs = ['PHI', 'KC', 'BUF', 'NE']  # Eagles, Chiefs, Bills, Patriots
    
    for team_abbrev in team_abbrevs:
        print(f"\n📊 {team_abbrev} 2024 Schedule Summary")
        print("-" * 30)
        
        try:
            schedule = Schedule(team_abbrev, '2024')
            
            # Basic stats
            regular_season = schedule.get_regular_season_games()
            wins = schedule.get_wins()
            losses = schedule.get_losses()
            home_games = schedule.get_home_games()
            away_games = schedule.get_away_games()
            
            print(f"Total Games: {len(schedule)}")
            print(f"Regular Season: {len(regular_season)}")
            print(f"Record: {len(wins)}-{len(losses)}")
            print(f"Home/Away: {len(home_games)}/{len(away_games)}")
            
            # Show first win and first loss
            if wins:
                first_win = wins[0]
                week = first_win.get('Week', 'N/A')
                opp = first_win.get('Opponent', 'N/A')
                score = f"{first_win.get('Team_Score', 'N/A')}-{first_win.get('Opp_Score', 'N/A')}"
                print(f"First Win: Week {week} vs {opp} ({score})")
            
            if losses:
                first_loss = losses[0]
                week = first_loss.get('Week', 'N/A')
                opp = first_loss.get('Opponent', 'N/A')
                score = f"{first_loss.get('Team_Score', 'N/A')}-{first_loss.get('Opp_Score', 'N/A')}"
                print(f"First Loss: Week {week} vs {opp} ({score})")
                
        except Exception as e:
            print(f"❌ Error loading {team_abbrev}: {e}")

    print("\n💾 Example: Exporting Eagles schedule to CSV...")
    try:
        eagles = Schedule('PHI', '2024')
        csv_file = eagles.to_csv('eagles_2024_example.csv')
        print(f"✅ Exported to: {csv_file}")
        
        # Show some specific game queries
        print(f"\n🔍 Eagles Game Queries:")
        week_1 = eagles.get_game(1)
        if week_1:
            print(f"Week 1: {week_1.get('Date')} vs {week_1.get('Opponent')} ({week_1.get('Result')} {week_1.get('Team_Score')}-{week_1.get('Opp_Score')})")
        
        playoff_games = eagles.get_playoff_games()
        print(f"Playoff Games: {len(playoff_games)}")
        if playoff_games:
            for game in playoff_games[:2]:  # Show first 2 playoff games
                week = game.get('Week', 'N/A')
                opp = game.get('Opponent', 'N/A')
                result = game.get('Result', 'N/A')
                score = f"{game.get('Team_Score', 'N/A')}-{game.get('Opp_Score', 'N/A')}"
                print(f"  Playoff Week {week}: vs {opp} ({result} {score})")
        
    except Exception as e:
        print(f"❌ Error with Eagles example: {e}")
    
    print(f"\n✅ Demo complete! You can now use Schedule('TEAM', 'YEAR') to get any team's schedule.")


if __name__ == "__main__":
    demo_schedule_usage()
