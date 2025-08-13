# Multi-Sport Database Management Guide

## 🏈🏀🏒 Overview

The All Sports Reference system now supports comprehensive multi-sport data management with dedicated database schemas for each sport. Each sport has tailored statistics, proper boxscore linking, and cross-sport analytics capabilities.

## ✅ Sports Currently Configured

| Sport | Schema | Status | Records | Specific Stats |
|-------|--------|--------|---------|----------------|
| **NFL** | `nfl` | ✅ Active | 33 games | Passing yards, rushing yards, touchdowns, penalties |
| **NBA** | `nba` | ✅ Ready | 0 games | Field goals, 3-pointers, rebounds, assists, steals |
| **NHL** | `nhl` | ✅ Ready | 0 games | Goals, assists, shots, saves, power plays, penalties |
| **NCAA Football** | `ncaaf` | ✅ Ready | 0 games | Same as NFL with college-specific adaptations |
| **NCAA Basketball** | `ncaab` | ✅ Ready | 0 games | Same as NBA with college-specific adaptations |

## 🛠️ Management Commands

### Database Setup
```bash
# Setup all sports at once
python multi_sport_database.py --setup-all

# Setup individual sports
python multi_sport_database.py --setup-sport nba
python multi_sport_database.py --setup-sport nhl
python multi_sport_database.py --setup-sport ncaaf
python multi_sport_database.py --setup-sport ncaab

# Check status
python multi_sport_database.py --status
python multi_sport_database.py --list-sports
```

### Data Collection Examples
```bash
# NFL data collection (already working)
python example_data_collection.py --team KAN --year 2023
python example_data_collection.py --team BUF --year 2023

# For other sports, you'll need to adapt the collection scripts
# based on existing modules in app/src/[sport]/
```

## 📊 Database Structure

### Common Fields (All Sports)
- `boxscore_id` - Unique game identifier for linking
- `team`, `opponent` - Team identifiers
- `date`, `season` - Temporal information
- `result`, `team_score`, `opp_score` - Game outcome
- `location` - Home/away indicator

### Sport-Specific Fields

#### NFL (`nfl.game_logs`)
```sql
-- Passing statistics
pass_cmp, pass_att, pass_cmp_pct, pass_yds, pass_td, pass_rate, pass_sk, pass_sk_yds

-- Rushing statistics  
rush_att, rush_yds, rush_td, rush_ypc

-- Total offense
tot_plays, tot_yds, tot_ypp

-- Turnovers & penalties
to_fumble, to_int, penalty_count, penalty_yds

-- Down conversions
third_down_success, third_down_att, fourth_down_success, fourth_down_att
```

#### NBA (`nba.game_logs`)
```sql
-- Shooting statistics
fg_made, fg_att, fg_pct, fg3_made, fg3_att, fg3_pct, ft_made, ft_att, ft_pct

-- Rebounds
oreb, dreb, treb

-- Other basketball stats
ast, stl, blk, tov, pf

-- Advanced metrics
pace, efg_pct, tov_pct, orb_pct, ft_rate
```

#### NHL (`nhl.game_logs`)
```sql
-- Scoring
goals, assists, points, plus_minus

-- Shooting
shots, shot_pct

-- Goaltending
saves, save_pct, goals_against

-- Special teams
pp_goals, pp_opportunities, pp_pct, sh_goals, pk_opportunities, pk_pct

-- Physical play
hits, blocks, penalty_minutes

-- Face-offs
faceoff_wins, faceoff_attempts, faceoff_pct
```

## 🔗 Cross-Sport Analytics

### Unified Queries
```sql
-- Games across all sports
SELECT 
    'NFL' as sport, team, opponent, result, team_score, opp_score, date, boxscore_id
FROM nfl.game_logs
UNION ALL
SELECT 
    'NBA' as sport, team, opponent, result, team_score, opp_score, date, boxscore_id  
FROM nba.game_logs
UNION ALL
SELECT 
    'NHL' as sport, team, opponent, result, team_score, opp_score, date, boxscore_id
FROM nhl.game_logs
ORDER BY date DESC;
```

### Sport-Specific Views
```sql
-- NFL game summary
SELECT * FROM nfl.game_summary WHERE season = 2023;

-- NBA game summary (when data available)
SELECT * FROM nba.game_summary WHERE season = 2024;

-- NHL game summary (when data available)  
SELECT * FROM nhl.game_summary WHERE season = 2024;
```

## 📈 Data Collection Strategy

### 1. Current Working: NFL
- ✅ Full data collection pipeline
- ✅ Boxscore ID extraction  
- ✅ Database integration
- ✅ 33 games collected (KAN + BUF 2023)

### 2. Ready for Implementation: NBA
- ✅ Database schema created
- ✅ Basketball-specific fields
- 🔄 Need to adapt collection scripts
- 📝 Use existing `app/src/nba/` modules

### 3. Ready for Implementation: NHL
- ✅ Database schema created
- ✅ Hockey-specific fields
- 🔄 Need to adapt collection scripts
- 📝 Use existing `app/src/nhl/` modules

### 4. Ready for Implementation: NCAA Sports
- ✅ Database schemas created (ncaaf, ncaab)
- ✅ College-specific adaptations
- 🔄 Need to adapt collection scripts
- 📝 Use existing `app/src/ncaaf/` and `app/src/ncaab/` modules

## 🚀 Next Steps

### Immediate Actions
1. **Adapt NBA Data Collection**
   - Modify `example_data_collection.py` for basketball
   - Map NBA field names to database schema
   - Test with Lakers or Warriors data

2. **Adapt NHL Data Collection**
   - Create hockey-specific collection script
   - Handle NHL boxscore ID format
   - Test with popular teams

3. **NCAA Sports Integration**
   - Adapt college football collection
   - Adapt college basketball collection
   - Handle tournament vs. regular season

### Development Tasks
1. **Sport-Specific Modules**
   ```python
   # Create sport-specific collection classes
   from src.nba.schedule import NBASchedule
   from src.nhl.schedule import NHLSchedule
   from src.ncaaf.schedule import NCAAFSchedule
   ```

2. **Field Mapping Functions**
   ```python
   def map_nba_fields(game_data):
       """Map NBA CSV fields to database columns."""
       
   def map_nhl_fields(game_data):
       """Map NHL CSV fields to database columns."""
   ```

3. **Unified Collection Interface**
   ```python
   def collect_sport_data(sport, team, year):
       """Unified interface for collecting any sport data."""
   ```

## 🔧 Troubleshooting

### Common Issues
1. **Field Mapping Errors**: Check sport-specific column names
2. **Boxscore ID Format**: Each sport may have different formats
3. **Date Formats**: Handle different season structures
4. **Team Abbreviations**: Map correctly between sports

### Debug Commands
```bash
# Check table structure
psql -c "\d nba.game_logs"
psql -c "\d nhl.game_logs"

# Check data samples
psql -c "SELECT * FROM nba.game_logs LIMIT 5;"
psql -c "SELECT * FROM nhl.game_logs LIMIT 5;"
```

## 🎯 Benefits Achieved

1. **✅ Unified Database**: All sports in one system
2. **✅ Sport-Specific Stats**: Tailored to each sport's needs
3. **✅ Cross-Sport Analytics**: Compare performance across sports
4. **✅ Scalable Architecture**: Easy to add new sports
5. **✅ Boxscore Linking**: Consistent game identification
6. **✅ Performance Optimized**: Proper indexes and constraints

The multi-sport database infrastructure is now complete and ready for comprehensive sports data collection and analysis! 🏆
