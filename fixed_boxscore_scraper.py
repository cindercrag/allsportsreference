#!/usr/bin/env python3
"""
Fixed NFL Boxscore Detail Scraper

This script fixes the parsing issues in the original boxscore scraper.
"""

import sys
import os
import time
import random
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
script_dir = Path(__file__).parent.absolute()
env_path = script_dir / '.env'
load_dotenv(env_path, override=True)

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from nfl_boxscore_scraper import NFLBoxscoreScraper, BoxscorePlayerStats, BoxscoreTeamStats, BoxscoreScoring
from src.nfl.database import PostgreSQLManager
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class FixedNFLBoxscoreScraper(NFLBoxscoreScraper):
    """Fixed version of the boxscore scraper with proper parsing"""
    
    def extract_player_stats(self, soup: BeautifulSoup, boxscore_id: str) -> list:
        """Extract player-level statistics - FIXED VERSION"""
        player_stats = []
        
        try:
            # Find the player offense table
            player_table = soup.find('table', {'id': 'player_offense'})
            if not player_table:
                logger.warning(f"⚠️  No player_offense table found for {boxscore_id}")
                return player_stats
            
            # Get headers to understand column positions
            headers = player_table.find('thead')
            if not headers:
                return player_stats
                
            header_cells = headers.find_all('th')
            header_text = [th.get_text(strip=True) for th in header_cells]
            
            # Debug: show headers
            logger.info(f"📋 Player table headers: {header_text}")
            
            # CORRECTED: Based on actual table structure, player is column 0, team is column 1
            # The complex headers are misleading - use the actual data positions
            col_indices = {
                'player': 0,    # Player name is first column
                'team': 1,      # Team is second column  
                'pass_cmp': 2,  # Passing completions
                'pass_att': 3,  # Passing attempts
                'pass_yds': 4,  # Passing yards
                'pass_td': 5,   # Passing TDs
                'pass_int': 6,  # Interceptions
                # Skip sack columns 7-8
                'rush_att': 10, # Rushing attempts (after passing stats)
                'rush_yds': 11, # Rushing yards
                'rush_td': 12,  # Rushing TDs
                # Skip long column 13
                'rec_tgt': 14,  # Receiving targets
                'rec_rec': 15,  # Receptions
                'rec_yds': 16,  # Receiving yards
                'rec_td': 17,   # Receiving TDs
                # Skip long and fumble columns
            }
            
            logger.info(f"📊 Column indices found: {col_indices}")
            
            # Parse player rows
            tbody = player_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 6:  # Need at least player, team, and some stats
                        continue
                    
                    # Get player name and team using correct indices
                    player_idx = col_indices.get('player', 0)  # Should be 0
                    team_idx = col_indices.get('team', 1)      # Should be 1
                    
                    if player_idx >= len(cells) or team_idx >= len(cells):
                        continue
                        
                    player_name = cells[player_idx].get_text(strip=True)
                    team = cells[team_idx].get_text(strip=True)
                    
                    # Skip invalid rows: header rows, totals, or invalid data
                    if (not player_name or not team or 
                        len(team) != 3 or 
                        player_name in ['Player', 'TD', 'Int', 'Passing', 'Rushing', 'Receiving', 'Fumbles'] or
                        team in ['Tm', 'Team'] or
                        player_name.lower() in ['total', 'team total'] or
                        'Team Totals' in player_name):
                        continue
                    
                    # Create player stat object
                    player_stat = BoxscorePlayerStats(
                        boxscore_id=boxscore_id,
                        player_name=player_name,
                        team=team
                    )
                    
                    # Extract stats based on column positions
                    try:
                        if 'pass_cmp' in col_indices and col_indices['pass_cmp'] < len(cells):
                            player_stat.pass_cmp = self._safe_int(cells[col_indices['pass_cmp']].get_text(strip=True))
                        if 'pass_att' in col_indices and col_indices['pass_att'] < len(cells):
                            player_stat.pass_att = self._safe_int(cells[col_indices['pass_att']].get_text(strip=True))
                        if 'pass_yds' in col_indices and col_indices['pass_yds'] < len(cells):
                            player_stat.pass_yds = self._safe_int(cells[col_indices['pass_yds']].get_text(strip=True))
                        if 'pass_td' in col_indices and col_indices['pass_td'] < len(cells):
                            player_stat.pass_td = self._safe_int(cells[col_indices['pass_td']].get_text(strip=True))
                        if 'pass_int' in col_indices and col_indices['pass_int'] < len(cells):
                            player_stat.pass_int = self._safe_int(cells[col_indices['pass_int']].get_text(strip=True))
                        
                        if 'rush_att' in col_indices and col_indices['rush_att'] < len(cells):
                            player_stat.rush_att = self._safe_int(cells[col_indices['rush_att']].get_text(strip=True))
                        if 'rush_yds' in col_indices and col_indices['rush_yds'] < len(cells):
                            player_stat.rush_yds = self._safe_int(cells[col_indices['rush_yds']].get_text(strip=True))
                        if 'rush_td' in col_indices and col_indices['rush_td'] < len(cells):
                            player_stat.rush_td = self._safe_int(cells[col_indices['rush_td']].get_text(strip=True))
                        
                        if 'rec_tgt' in col_indices and col_indices['rec_tgt'] < len(cells):
                            player_stat.rec_tgt = self._safe_int(cells[col_indices['rec_tgt']].get_text(strip=True))
                        if 'rec_rec' in col_indices and col_indices['rec_rec'] < len(cells):
                            player_stat.rec_rec = self._safe_int(cells[col_indices['rec_rec']].get_text(strip=True))
                        if 'rec_yds' in col_indices and col_indices['rec_yds'] < len(cells):
                            player_stat.rec_yds = self._safe_int(cells[col_indices['rec_yds']].get_text(strip=True))
                        if 'rec_td' in col_indices and col_indices['rec_td'] < len(cells):
                            player_stat.rec_td = self._safe_int(cells[col_indices['rec_td']].get_text(strip=True))
                    
                    except Exception as e:
                        logger.warning(f"⚠️  Error extracting stats for {player_name}: {e}")
                    
                    player_stats.append(player_stat)
            
            logger.info(f"👥 Extracted stats for {len(player_stats)} players")
            
        except Exception as e:
            logger.error(f"❌ Error extracting player stats for {boxscore_id}: {e}")
        
        return player_stats

    def extract_team_stats(self, soup: BeautifulSoup, boxscore_id: str) -> list:
        """Extract team-level statistics - FIXED VERSION"""
        team_stats = []
        
        try:
            # Find the team stats table
            team_table = soup.find('table', {'id': 'team_stats'})
            if not team_table:
                logger.warning(f"⚠️  No team_stats table found for {boxscore_id}")
                return team_stats
            
            # Get headers to identify teams
            headers = team_table.find('thead')
            if not headers:
                return team_stats
                
            header_cells = headers.find_all('th')
            header_text = [th.get_text(strip=True) for th in header_cells]
            
            # Expected structure: ['', 'BAL', 'KAN'] where BAL and KAN are team abbreviations
            teams = []
            for header in header_text[1:]:  # Skip first empty header
                if len(header) == 3 and header.isalpha():  # Team abbreviation
                    teams.append(header)
            
            if len(teams) != 2:
                logger.warning(f"⚠️  Expected 2 teams, found {len(teams)}: {teams}")
                return team_stats
            
            logger.info(f"📊 Found teams: {teams}")
            
            # Parse team stats rows
            tbody = team_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                
                # Create team stat objects
                team_data = {teams[0]: {}, teams[1]: {}}
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        stat_name = cells[0].get_text(strip=True)
                        team1_val = cells[1].get_text(strip=True)
                        team2_val = cells[2].get_text(strip=True)
                        
                        team_data[teams[0]][stat_name] = team1_val
                        team_data[teams[1]][stat_name] = team2_val
                
                # Create BoxscoreTeamStats objects
                for team in teams:
                    data = team_data[team]
                    
                    team_stat = BoxscoreTeamStats(
                        boxscore_id=boxscore_id,
                        team=team,
                        first_downs=self._safe_int(data.get('First Downs')),
                        total_yards=self._safe_int(data.get('Total Yards')),
                        turnovers=self._safe_int(data.get('Turnovers')),
                        time_of_possession=data.get('Time of Possession')
                    )
                    
                    # Parse specific formatted stats
                    if 'Rush-Yds-TDs' in data:
                        rush_data = data['Rush-Yds-TDs'].split('-')
                        if len(rush_data) >= 2:
                            team_stat.rushing_yards = self._safe_int(rush_data[1])
                    
                    if 'Cmp-Att-Yd-TD-INT' in data:
                        pass_data = data['Cmp-Att-Yd-TD-INT'].split('-')
                        if len(pass_data) >= 3:
                            team_stat.passing_yards = self._safe_int(pass_data[2])
                    
                    if 'Penalties-Yards' in data:
                        penalty_data = data['Penalties-Yards'].split('-')
                        if len(penalty_data) >= 2:
                            team_stat.penalties = self._safe_int(penalty_data[0])
                            team_stat.penalty_yards = self._safe_int(penalty_data[1])
                    
                    team_stats.append(team_stat)
            
            logger.info(f"📊 Extracted team stats for {len(team_stats)} teams")
            
        except Exception as e:
            logger.error(f"❌ Error extracting team stats for {boxscore_id}: {e}")
        
        return team_stats

    def extract_scoring_data(self, soup: BeautifulSoup, boxscore_id: str) -> list:
        """Extract scoring events - FIXED VERSION"""
        scoring_events = []
        
        try:
            # Find the scoring table
            scoring_table = soup.find('table', {'id': 'scoring'})
            if not scoring_table:
                logger.warning(f"⚠️  No scoring table found for {boxscore_id}")
                return scoring_events
            
            # Parse scoring events
            tbody = scoring_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 6:
                        quarter_text = cells[0].get_text(strip=True)
                        time_remaining = cells[1].get_text(strip=True)
                        team = cells[2].get_text(strip=True)
                        description = cells[3].get_text(strip=True)
                        score_home = self._safe_int(cells[4].get_text(strip=True))
                        score_away = self._safe_int(cells[5].get_text(strip=True))
                        
                        # Fix quarter parsing - provide default if can't parse
                        quarter = self._safe_int(quarter_text)
                        if quarter is None:
                            quarter = 1  # Default to first quarter if parsing fails
                        
                        # Only add if we have meaningful data
                        if time_remaining and team and description:
                            scoring_event = BoxscoreScoring(
                                boxscore_id=boxscore_id,
                                quarter=quarter,
                                time_remaining=time_remaining,
                                team=team,
                                description=description,
                                score_home=score_home or 0,
                                score_away=score_away or 0
                            )
                            scoring_events.append(scoring_event)
            
            logger.info(f"🏆 Extracted {len(scoring_events)} scoring events")
            
        except Exception as e:
            logger.error(f"❌ Error extracting scoring data for {boxscore_id}: {e}")
        
        return scoring_events

    def extract_officials_data(self, soup: BeautifulSoup, boxscore_id: str) -> list:
        """Extract game officials data"""
        officials = []
        
        try:
            # Find the officials table
            officials_table = soup.find('table', {'id': 'officials'})
            if not officials_table:
                logger.warning(f"⚠️  No officials table found for {boxscore_id}")
                return officials
            
            # Parse officials data - officials table has direct tr elements, no tbody
            rows = officials_table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    position = cells[0].get_text(strip=True)
                    name = cells[1].get_text(strip=True)
                    
                    # Skip header rows and invalid data
                    if (position and name and 
                        position != 'Officials' and 
                        len(position) > 2 and len(name) > 2):
                        official_data = {
                            'boxscore_id': boxscore_id,
                            'position': position,
                            'name': name
                        }
                        officials.append(official_data)
            
            logger.info(f"🏛️ Extracted {len(officials)} officials")
            
        except Exception as e:
            logger.error(f"❌ Error extracting officials data for {boxscore_id}: {e}")
        
        return officials

    def save_officials_data(self, officials: list):
        """Save officials data to database"""
        try:
            with PostgreSQLManager() as db:
                with db._connection.cursor() as cursor:
                    
                    for official in officials:
                        cursor.execute("""
                            INSERT INTO nfl.boxscore_officials (boxscore_id, position, name, scraped_at)
                            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (boxscore_id, position) DO UPDATE SET
                                name = EXCLUDED.name,
                                scraped_at = EXCLUDED.scraped_at
                        """, (
                            official['boxscore_id'],
                            official['position'], 
                            official['name']
                        ))
                    
                    db._connection.commit()
                    logger.info(f"💾 Saved {len(officials)} officials to database")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Error saving officials data: {e}")
            return False

    def extract_defense_data(self, soup: BeautifulSoup, boxscore_id: str) -> list:
        """Extract player defense statistics"""
        defense_stats = []
        
        try:
            # Find the player defense table
            defense_table = soup.find('table', {'id': 'player_defense'})
            if not defense_table:
                logger.warning(f"⚠️  No player_defense table found for {boxscore_id}")
                return defense_stats
            
            # Parse defense data - direct tr elements
            rows = defense_table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 8:  # Minimum columns needed for defense data
                    cell_text = [cell.get_text(strip=True) for cell in cells]
                    
                    # Check if this is a valid player row
                    player_name = cell_text[0] if len(cell_text) > 0 else ""
                    team = cell_text[1] if len(cell_text) > 1 else ""
                    
                    # Skip header rows and invalid data
                    if (player_name and team and 
                        player_name not in ['', 'Player', 'Def Interceptions', 'Tackles', 'Fumbles'] and
                        len(player_name) > 3 and  # Player name should be longer than 3 chars
                        len(team) == 3):  # Team should be 3 chars
                        
                        # Map defense statistics with proper defaults
                        def safe_float(value, default=0.0):
                            try:
                                return float(value) if value and value != '' else default
                            except:
                                return default
                        
                        def safe_int(value, default=0):
                            try:
                                return int(float(value)) if value and value != '' else default
                            except:
                                return default
                        
                        defense_data = {
                            'boxscore_id': boxscore_id,
                            'player_name': player_name,
                            'team': team,
                            'def_int': safe_int(cell_text[2] if len(cell_text) > 2 else ''),  # Interceptions
                            'def_int_yds': safe_int(cell_text[3] if len(cell_text) > 3 else ''),  # INT yards
                            'def_int_td': safe_int(cell_text[4] if len(cell_text) > 4 else ''),  # INT TDs
                            'def_int_long': safe_int(cell_text[5] if len(cell_text) > 5 else ''),  # INT long (not in DB)
                            'def_pd': safe_int(cell_text[6] if len(cell_text) > 6 else ''),  # Passes defended
                            'def_sacks': safe_float(cell_text[7] if len(cell_text) > 7 else ''),  # Sacks
                            'def_tackles': safe_int(cell_text[8] if len(cell_text) > 8 else ''),  # Combined tackles
                            'def_tackles_solo': safe_int(cell_text[9] if len(cell_text) > 9 else ''),  # Solo tackles (not in DB)
                            'def_assists': safe_int(cell_text[10] if len(cell_text) > 10 else ''),  # Tackle assists
                            'def_tackles_for_loss': safe_int(cell_text[11] if len(cell_text) > 11 else ''),  # TFL (not in DB)
                            'def_qb_hits': safe_int(cell_text[12] if len(cell_text) > 12 else ''),  # QB hits (not in DB)
                            'def_fr': safe_int(cell_text[13] if len(cell_text) > 13 else ''),  # Fumbles recovered
                            'def_fumble_yards': safe_int(cell_text[14] if len(cell_text) > 14 else ''),  # Fumble yards (not in DB)
                            'def_fumble_td': safe_int(cell_text[15] if len(cell_text) > 15 else ''),  # Fumble TD (not in DB)
                            'def_ff': safe_int(cell_text[16] if len(cell_text) > 16 else '')  # Fumbles forced
                        }
                        
                        defense_stats.append(defense_data)
            
            logger.info(f"🛡️ Extracted {len(defense_stats)} defensive player stats")
            
        except Exception as e:
            logger.error(f"❌ Error extracting defense data for {boxscore_id}: {e}")
        
        return defense_stats

    def save_defense_data(self, defense_stats: list):
        """Save defense data as new player records or update existing ones"""
        try:
            with PostgreSQLManager() as db:
                with db._connection.cursor() as cursor:
                    
                    for defense in defense_stats:
                        # Try to update existing record first, then insert if not found
                        cursor.execute("""
                            UPDATE nfl.boxscore_player_stats 
                            SET 
                                def_int = %s,
                                def_int_yds = %s,
                                def_int_td = %s,
                                def_pd = %s,
                                def_sacks = %s,
                                def_tackles = %s,
                                def_assists = %s,
                                def_fr = %s,
                                def_ff = %s,
                                created_at = CURRENT_TIMESTAMP
                            WHERE boxscore_id = %s AND player_name = %s AND team = %s
                        """, (
                            defense['def_int'],
                            defense['def_int_yds'],
                            defense['def_int_td'],
                            defense['def_pd'],
                            defense['def_sacks'],
                            defense['def_tackles'],
                            defense['def_assists'],
                            defense['def_fr'],
                            defense['def_ff'],
                            defense['boxscore_id'],
                            defense['player_name'],
                            defense['team']
                        ))
                        
                        # If no rows were updated, insert a new record
                        if cursor.rowcount == 0:
                            cursor.execute("""
                                INSERT INTO nfl.boxscore_player_stats (
                                    boxscore_id, player_name, team,
                                    def_int, def_int_yds, def_int_td, def_pd, def_sacks,
                                    def_tackles, def_assists, def_fr, def_ff,
                                    created_at
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                            """, (
                                defense['boxscore_id'],
                                defense['player_name'],
                                defense['team'],
                                defense['def_int'],
                                defense['def_int_yds'],
                                defense['def_int_td'],
                                defense['def_pd'],
                                defense['def_sacks'],
                                defense['def_tackles'],
                                defense['def_assists'],
                                defense['def_fr'],
                                defense['def_ff']
                            ))
                    
                    db._connection.commit()
                    logger.info(f"💾 Processed {len(defense_stats)} defensive player records")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Error saving defense data: {e}")
            return False

    def extract_returns_data(self, soup: BeautifulSoup, boxscore_id: str) -> list:
        """Extract kick and punt return statistics"""
        returns_stats = []
        
        try:
            # Find the returns table
            returns_table = soup.find('table', {'id': 'returns'})
            if not returns_table:
                logger.warning(f"⚠️  No returns table found for {boxscore_id}")
                return returns_stats
            
            # Parse returns data - direct tr elements
            rows = returns_table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 12:  # Minimum columns needed for returns data
                    cell_text = [cell.get_text(strip=True) for cell in cells]
                    
                    # Check if this is a valid player row
                    player_name = cell_text[0] if len(cell_text) > 0 else ""
                    team = cell_text[1] if len(cell_text) > 1 else ""
                    
                    # Skip header rows and invalid data
                    if (player_name and team and 
                        player_name not in ['', 'Player', 'Kick Returns', 'Punt Returns'] and
                        len(player_name) > 3 and  # Player name should be longer than 3 chars
                        len(team) == 3):  # Team should be 3 chars
                        
                        # Map return statistics with proper defaults
                        def safe_float(value, default=0.0):
                            try:
                                if value and value != '' and value != '-':
                                    return float(value)
                                return default
                            except:
                                return default
                        
                        def safe_int(value, default=0):
                            try:
                                if value and value != '' and value != '-':
                                    return int(float(value))
                                return default
                            except:
                                return default
                        
                        returns_data = {
                            'boxscore_id': boxscore_id,
                            'player_name': player_name,
                            'team': team,
                            # Kick return stats (columns 2-6)
                            'kick_returns': safe_int(cell_text[2] if len(cell_text) > 2 else ''),
                            'kick_return_yards': safe_int(cell_text[3] if len(cell_text) > 3 else ''),
                            'kick_return_avg': safe_float(cell_text[4] if len(cell_text) > 4 else ''),
                            'kick_return_td': safe_int(cell_text[5] if len(cell_text) > 5 else ''),
                            'kick_return_long': safe_int(cell_text[6] if len(cell_text) > 6 else ''),
                            # Punt return stats (columns 7-11)
                            'punt_returns': safe_int(cell_text[7] if len(cell_text) > 7 else ''),
                            'punt_return_yards': safe_int(cell_text[8] if len(cell_text) > 8 else ''),
                            'punt_return_avg': safe_float(cell_text[9] if len(cell_text) > 9 else ''),
                            'punt_return_td': safe_int(cell_text[10] if len(cell_text) > 10 else ''),
                            'punt_return_long': safe_int(cell_text[11] if len(cell_text) > 11 else '')
                        }
                        
                        returns_stats.append(returns_data)
            
            logger.info(f"🏃 Extracted {len(returns_stats)} return specialists")
            
        except Exception as e:
            logger.error(f"❌ Error extracting returns data for {boxscore_id}: {e}")
        
        return returns_stats

    def save_returns_data(self, returns_stats: list):
        """Save return data to the existing player stats table"""
        try:
            with PostgreSQLManager() as db:
                with db._connection.cursor() as cursor:
                    
                    for returns in returns_stats:
                        # First try to update existing player record
                        cursor.execute("""
                            UPDATE nfl.boxscore_player_stats 
                            SET 
                                kick_returns = %s,
                                kick_return_yards = %s,
                                kick_return_avg = %s,
                                kick_return_td = %s,
                                kick_return_long = %s,
                                punt_returns = %s,
                                punt_return_yards = %s,
                                punt_return_avg = %s,
                                punt_return_td = %s,
                                punt_return_long = %s,
                                created_at = CURRENT_TIMESTAMP
                            WHERE boxscore_id = %s AND player_name = %s AND team = %s
                        """, (
                            returns['kick_returns'],
                            returns['kick_return_yards'],
                            returns['kick_return_avg'],
                            returns['kick_return_td'],
                            returns['kick_return_long'],
                            returns['punt_returns'],
                            returns['punt_return_yards'],
                            returns['punt_return_avg'],
                            returns['punt_return_td'],
                            returns['punt_return_long'],
                            returns['boxscore_id'],
                            returns['player_name'],
                            returns['team']
                        ))
                        
                        # If no rows were updated, insert a new player record
                        if cursor.rowcount == 0:
                            cursor.execute("""
                                INSERT INTO nfl.boxscore_player_stats (
                                    boxscore_id, player_name, team,
                                    kick_returns, kick_return_yards, kick_return_avg, kick_return_td, kick_return_long,
                                    punt_returns, punt_return_yards, punt_return_avg, punt_return_td, punt_return_long,
                                    created_at
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                                )
                            """, (
                                returns['boxscore_id'],
                                returns['player_name'],
                                returns['team'],
                                returns['kick_returns'],
                                returns['kick_return_yards'],
                                returns['kick_return_avg'],
                                returns['kick_return_td'],
                                returns['kick_return_long'],
                                returns['punt_returns'],
                                returns['punt_return_yards'],
                                returns['punt_return_avg'],
                                returns['punt_return_td'],
                                returns['punt_return_long']
                            ))
                    
                    db._connection.commit()
                    logger.info(f"💾 Processed {len(returns_stats)} return specialist records")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Error saving returns data: {e}")
            return False

    def extract_kicking_punting_data(self, soup: BeautifulSoup, boxscore_id: str) -> list:
        """Extract kicking and punting statistics"""
        kicking_stats = []
        
        try:
            # Find the kicking table using div_kicking
            kicking_div = soup.find('div', {'id': 'div_kicking'})
            if not kicking_div:
                logger.warning(f"⚠️  No div_kicking found for {boxscore_id}")
                return kicking_stats
            
            kicking_table = kicking_div.find('table')
            if not kicking_table:
                logger.warning(f"⚠️  No table found in div_kicking for {boxscore_id}")
                return kicking_stats
            
            logger.info(f"🦵 Found kicking table for {boxscore_id}")
            
            # Get table headers to understand column positions
            headers = []
            header_row = kicking_table.find('thead')
            if header_row:
                for th in header_row.find_all('th'):
                    header_text = th.get_text(strip=True)
                    headers.append(header_text)
            
            logger.info(f"📋 Kicking table headers: {headers}")
            
            # Process each row in the table body
            tbody = kicking_table.find('tbody')
            if tbody:
                for row in tbody.find_all('tr'):
                    cells = []
                    for cell in row.find_all(['td', 'th']):
                        cell_text = cell.get_text(strip=True)
                        cells.append(cell_text)
                    
                    # Skip empty rows or header rows
                    if not cells or len(cells) < 3:
                        continue
                    
                    # Expected format based on actual data analysis: 
                    # Player at index 0, Team at index 1, then XPM, XPA, FGM, FGA, Punts, Yards, Avg, Long
                    try:
                        player_name = cells[0] if len(cells) > 0 else ""
                        team = cells[1] if len(cells) > 1 else ""
                        
                        # Skip header rows, empty rows, or invalid data
                        if (not player_name or not team or 
                            player_name == "Player" or team == "Tm" or
                            len(cells) < 6):  # Need at least 6 columns for basic kicking data
                            continue
                        
                        # Helper function to safely convert to number
                        def safe_int(value, default=0):
                            if value in ['', '-', None]:
                                return default
                            try:
                                return int(value)
                            except (ValueError, TypeError):
                                return default
                        
                        def safe_float(value, default=0.0):
                            if value in ['', '-', None]:
                                return default
                            try:
                                # Remove % sign if present
                                if isinstance(value, str) and value.endswith('%'):
                                    value = value[:-1]
                                return float(value)
                            except (ValueError, TypeError):
                                return default
                        
                        # Map the columns based on actual table structure
                        # Player, Team, XPM, XPA, FGM, FGA, Punts, Yards, Avg, Long
                        kicking_data = {
                            'boxscore_id': boxscore_id,
                            'player_name': player_name,
                            'team': team,
                            # Extra Points (XPM/XPA)
                            'xp_made': safe_int(cells[2] if len(cells) > 2 else ""),
                            'xp_att': safe_int(cells[3] if len(cells) > 3 else ""),
                            # Field Goals (FGM/FGA)
                            'fg_made': safe_int(cells[4] if len(cells) > 4 else ""),
                            'fg_att': safe_int(cells[5] if len(cells) > 5 else ""),
                            # Punting
                            'punt_punts': safe_int(cells[6] if len(cells) > 6 else ""),
                            'punt_yards': safe_int(cells[7] if len(cells) > 7 else ""),
                            'punt_avg': safe_float(cells[8] if len(cells) > 8 else ""),
                            'punt_long': safe_int(cells[9] if len(cells) > 9 else ""),
                            # Calculate percentages
                            'fg_pct': 0.0,
                            'xp_pct': 0.0,
                            # Initialize other fields to 0
                            'fg_long': 0,
                            'fg_1_19_made': 0, 'fg_1_19_att': 0,
                            'fg_20_29_made': 0, 'fg_20_29_att': 0,
                            'fg_30_39_made': 0, 'fg_30_39_att': 0,
                            'fg_40_49_made': 0, 'fg_40_49_att': 0,
                            'fg_50_plus_made': 0, 'fg_50_plus_att': 0,
                            'punt_net_avg': 0.0, 'punt_in_20': 0, 'punt_in_20_pct': 0.0,
                            'punt_touchbacks': 0, 'punt_touchback_pct': 0.0, 'punt_blocked': 0
                        }
                        
                        # Calculate percentages
                        if kicking_data['fg_att'] > 0:
                            kicking_data['fg_pct'] = round((kicking_data['fg_made'] / kicking_data['fg_att']) * 100, 1)
                        if kicking_data['xp_att'] > 0:
                            kicking_data['xp_pct'] = round((kicking_data['xp_made'] / kicking_data['xp_att']) * 100, 1)
                        
                        kicking_stats.append(kicking_data)
                        logger.info(f"📊 Processed kicking/punting: {player_name} ({team})")
                        
                    except Exception as row_error:
                        logger.warning(f"⚠️  Error processing kicking row {cells}: {row_error}")
                        continue
            
            logger.info(f"✅ Extracted {len(kicking_stats)} kicking/punting records")
            
        except Exception as e:
            logger.error(f"❌ Error extracting kicking data for {boxscore_id}: {e}")
        
        return kicking_stats

    def save_kicking_punting_data(self, kicking_stats: list):
        """Save kicking and punting data to the existing player stats table"""
        try:
            with PostgreSQLManager() as db:
                with db._connection.cursor() as cursor:
                    
                    for kicking in kicking_stats:
                        # First try to update existing player record
                        cursor.execute("""
                            UPDATE nfl.boxscore_player_stats 
                            SET 
                                fg_made = %s, fg_att = %s, fg_pct = %s, fg_long = %s,
                                fg_1_19_made = %s, fg_1_19_att = %s,
                                fg_20_29_made = %s, fg_20_29_att = %s,
                                fg_30_39_made = %s, fg_30_39_att = %s,
                                fg_40_49_made = %s, fg_40_49_att = %s,
                                fg_50_plus_made = %s, fg_50_plus_att = %s,
                                xp_made = %s, xp_att = %s, xp_pct = %s,
                                punt_punts = %s, punt_yards = %s, punt_long = %s,
                                punt_avg = %s, punt_net_avg = %s,
                                punt_in_20 = %s, punt_in_20_pct = %s,
                                punt_touchbacks = %s, punt_touchback_pct = %s,
                                punt_blocked = %s,
                                created_at = CURRENT_TIMESTAMP
                            WHERE boxscore_id = %s AND player_name = %s AND team = %s
                        """, (
                            kicking['fg_made'], kicking['fg_att'], kicking['fg_pct'], kicking['fg_long'],
                            kicking['fg_1_19_made'], kicking['fg_1_19_att'],
                            kicking['fg_20_29_made'], kicking['fg_20_29_att'],
                            kicking['fg_30_39_made'], kicking['fg_30_39_att'],
                            kicking['fg_40_49_made'], kicking['fg_40_49_att'],
                            kicking['fg_50_plus_made'], kicking['fg_50_plus_att'],
                            kicking['xp_made'], kicking['xp_att'], kicking['xp_pct'],
                            kicking['punt_punts'], kicking['punt_yards'], kicking['punt_long'],
                            kicking['punt_avg'], kicking['punt_net_avg'],
                            kicking['punt_in_20'], kicking['punt_in_20_pct'],
                            kicking['punt_touchbacks'], kicking['punt_touchback_pct'],
                            kicking['punt_blocked'],
                            kicking['boxscore_id'], kicking['player_name'], kicking['team']
                        ))
                        
                        # If no rows were updated, insert a new player record
                        if cursor.rowcount == 0:
                            cursor.execute("""
                                INSERT INTO nfl.boxscore_player_stats (
                                    boxscore_id, player_name, team,
                                    fg_made, fg_att, fg_pct, fg_long,
                                    fg_1_19_made, fg_1_19_att, fg_20_29_made, fg_20_29_att,
                                    fg_30_39_made, fg_30_39_att, fg_40_49_made, fg_40_49_att,
                                    fg_50_plus_made, fg_50_plus_att,
                                    xp_made, xp_att, xp_pct,
                                    punt_punts, punt_yards, punt_long, punt_avg, punt_net_avg,
                                    punt_in_20, punt_in_20_pct, punt_touchbacks, punt_touchback_pct,
                                    punt_blocked, created_at
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                                )
                            """, (
                                kicking['boxscore_id'], kicking['player_name'], kicking['team'],
                                kicking['fg_made'], kicking['fg_att'], kicking['fg_pct'], kicking['fg_long'],
                                kicking['fg_1_19_made'], kicking['fg_1_19_att'], kicking['fg_20_29_made'], kicking['fg_20_29_att'],
                                kicking['fg_30_39_made'], kicking['fg_30_39_att'], kicking['fg_40_49_made'], kicking['fg_40_49_att'],
                                kicking['fg_50_plus_made'], kicking['fg_50_plus_att'],
                                kicking['xp_made'], kicking['xp_att'], kicking['xp_pct'],
                                kicking['punt_punts'], kicking['punt_yards'], kicking['punt_long'],
                                kicking['punt_avg'], kicking['punt_net_avg'],
                                kicking['punt_in_20'], kicking['punt_in_20_pct'],
                                kicking['punt_touchbacks'], kicking['punt_touchback_pct'],
                                kicking['punt_blocked']
                            ))
                    
                    db._connection.commit()
                    logger.info(f"💾 Processed {len(kicking_stats)} kicking/punting records")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Error saving kicking/punting data: {e}")
            return False


    def extract_advanced_passing_data(self, soup: BeautifulSoup, boxscore_id: str) -> list:
        """Extract advanced passing statistics"""
        advanced_passing_stats = []
        
        try:
            # Find the advanced passing table using div_passing_advanced
            advanced_div = soup.find('div', {'id': 'div_passing_advanced'})
            if not advanced_div:
                logger.warning(f"⚠️  No div_passing_advanced found for {boxscore_id}")
                return advanced_passing_stats
            
            advanced_table = advanced_div.find('table')
            if not advanced_table:
                logger.warning(f"⚠️  No table found in div_passing_advanced for {boxscore_id}")
                return advanced_passing_stats
            
            logger.info(f"🎯 Found advanced passing table for {boxscore_id}")
            
            # Get table headers to understand column positions
            headers = []
            header_row = advanced_table.find('thead')
            if header_row:
                for th in header_row.find_all('th'):
                    header_text = th.get_text(strip=True)
                    headers.append(header_text)
            
            logger.info(f"📋 Advanced passing headers: {headers}")
            
            # Process each row in the table body
            tbody = advanced_table.find('tbody')
            if tbody:
                for row in tbody.find_all('tr'):
                    cells = []
                    for cell in row.find_all(['td', 'th']):
                        cell_text = cell.get_text(strip=True)
                        cells.append(cell_text)
                    
                    # Skip empty rows or header rows
                    if not cells or len(cells) < 3:
                        continue
                    
                    # Expected format based on analysis: 
                    # ['Player', 'Tm', 'Cmp', 'Att', 'Yds', '1D', '1D%', 'IAY', 'IAY/PA', 'CAY', 'CAY/Cmp', 'CAY/PA', 'YAC', 'YAC/Cmp', 'Drops', 'Drop%', 'BadTh', 'Bad%', 'Sk', 'Bltz', 'Hrry', 'Hits', 'Prss', 'Prss%', 'Scrm', 'Yds/Scr']
                    try:
                        player_name = cells[0] if len(cells) > 0 else ""
                        team = cells[1] if len(cells) > 1 else ""
                        
                        # Skip header rows, empty rows, or invalid data
                        if (not player_name or not team or 
                            player_name == "Player" or team == "Tm" or
                            len(cells) < 10):  # Need at least 10 columns for meaningful data
                            continue
                        
                        # Helper function to safely convert to number
                        def safe_int(value, default=0):
                            if value in ['', '-', None]:
                                return default
                            try:
                                return int(value)
                            except (ValueError, TypeError):
                                return default
                        
                        def safe_float(value, default=0.0):
                            if value in ['', '-', None]:
                                return default
                            try:
                                # Remove % sign if present
                                if isinstance(value, str) and value.endswith('%'):
                                    value = value[:-1]
                                return float(value)
                            except (ValueError, TypeError):
                                return default
                        
                        # Map the columns based on expected table structure
                        advanced_data = {
                            'boxscore_id': boxscore_id,
                            'player_name': player_name,
                            'team': team,
                            # Basic stats (for validation)
                            'cmp': safe_int(cells[2] if len(cells) > 2 else ""),
                            'att': safe_int(cells[3] if len(cells) > 3 else ""),
                            'yds': safe_int(cells[4] if len(cells) > 4 else ""),
                            # First Downs
                            'first_downs': safe_int(cells[5] if len(cells) > 5 else ""),
                            'first_down_pct': safe_float(cells[6] if len(cells) > 6 else ""),
                            # Air Yards Analysis
                            'intended_air_yards': safe_int(cells[7] if len(cells) > 7 else ""),
                            'intended_air_yards_per_att': safe_float(cells[8] if len(cells) > 8 else ""),
                            'completed_air_yards': safe_int(cells[9] if len(cells) > 9 else ""),
                            'completed_air_yards_per_cmp': safe_float(cells[10] if len(cells) > 10 else ""),
                            'completed_air_yards_per_att': safe_float(cells[11] if len(cells) > 11 else ""),
                            # YAC Analysis
                            'yac': safe_int(cells[12] if len(cells) > 12 else ""),
                            'yac_per_cmp': safe_float(cells[13] if len(cells) > 13 else ""),
                            # Accuracy Analysis
                            'drops': safe_int(cells[14] if len(cells) > 14 else ""),
                            'drop_pct': safe_float(cells[15] if len(cells) > 15 else ""),
                            'bad_throws': safe_int(cells[16] if len(cells) > 16 else ""),
                            'bad_throw_pct': safe_float(cells[17] if len(cells) > 17 else ""),
                            # Pressure Analysis
                            'sacks': safe_int(cells[18] if len(cells) > 18 else ""),
                            'blitzes_faced': safe_int(cells[19] if len(cells) > 19 else ""),
                            'hurries': safe_int(cells[20] if len(cells) > 20 else ""),
                            'hits': safe_int(cells[21] if len(cells) > 21 else ""),
                            'pressures': safe_int(cells[22] if len(cells) > 22 else ""),
                            'pressure_pct': safe_float(cells[23] if len(cells) > 23 else ""),
                            # Mobility
                            'scrambles': safe_int(cells[24] if len(cells) > 24 else ""),
                            'scramble_yards_per_scramble': safe_float(cells[25] if len(cells) > 25 else "")
                        }
                        
                        advanced_passing_stats.append(advanced_data)
                        logger.info(f"📊 Processed advanced passing: {player_name} ({team})")
                        
                    except Exception as row_error:
                        logger.warning(f"⚠️  Error processing advanced passing row {cells}: {row_error}")
                        continue
            
            logger.info(f"✅ Extracted {len(advanced_passing_stats)} advanced passing records")
            
        except Exception as e:
            logger.error(f"❌ Error extracting advanced passing data for {boxscore_id}: {e}")
        
        return advanced_passing_stats

    def save_advanced_passing_data(self, advanced_passing_stats: list):
        """Save advanced passing data to the dedicated table"""
        try:
            with PostgreSQLManager() as db:
                with db._connection.cursor() as cursor:
                    
                    for adv_pass in advanced_passing_stats:
                        # Insert or update advanced passing record
                        cursor.execute("""
                            INSERT INTO nfl.boxscore_advanced_passing (
                                boxscore_id, player_name, team,
                                cmp, att, yds,
                                first_downs, first_down_pct,
                                intended_air_yards, intended_air_yards_per_att,
                                completed_air_yards, completed_air_yards_per_cmp, completed_air_yards_per_att,
                                yac, yac_per_cmp,
                                drops, drop_pct, bad_throws, bad_throw_pct,
                                sacks, blitzes_faced, hurries, hits, pressures, pressure_pct,
                                scrambles, scramble_yards_per_scramble,
                                created_at
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                            ) ON CONFLICT (boxscore_id, player_name, team) 
                            DO UPDATE SET
                                cmp = EXCLUDED.cmp,
                                att = EXCLUDED.att,
                                yds = EXCLUDED.yds,
                                first_downs = EXCLUDED.first_downs,
                                first_down_pct = EXCLUDED.first_down_pct,
                                intended_air_yards = EXCLUDED.intended_air_yards,
                                intended_air_yards_per_att = EXCLUDED.intended_air_yards_per_att,
                                completed_air_yards = EXCLUDED.completed_air_yards,
                                completed_air_yards_per_cmp = EXCLUDED.completed_air_yards_per_cmp,
                                completed_air_yards_per_att = EXCLUDED.completed_air_yards_per_att,
                                yac = EXCLUDED.yac,
                                yac_per_cmp = EXCLUDED.yac_per_cmp,
                                drops = EXCLUDED.drops,
                                drop_pct = EXCLUDED.drop_pct,
                                bad_throws = EXCLUDED.bad_throws,
                                bad_throw_pct = EXCLUDED.bad_throw_pct,
                                sacks = EXCLUDED.sacks,
                                blitzes_faced = EXCLUDED.blitzes_faced,
                                hurries = EXCLUDED.hurries,
                                hits = EXCLUDED.hits,
                                pressures = EXCLUDED.pressures,
                                pressure_pct = EXCLUDED.pressure_pct,
                                scrambles = EXCLUDED.scrambles,
                                scramble_yards_per_scramble = EXCLUDED.scramble_yards_per_scramble,
                                created_at = CURRENT_TIMESTAMP
                        """, (
                            adv_pass['boxscore_id'], adv_pass['player_name'], adv_pass['team'],
                            adv_pass['cmp'], adv_pass['att'], adv_pass['yds'],
                            adv_pass['first_downs'], adv_pass['first_down_pct'],
                            adv_pass['intended_air_yards'], adv_pass['intended_air_yards_per_att'],
                            adv_pass['completed_air_yards'], adv_pass['completed_air_yards_per_cmp'], 
                            adv_pass['completed_air_yards_per_att'],
                            adv_pass['yac'], adv_pass['yac_per_cmp'],
                            adv_pass['drops'], adv_pass['drop_pct'], adv_pass['bad_throws'], adv_pass['bad_throw_pct'],
                            adv_pass['sacks'], adv_pass['blitzes_faced'], adv_pass['hurries'], 
                            adv_pass['hits'], adv_pass['pressures'], adv_pass['pressure_pct'],
                            adv_pass['scrambles'], adv_pass['scramble_yards_per_scramble']
                        ))
                    
                    db._connection.commit()
                    logger.info(f"💾 Processed {len(advanced_passing_stats)} advanced passing records")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Error saving advanced passing data: {e}")
            return False


    def extract_advanced_rushing_data(self, soup: BeautifulSoup, boxscore_id: str) -> list:
        """Extract advanced rushing statistics"""
        advanced_rushing_stats = []
        
        try:
            # Find the advanced rushing table using div_rushing_advanced
            advanced_div = soup.find('div', {'id': 'div_rushing_advanced'})
            if not advanced_div:
                logger.warning(f"⚠️  No div_rushing_advanced found for {boxscore_id}")
                return advanced_rushing_stats
            
            advanced_table = advanced_div.find('table')
            if not advanced_table:
                logger.warning(f"⚠️  No table found in div_rushing_advanced for {boxscore_id}")
                return advanced_rushing_stats
            
            logger.info(f"🏃 Found advanced rushing table for {boxscore_id}")
            
            # Get table headers to understand column positions
            headers = []
            header_row = advanced_table.find('thead')
            if header_row:
                for th in header_row.find_all('th'):
                    header_text = th.get_text(strip=True)
                    headers.append(header_text)
            
            logger.info(f"📋 Advanced rushing headers: {headers}")
            
            # Process each row in the table body
            tbody = advanced_table.find('tbody')
            if tbody:
                for row in tbody.find_all('tr'):
                    cells = []
                    for cell in row.find_all(['td', 'th']):
                        cell_text = cell.get_text(strip=True)
                        cells.append(cell_text)
                    
                    # Skip empty rows or header rows
                    if not cells or len(cells) < 3:
                        continue
                    
                    # Skip header rows that appear in the body
                    if cells[0] in ['Player', 'Tm'] or cells[0] == 'Tm':
                        continue
                    
                    try:
                        # Local utility functions
                        def clean_text(text):
                            return text.strip() if text else ''
                        
                        def safe_int(value, default=0):
                            try:
                                return int(float(value)) if value and value != '' else default
                            except:
                                return default
                        
                        def safe_decimal(value, default=0.0):
                            try:
                                return float(value) if value and value != '' else default
                            except:
                                return default
                        
                        # Expected columns: ['Player', 'Tm', 'Att', 'Yds', 'TD', '1D', 'YBC', 'YBC/Att', 'YAC', 'YAC/Att', 'BrkTkl', 'Att/Br']
                        rushing_record = {
                            'boxscore_id': boxscore_id,
                            'player_name': clean_text(cells[0]),
                            'team': clean_text(cells[1]) if len(cells) > 1 else '',
                            'rush_att': safe_int(cells[2]) if len(cells) > 2 else 0,
                            'rush_yds': safe_int(cells[3]) if len(cells) > 3 else 0,
                            'rush_td': safe_int(cells[4]) if len(cells) > 4 else 0,
                            'rush_first_downs': safe_int(cells[5]) if len(cells) > 5 else 0,
                            'yards_before_contact': safe_int(cells[6]) if len(cells) > 6 else 0,
                            'yards_before_contact_per_att': safe_decimal(cells[7]) if len(cells) > 7 else 0.0,
                            'yards_after_contact': safe_int(cells[8]) if len(cells) > 8 else 0,
                            'yards_after_contact_per_att': safe_decimal(cells[9]) if len(cells) > 9 else 0.0,
                            'broken_tackles': safe_int(cells[10]) if len(cells) > 10 else 0,
                            'att_per_broken_tackle': safe_decimal(cells[11]) if len(cells) > 11 else 0.0
                        }
                        
                        # Only add if player has actual rushing attempts
                        if rushing_record['rush_att'] > 0:
                            advanced_rushing_stats.append(rushing_record)
                            logger.debug(f"🏃 Advanced rushing: {rushing_record['player_name']} ({rushing_record['team']}) - "
                                       f"{rushing_record['rush_att']} att, {rushing_record['yards_before_contact']} YBC, "
                                       f"{rushing_record['yards_after_contact']} YAC, {rushing_record['broken_tackles']} BrkTkl")
                        
                    except Exception as e:
                        logger.warning(f"⚠️  Error parsing advanced rushing row: {cells[:3]} - {e}")
                        continue
            
            logger.info(f"🏃 Extracted {len(advanced_rushing_stats)} advanced rushing records")
            
        except Exception as e:
            logger.error(f"❌ Error extracting advanced rushing data: {e}")
        
        return advanced_rushing_stats

    def save_advanced_rushing_data(self, advanced_rushing_stats: list):
        """Save advanced rushing data to the dedicated table"""
        try:
            with PostgreSQLManager() as db:
                with db._connection.cursor() as cursor:
                    
                    for rushing in advanced_rushing_stats:
                        cursor.execute("""
                            INSERT INTO nfl.boxscore_advanced_rushing (
                                boxscore_id, player_name, team,
                                rush_att, rush_yds, rush_td, rush_first_downs,
                                yards_before_contact, yards_before_contact_per_att,
                                yards_after_contact, yards_after_contact_per_att,
                                broken_tackles, att_per_broken_tackle
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (boxscore_id, player_name, team) 
                            DO UPDATE SET
                                rush_att = EXCLUDED.rush_att,
                                rush_yds = EXCLUDED.rush_yds,
                                rush_td = EXCLUDED.rush_td,
                                rush_first_downs = EXCLUDED.rush_first_downs,
                                yards_before_contact = EXCLUDED.yards_before_contact,
                                yards_before_contact_per_att = EXCLUDED.yards_before_contact_per_att,
                                yards_after_contact = EXCLUDED.yards_after_contact,
                                yards_after_contact_per_att = EXCLUDED.yards_after_contact_per_att,
                                broken_tackles = EXCLUDED.broken_tackles,
                                att_per_broken_tackle = EXCLUDED.att_per_broken_tackle,
                                updated_at = CURRENT_TIMESTAMP
                        """, (
                            rushing['boxscore_id'],
                            rushing['player_name'],
                            rushing['team'],
                            rushing['rush_att'],
                            rushing['rush_yds'],
                            rushing['rush_td'],
                            rushing['rush_first_downs'],
                            rushing['yards_before_contact'],
                            rushing['yards_before_contact_per_att'],
                            rushing['yards_after_contact'],
                            rushing['yards_after_contact_per_att'],
                            rushing['broken_tackles'],
                            rushing['att_per_broken_tackle']
                        ))
                    
                    db._connection.commit()
                    logger.info(f"💾 Processed {len(advanced_rushing_stats)} advanced rushing records")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Error saving advanced rushing data: {e}")
            return False


    def scrape_boxscore_details(self, boxscore_id: str) -> bool:
        """Scrape detailed statistics for a single boxscore - ENHANCED VERSION"""
        logger.info(f"🔍 Scraping boxscore details: {boxscore_id}")
        
        try:
            # Fetch the HTML
            soup = self.fetch_boxscore_html(boxscore_id)
            if not soup:
                return False
            
            # Extract all data
            player_stats = self.extract_player_stats(soup, boxscore_id)
            team_stats = self.extract_team_stats(soup, boxscore_id)
            scoring_events = self.extract_scoring_data(soup, boxscore_id)
            officials = self.extract_officials_data(soup, boxscore_id)
            defense_stats = self.extract_defense_data(soup, boxscore_id)
            returns_stats = self.extract_returns_data(soup, boxscore_id)
            kicking_stats = self.extract_kicking_punting_data(soup, boxscore_id)
            advanced_passing_stats = self.extract_advanced_passing_data(soup, boxscore_id)
            advanced_rushing_stats = self.extract_advanced_rushing_data(soup, boxscore_id)
            
            # Save to database
            self.save_boxscore_data(boxscore_id, player_stats, team_stats, scoring_events)
            officials_success = self.save_officials_data(officials)
            defense_success = self.save_defense_data(defense_stats)
            returns_success = self.save_returns_data(returns_stats)
            kicking_success = self.save_kicking_punting_data(kicking_stats)
            advanced_passing_success = self.save_advanced_passing_data(advanced_passing_stats)
            advanced_rushing_success = self.save_advanced_rushing_data(advanced_rushing_stats)
            
            success = (officials_success and defense_success and returns_success and 
                      kicking_success and advanced_passing_success and advanced_rushing_success)
            if success:
                logger.info(f"✅ Successfully scraped boxscore: {boxscore_id} (includes defense, officials, returns, kicking, advanced passing & advanced rushing)")
            else:
                logger.warning(f"⚠️  Partially successful scraping: {boxscore_id}")
                
            return True  # Return True if core data was saved, even if extras failed
            
        except Exception as e:
            logger.error(f"❌ Error scraping boxscore {boxscore_id}: {e}")
            return False


def main():
    """Test the fixed scraper"""
    if len(sys.argv) > 1:
        season = int(sys.argv[1])
    else:
        season = 2024
    
    logger.info("🏈 Fixed NFL Boxscore Scraper")
    logger.info("=" * 50)
    logger.info(f"📅 Processing season: {season}")
    
    scraper = FixedNFLBoxscoreScraper()
    
    try:
        # Create database tables
        scraper.create_database_tables()
        
        # Get available boxscore IDs for the specified season
        boxscore_ids = scraper.get_available_boxscore_ids(limit=5, season=season)  # Test with 5 games
        
        if not boxscore_ids:
            logger.warning("⚠️  No boxscore IDs found that need scraping")
            return
        
        logger.info(f"📋 Found {len(boxscore_ids)} boxscores to scrape")
        
        # Scrape each boxscore
        successful_scrapes = 0
        for i, boxscore_id in enumerate(boxscore_ids):
            logger.info(f"🎯 Progress: {i+1}/{len(boxscore_ids)}")
            if scraper.scrape_boxscore_details(boxscore_id):
                successful_scrapes += 1
            
            # Be respectful with delays between requests
            if i < len(boxscore_ids) - 1:
                time.sleep(random.uniform(2, 4))
        
        logger.info(f"🎯 Scraping completed: {successful_scrapes}/{len(boxscore_ids)} successful")
        
        # Show results
        logger.info("\n📊 Final results:")
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM nfl.boxscore_player_stats")
                player_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM nfl.boxscore_team_stats")
                team_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM nfl.boxscore_scoring")
                scoring_count = cursor.fetchone()[0]
                
                logger.info(f"   👥 Player stats: {player_count} records")
                logger.info(f"   🏟️ Team stats: {team_count} records")
                logger.info(f"   🏆 Scoring events: {scoring_count} records")
                    
    except Exception as e:
        logger.error(f"❌ Scraping failed: {e}")
        raise


if __name__ == "__main__":
    main()
