#!/usr/bin/env python3
"""
Demo script showing the enhanced NFL data scraping with Pydantic models.

This script demonstrates:
1. Loading NFL team data with descriptive column names
2. Converting to validated Pydantic models
3. Type-safe data access and validation
4. Advanced filtering and analysis
"""

from app.src.nfl.models import NFLTeamData, NFLColumnMapping, NFLConference
from app.src.nfl.teams import Teams


def main():
    print("🏈 NFL Data Analysis with Pydantic Models")
    print("=" * 50)
    
    # Load teams data
    print("\n📊 Loading 2024 NFL team data...")
    teams = Teams('2024')
    print(f"   Found {len(teams.team_data_dict)} teams")
    
    # Convert to Pydantic models
    print("\n🔄 Converting to validated Pydantic models...")
    models = teams.to_models()
    print(f"   Created {len(models)} validated models with type safety")
    
    # Display column mapping
    print("\n📋 Available data fields (with descriptive names):")
    preferred_columns = NFLColumnMapping.get_preferred_column_names()
    for i, col in enumerate(preferred_columns, 1):
        print(f"   {i:2}. {col}")
    
    # Conference analysis
    print("\n🏟️  Conference Analysis:")
    afc_teams = [m for m in models if m.conference == NFLConference.AFC]
    nfc_teams = [m for m in models if m.conference == NFLConference.NFC]
    
    print(f"   AFC Teams: {len(afc_teams)}")
    print(f"   NFC Teams: {len(nfc_teams)}")
    
    # Top teams analysis
    print("\n🏆 Top 5 Teams by Simple Rating System (SRS):")
    top_teams = sorted(models, key=lambda x: x.simple_rating_system, reverse=True)[:5]
    for i, team in enumerate(top_teams, 1):
        print(f"   {i}. {team.team}: {team.simple_rating_system:.1f} SRS ({team.wins}-{team.losses})")
    
    # Playoff contenders (13+ wins)
    print("\n🎯 Playoff Contenders (13+ wins):")
    contenders = [m for m in models if m.wins >= 13]
    for team in sorted(contenders, key=lambda x: x.wins, reverse=True):
        pf_pa_ratio = team.points_for / team.points_allowed
        print(f"   {team.team}: {team.wins}-{team.losses} | "
              f"PF/PA: {team.points_for}/{team.points_allowed} (ratio: {pf_pa_ratio:.2f})")
    
    # Demonstrate model lookup
    print("\n🔍 Individual Team Lookup:")
    chiefs = teams.get_model_by_abbrev('KAN')
    if chiefs:
        print(f"   Team: {chiefs.team}")
        print(f"   Record: {chiefs.wins}-{chiefs.losses} ({chiefs.win_loss_percentage:.3f})")
        print(f"   Conference: {chiefs.conference.value}")
        print(f"   Points For: {chiefs.points_for}")
        print(f"   Points Allowed: {chiefs.points_allowed}")
        print(f"   Point Differential: {chiefs.points_differential:+d}")
        print(f"   Simple Rating System: {chiefs.simple_rating_system}")
    
    # Data validation demo
    print("\n✅ Pydantic Validation Features:")
    print("   ✓ Type safety: All numeric fields validated as integers/floats")
    print("   ✓ Field validation: Wins/losses must be non-negative")
    print("   ✓ Enum validation: Conference must be AFC or NFC")
    print("   ✓ Descriptive field names: Based on website mouse-over descriptions")
    print("   ✓ Automatic conversion: String numbers converted to appropriate types")
    
    print("\n🎉 Demo complete! The Pydantic integration provides:")
    print("   • Type-safe data access with validation")
    print("   • Descriptive field names from website tooltips")
    print("   • Easy data manipulation and analysis")
    print("   • Automatic data conversion and validation")
    print("   • Clean, maintainable code structure")


if __name__ == "__main__":
    main()
