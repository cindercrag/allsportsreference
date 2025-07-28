#!/usr/bin/env python3
"""
Test script to verify all NFL scraping functionality is working correctly.
"""

def test_teams():
    """Test the Teams class functionality."""
    print("🏈 Testing Teams class functionality...")
    
    try:
        from app.src.nfl.teams import Teams
        
        # Create Teams instance
        teams = Teams(2024)
        print(f"✅ Teams loaded: {len(teams.team_data_dict)} teams found")
        
        if not teams.team_data_dict:
            print("❌ No team data found")
            return False
        
        # Test team access
        eagles = teams.get_team('PHI')
        print(f"✅ Team access: {eagles.get('Team', 'Unknown')}")
        
        # Test DataFrame
        df = teams.to_dataframe()
        print(f"✅ DataFrame: {len(df)} rows, {len(df.columns)} columns")
        
        # Test CSV export
        filename = teams.to_csv()
        print(f"✅ CSV export: {filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Teams test failed: {e}")
        return False


def test_models():
    """Test Pydantic models functionality."""
    print("\n📊 Testing Pydantic models...")
    
    try:
        from app.src.nfl.teams import Teams
        
        teams = Teams(2024)
        models = teams.to_models()
        print(f"✅ Models created: {len(models)} models")
        
        if models:
            eagles = teams.get_model_by_abbrev('PHI')
            print(f"✅ Model access: {eagles.team} ({eagles.wins}-{eagles.losses})")
        
        return True
        
    except Exception as e:
        print(f"❌ Models test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Running NFL scraper functionality tests...\n")
    
    results = []
    results.append(test_teams())
    results.append(test_models())
    
    print(f"\n📋 Test Results:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Everything is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()
