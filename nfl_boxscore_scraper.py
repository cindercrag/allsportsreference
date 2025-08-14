#!/usr/bin/env python3
"""
NFL Advanced Boxscore Detail Scraper

This module scrapes detailed boxscore statistics from pro-football-reference.com
using the boxscore IDs stored in our database. It extracts comprehensive data including:

- Player-level passing, rushing, receiving stats
- Defensive statistics by player  
- Team-level advanced metrics
- Drive summaries
- Play-by-play data
- Snap counts
- Scoring details

The data is stored in new database tables linked by boxscore_id for advanced analysis.
"""

import sys
import os
import logging
from bs4 import BeautifulSoup, Comment
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
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

from src.nfl.database import PostgreSQLManager
from src.utils.common import _curl_page, export_dataframe_to_csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

@dataclass
class BoxscorePlayerStats:
    """Player-level statistics from boxscore"""
    boxscore_id: str
    player_name: str
    team: str
    
    # Passing stats
    pass_cmp: Optional[int] = None
    pass_att: Optional[int] = None
    pass_yds: Optional[int] = None
    pass_td: Optional[int] = None
    pass_int: Optional[int] = None
    pass_sacks: Optional[int] = None
    pass_sack_yds: Optional[int] = None
    pass_rating: Optional[float] = None
    
    # Rushing stats
    rush_att: Optional[int] = None
    rush_yds: Optional[int] = None
    rush_td: Optional[int] = None
    rush_long: Optional[int] = None
    
    # Receiving stats
    rec_tgt: Optional[int] = None
    rec_rec: Optional[int] = None
    rec_yds: Optional[int] = None
    rec_td: Optional[int] = None
    rec_long: Optional[int] = None
    
    # Defensive stats
    def_tackles: Optional[int] = None
    def_assists: Optional[int] = None
    def_sacks: Optional[float] = None
    def_int: Optional[int] = None
    def_int_yds: Optional[int] = None
    def_int_td: Optional[int] = None
    def_pd: Optional[int] = None
    def_ff: Optional[int] = None
    def_fr: Optional[int] = None

@dataclass 
class BoxscoreTeamStats:
    """Team-level advanced statistics"""
    boxscore_id: str
    team: str
    
    # Basic team stats
    first_downs: Optional[int] = None
    total_yards: Optional[int] = None
    passing_yards: Optional[int] = None
    rushing_yards: Optional[int] = None
    turnovers: Optional[int] = None
    penalties: Optional[int] = None
    penalty_yards: Optional[int] = None
    time_of_possession: Optional[str] = None
    
    # Advanced metrics
    third_down_conversions: Optional[str] = None
    fourth_down_conversions: Optional[str] = None
    red_zone_conversions: Optional[str] = None

@dataclass
class BoxscoreScoring:
    """Scoring events from the game"""
    boxscore_id: str
    quarter: int
    time_remaining: str
    team: str
    description: str
    score_home: int
    score_away: int

@dataclass
class BoxscoreDrive:
    """Drive summary data"""
    boxscore_id: str
    team: str
    quarter: int
    start_time: str
    start_field: str
    plays: int
    duration: str
    yards: int
    result: str

class NFLBoxscoreScraper:
    """Scraper for detailed NFL boxscore data from pro-football-reference.com"""
    
    def __init__(self):
        self.base_url = "https://www.pro-football-reference.com/boxscores/"
        self.db = PostgreSQLManager()
        
    def get_boxscore_url(self, boxscore_id: str) -> str:
        """Generate the full URL for a boxscore ID"""
        return f"{self.base_url}{boxscore_id}.htm"
    
    def fetch_boxscore_html(self, boxscore_id: str) -> Optional[BeautifulSoup]:
        """Fetch and parse the boxscore HTML using pycurl"""
        url = self.get_boxscore_url(boxscore_id)
        
        try:
            logger.info(f"🌐 Fetching boxscore: {boxscore_id}")
            
            # Add random delay to be respectful
            time.sleep(random.uniform(1, 3))
            
            # Use pycurl via the existing utility function
            html_content = _curl_page(url=url)
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract content from HTML comments (common in sports-reference sites)
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                try:
                    comment_soup = BeautifulSoup(comment, 'html.parser')
                    # Replace the comment with parsed content
                    comment.replace_with(comment_soup)
                except:
                    continue
            
            logger.info(f"✅ Successfully fetched boxscore: {boxscore_id}")
            return soup
            
        except Exception as e:
            logger.error(f"❌ Error fetching boxscore {boxscore_id}: {e}")
            return None
    
    def extract_team_stats(self, soup: BeautifulSoup, boxscore_id: str) -> List[BoxscoreTeamStats]:
        """Extract team-level statistics from HTML comments"""
        team_stats = []
        
        try:
            # Team stats are in HTML comments
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            
            for comment in comments:
                if 'team_stats' in comment:
                    comment_soup = BeautifulSoup(comment, 'html.parser')
                    team_stats_table = comment_soup.find('table', {'id': 'team_stats'})
                    
                    if team_stats_table:
                        # Get team names from header row
                        header_row = team_stats_table.find('tr')
                        if header_row:
                            header_cells = header_row.find_all(['th', 'td'])
                            if len(header_cells) >= 3:
                                team1 = header_cells[1].get_text(strip=True)
                                team2 = header_cells[2].get_text(strip=True)
                        
                        # Parse each stat row
                        stats_data = {team1: {}, team2: {}}
                        rows = team_stats_table.find_all('tr')[1:]  # Skip header
                        
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 3:
                                stat_name = cells[0].get_text(strip=True)
                                team1_value = cells[1].get_text(strip=True)
                                team2_value = cells[2].get_text(strip=True)
                                
                                stats_data[team1][stat_name] = team1_value
                                stats_data[team2][stat_name] = team2_value
                        
                        # Create BoxscoreTeamStats objects for both teams
                        for team in [team1, team2]:
                            data = stats_data[team]
                            
                            # Parse rushing yards from "Rush-Yds-TDs" format
                            rushing_yards = None
                            if "Rush-Yds-TDs" in data:
                                rush_parts = data["Rush-Yds-TDs"].split('-')
                                if len(rush_parts) >= 2:
                                    rushing_yards = self._safe_int(rush_parts[1])
                            
                            # Parse penalties from "Penalties-Yards" format  
                            penalties = None
                            penalty_yards = None
                            if "Penalties-Yards" in data:
                                pen_parts = data["Penalties-Yards"].split('-')
                                if len(pen_parts) >= 2:
                                    penalties = self._safe_int(pen_parts[0])
                                    penalty_yards = self._safe_int(pen_parts[1])
                            
                            team_stat = BoxscoreTeamStats(
                                boxscore_id=boxscore_id,
                                team=team,
                                first_downs=self._safe_int(data.get('First Downs')),
                                total_yards=self._safe_int(data.get('Total Yards')),
                                passing_yards=self._safe_int(data.get('Net Pass Yards')),
                                rushing_yards=rushing_yards,
                                turnovers=self._safe_int(data.get('Turnovers')),
                                penalties=penalties,
                                penalty_yards=penalty_yards,
                                time_of_possession=data.get('Time of Possession'),
                                third_down_conversions=data.get('Third Down Conv.'),
                                fourth_down_conversions=data.get('Fourth Down Conv.'),
                            )
                            team_stats.append(team_stat)
                        break
                        
            logger.info(f"📊 Extracted team stats for {len(team_stats)} teams")
            
        except Exception as e:
            logger.error(f"❌ Error extracting team stats for {boxscore_id}: {e}")
        
        return team_stats
    
    def extract_player_stats(self, soup: BeautifulSoup, boxscore_id: str) -> List[BoxscorePlayerStats]:
        """Extract player-level statistics"""
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
            
            # Find column indices for stats we want
            col_indices = {}
            for i, header in enumerate(header_text):
                if header == 'Player':
                    col_indices['player'] = i
                elif header == 'Tm':
                    col_indices['team'] = i
                elif header == 'Cmp':
                    col_indices['pass_cmp'] = i
                elif header == 'Att' and 'pass_att' not in col_indices:
                    col_indices['pass_att'] = i
                elif header == 'Yds' and 'pass_yds' not in col_indices:
                    col_indices['pass_yds'] = i
                elif header == 'TD' and 'pass_td' not in col_indices:
                    col_indices['pass_td'] = i
                elif header == 'Int':
                    col_indices['pass_int'] = i
            
            # Find rushing and receiving column indices (they appear after passing)
            passing_end = max([v for k, v in col_indices.items() if 'pass' in k], default=0)
            
            for i in range(passing_end + 1, len(header_text)):
                header = header_text[i]
                if header == 'Att' and 'rush_att' not in col_indices:
                    col_indices['rush_att'] = i
                elif header == 'Yds' and 'rush_yds' not in col_indices:
                    col_indices['rush_yds'] = i
                elif header == 'TD' and 'rush_td' not in col_indices:
                    col_indices['rush_td'] = i
                elif header == 'Rec':
                    col_indices['rec_rec'] = i
                elif header == 'Yds' and 'rec_yds' not in col_indices and 'rec_rec' in col_indices:
                    col_indices['rec_yds'] = i
                elif header == 'TD' and 'rec_td' not in col_indices and 'rec_rec' in col_indices:
                    col_indices['rec_td'] = i
                elif header == 'Tgt':
                    col_indices['rec_tgt'] = i
            
            # Parse player rows
            tbody = player_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < max(col_indices.values(), default=0) + 1:
                        continue
                    
                    # Extract player data
                    player_name = cells[col_indices.get('player', 0)].get_text(strip=True)
                    team = cells[col_indices.get('team', 1)].get_text(strip=True)
                    
                    if not player_name or not team:
                        continue
                    
                    # Create player stat object
                    player_stat = BoxscorePlayerStats(
                        boxscore_id=boxscore_id,
                        player_name=player_name,
                        team=team,
                        pass_cmp=self._safe_int(cells[col_indices.get('pass_cmp', -1)].get_text(strip=True)) if col_indices.get('pass_cmp', -1) >= 0 else None,
                        pass_att=self._safe_int(cells[col_indices.get('pass_att', -1)].get_text(strip=True)) if col_indices.get('pass_att', -1) >= 0 else None,
                        pass_yds=self._safe_int(cells[col_indices.get('pass_yds', -1)].get_text(strip=True)) if col_indices.get('pass_yds', -1) >= 0 else None,
                        pass_td=self._safe_int(cells[col_indices.get('pass_td', -1)].get_text(strip=True)) if col_indices.get('pass_td', -1) >= 0 else None,
                        pass_int=self._safe_int(cells[col_indices.get('pass_int', -1)].get_text(strip=True)) if col_indices.get('pass_int', -1) >= 0 else None,
                        rush_att=self._safe_int(cells[col_indices.get('rush_att', -1)].get_text(strip=True)) if col_indices.get('rush_att', -1) >= 0 else None,
                        rush_yds=self._safe_int(cells[col_indices.get('rush_yds', -1)].get_text(strip=True)) if col_indices.get('rush_yds', -1) >= 0 else None,
                        rush_td=self._safe_int(cells[col_indices.get('rush_td', -1)].get_text(strip=True)) if col_indices.get('rush_td', -1) >= 0 else None,
                        rec_tgt=self._safe_int(cells[col_indices.get('rec_tgt', -1)].get_text(strip=True)) if col_indices.get('rec_tgt', -1) >= 0 else None,
                        rec_rec=self._safe_int(cells[col_indices.get('rec_rec', -1)].get_text(strip=True)) if col_indices.get('rec_rec', -1) >= 0 else None,
                        rec_yds=self._safe_int(cells[col_indices.get('rec_yds', -1)].get_text(strip=True)) if col_indices.get('rec_yds', -1) >= 0 else None,
                        rec_td=self._safe_int(cells[col_indices.get('rec_td', -1)].get_text(strip=True)) if col_indices.get('rec_td', -1) >= 0 else None,
                        def_tackles=None,  # Would need defensive table
                        def_assists=None,
                        def_sacks=None
                    )
                    player_stats.append(player_stat)
            
            logger.info(f"👥 Extracted stats for {len(player_stats)} players")
            
        except Exception as e:
            logger.error(f"❌ Error extracting player stats for {boxscore_id}: {e}")
        
        return player_stats
    
    def extract_scoring_data(self, soup: BeautifulSoup, boxscore_id: str) -> List[BoxscoreScoring]:
        """Extract scoring events timeline"""
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
                        quarter = cells[0].get_text(strip=True)
                        time_remaining = cells[1].get_text(strip=True)
                        team = cells[2].get_text(strip=True)
                        description = cells[3].get_text(strip=True)
                        score_home = self._safe_int(cells[4].get_text(strip=True))
                        score_away = self._safe_int(cells[5].get_text(strip=True))
                        
                        # Only add if we have a quarter (skip empty rows)
                        if quarter:
                            scoring_event = BoxscoreScoring(
                                boxscore_id=boxscore_id,
                                quarter=self._safe_int(quarter),
                                time_remaining=time_remaining,
                                team=team,
                                description=description,
                                score_home=score_home,
                                score_away=score_away
                            )
                            scoring_events.append(scoring_event)
            
            logger.info(f"🏆 Extracted {len(scoring_events)} scoring events")
            
        except Exception as e:
            logger.error(f"❌ Error extracting scoring data for {boxscore_id}: {e}")
        
        return scoring_events
    
    def _parse_offensive_stats(self, table, boxscore_id: str) -> List[BoxscorePlayerStats]:
        """Parse offensive statistics table"""
        stats = []
        
        try:
            rows = table.find('tbody').find_all('tr')
            current_team = None
            
            for row in rows:
                # Check if this is a team header row
                if 'thead' in row.get('class', []) or row.find('th'):
                    team_header = row.find('th')
                    if team_header and len(team_header.get_text().strip()) == 3:
                        current_team = team_header.get_text().strip()
                    continue
                
                cells = row.find_all('td')
                if len(cells) < 2 or not current_team:
                    continue
                
                player_name = cells[0].get_text().strip()
                if not player_name:
                    continue
                
                # Extract stats based on available columns
                player_stat = BoxscorePlayerStats(
                    boxscore_id=boxscore_id,
                    player_name=player_name,
                    team=current_team
                )
                
                # Parse passing stats (columns vary by position)
                if len(cells) > 4:  # Likely has passing stats
                    try:
                        player_stat.pass_cmp = self._safe_int(cells[1].get_text())
                        player_stat.pass_att = self._safe_int(cells[2].get_text())
                        player_stat.pass_yds = self._safe_int(cells[3].get_text())
                        player_stat.pass_td = self._safe_int(cells[4].get_text())
                        if len(cells) > 5:
                            player_stat.pass_int = self._safe_int(cells[5].get_text())
                    except:
                        pass
                
                stats.append(player_stat)
                
        except Exception as e:
            logger.error(f"❌ Error parsing offensive stats: {e}")
        
        return stats
    
    def _parse_defensive_stats(self, table, boxscore_id: str) -> List[BoxscorePlayerStats]:
        """Parse defensive statistics table"""
        stats = []
        
        try:
            rows = table.find('tbody').find_all('tr')
            current_team = None
            
            for row in rows:
                # Check if this is a team header row
                if 'thead' in row.get('class', []) or row.find('th'):
                    team_header = row.find('th')
                    if team_header and len(team_header.get_text().strip()) == 3:
                        current_team = team_header.get_text().strip()
                    continue
                
                cells = row.find_all('td')
                if len(cells) < 2 or not current_team:
                    continue
                
                player_name = cells[0].get_text().strip()
                if not player_name:
                    continue
                
                # Extract defensive stats
                player_stat = BoxscorePlayerStats(
                    boxscore_id=boxscore_id,
                    player_name=player_name,
                    team=current_team
                )
                
                try:
                    if len(cells) > 1:
                        player_stat.def_tackles = self._safe_int(cells[1].get_text())
                    if len(cells) > 2:
                        player_stat.def_assists = self._safe_int(cells[2].get_text())
                    if len(cells) > 3:
                        player_stat.def_sacks = self._safe_float(cells[3].get_text())
                except:
                    pass
                
                stats.append(player_stat)
                
        except Exception as e:
            logger.error(f"❌ Error parsing defensive stats: {e}")
        
        return stats
    
    def _safe_int(self, value: str) -> Optional[int]:
        """Safely convert string to int"""
        if not value or value.strip() == '' or value.strip() == '--':
            return None
        try:
            return int(value.strip())
        except:
            return None
    
    def _safe_float(self, value: str) -> Optional[float]:
        """Safely convert string to float"""
        if not value or value.strip() == '' or value.strip() == '--':
            return None
        try:
            return float(value.strip())
        except:
            return None
    
    def create_database_tables(self):
        """Create database tables for advanced boxscore data"""
        logger.info("🗄️  Creating advanced boxscore database tables...")
        
        # Player stats table
        player_stats_sql = """
        CREATE TABLE IF NOT EXISTS nfl.boxscore_player_stats (
            id SERIAL PRIMARY KEY,
            boxscore_id VARCHAR(20) NOT NULL,
            player_name VARCHAR(100) NOT NULL,
            team VARCHAR(3) NOT NULL,
            
            -- Passing stats
            pass_cmp INTEGER,
            pass_att INTEGER,
            pass_yds INTEGER,
            pass_td INTEGER,
            pass_int INTEGER,
            pass_sacks INTEGER,
            pass_sack_yds INTEGER,
            pass_rating DECIMAL(5,1),
            
            -- Rushing stats
            rush_att INTEGER,
            rush_yds INTEGER,
            rush_td INTEGER,
            rush_long INTEGER,
            
            -- Receiving stats
            rec_tgt INTEGER,
            rec_rec INTEGER,
            rec_yds INTEGER,
            rec_td INTEGER,
            rec_long INTEGER,
            
            -- Defensive stats
            def_tackles INTEGER,
            def_assists INTEGER,
            def_sacks DECIMAL(3,1),
            def_int INTEGER,
            def_int_yds INTEGER,
            def_int_td INTEGER,
            def_pd INTEGER,
            def_ff INTEGER,
            def_fr INTEGER,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT fk_player_boxscore 
                FOREIGN KEY (boxscore_id) 
                REFERENCES nfl.game_logs(boxscore_id)
                ON DELETE CASCADE,
                
            CONSTRAINT unique_player_boxscore 
                UNIQUE (boxscore_id, player_name, team)
        );
        
        CREATE INDEX IF NOT EXISTS idx_player_stats_boxscore ON nfl.boxscore_player_stats(boxscore_id);
        CREATE INDEX IF NOT EXISTS idx_player_stats_player ON nfl.boxscore_player_stats(player_name);
        CREATE INDEX IF NOT EXISTS idx_player_stats_team ON nfl.boxscore_player_stats(team);
        """
        
        # Team stats table
        team_stats_sql = """
        CREATE TABLE IF NOT EXISTS nfl.boxscore_team_stats (
            id SERIAL PRIMARY KEY,
            boxscore_id VARCHAR(20) NOT NULL,
            team VARCHAR(3) NOT NULL,
            
            first_downs INTEGER,
            total_yards INTEGER,
            passing_yards INTEGER,
            rushing_yards INTEGER,
            turnovers INTEGER,
            penalties INTEGER,
            penalty_yards INTEGER,
            time_of_possession VARCHAR(10),
            third_down_conversions VARCHAR(10),
            fourth_down_conversions VARCHAR(10),
            red_zone_conversions VARCHAR(10),
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT fk_team_boxscore 
                FOREIGN KEY (boxscore_id) 
                REFERENCES nfl.game_logs(boxscore_id)
                ON DELETE CASCADE,
                
            CONSTRAINT unique_team_boxscore 
                UNIQUE (boxscore_id, team)
        );
        
        CREATE INDEX IF NOT EXISTS idx_team_stats_boxscore ON nfl.boxscore_team_stats(boxscore_id);
        CREATE INDEX IF NOT EXISTS idx_team_stats_team ON nfl.boxscore_team_stats(team);
        """
        
        # Scoring events table
        scoring_sql = """
        CREATE TABLE IF NOT EXISTS nfl.boxscore_scoring (
            id SERIAL PRIMARY KEY,
            boxscore_id VARCHAR(20) NOT NULL,
            quarter INTEGER NOT NULL,
            time_remaining VARCHAR(10),
            team VARCHAR(3) NOT NULL,
            description TEXT,
            score_home INTEGER,
            score_away INTEGER,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT fk_scoring_boxscore 
                FOREIGN KEY (boxscore_id) 
                REFERENCES nfl.game_logs(boxscore_id)
                ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_scoring_boxscore ON nfl.boxscore_scoring(boxscore_id);
        CREATE INDEX IF NOT EXISTS idx_scoring_team ON nfl.boxscore_scoring(team);
        """
        
        try:
            with PostgreSQLManager() as db:
                with db._connection.cursor() as cursor:
                    cursor.execute(player_stats_sql)
                    cursor.execute(team_stats_sql)
                    cursor.execute(scoring_sql)
                    db._connection.commit()
            
            logger.info("✅ Advanced boxscore tables created successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error creating database tables: {e}")
            raise
    
    def save_boxscore_data(self, boxscore_id: str, player_stats: List[BoxscorePlayerStats], 
                          team_stats: List[BoxscoreTeamStats], scoring_events: List[BoxscoreScoring]):
        """Save all boxscore data to database"""
        try:
            with PostgreSQLManager() as db:
                with db._connection.cursor() as cursor:
                    
                    # Save player stats
                    for stat in player_stats:
                        cursor.execute("""
                            INSERT INTO nfl.boxscore_player_stats (
                                boxscore_id, player_name, team, pass_cmp, pass_att, pass_yds, 
                                pass_td, pass_int, rush_att, rush_yds, rush_td, rec_tgt, 
                                rec_rec, rec_yds, rec_td, def_tackles, def_assists, def_sacks
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (boxscore_id, player_name, team) DO UPDATE SET
                                pass_cmp = EXCLUDED.pass_cmp,
                                pass_att = EXCLUDED.pass_att,
                                pass_yds = EXCLUDED.pass_yds,
                                pass_td = EXCLUDED.pass_td,
                                pass_int = EXCLUDED.pass_int,
                                rush_att = EXCLUDED.rush_att,
                                rush_yds = EXCLUDED.rush_yds,
                                rush_td = EXCLUDED.rush_td,
                                rec_tgt = EXCLUDED.rec_tgt,
                                rec_rec = EXCLUDED.rec_rec,
                                rec_yds = EXCLUDED.rec_yds,
                                rec_td = EXCLUDED.rec_td,
                                def_tackles = EXCLUDED.def_tackles,
                                def_assists = EXCLUDED.def_assists,
                                def_sacks = EXCLUDED.def_sacks
                        """, (
                            stat.boxscore_id, stat.player_name, stat.team, stat.pass_cmp,
                            stat.pass_att, stat.pass_yds, stat.pass_td, stat.pass_int,
                            stat.rush_att, stat.rush_yds, stat.rush_td, stat.rec_tgt,
                            stat.rec_rec, stat.rec_yds, stat.rec_td, stat.def_tackles,
                            stat.def_assists, stat.def_sacks
                        ))
                    
                    # Save team stats
                    for stat in team_stats:
                        cursor.execute("""
                            INSERT INTO nfl.boxscore_team_stats (
                                boxscore_id, team, first_downs, total_yards, passing_yards,
                                rushing_yards, turnovers, penalties, penalty_yards,
                                time_of_possession, third_down_conversions, fourth_down_conversions
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (boxscore_id, team) DO UPDATE SET
                                first_downs = EXCLUDED.first_downs,
                                total_yards = EXCLUDED.total_yards,
                                passing_yards = EXCLUDED.passing_yards,
                                rushing_yards = EXCLUDED.rushing_yards,
                                turnovers = EXCLUDED.turnovers,
                                penalties = EXCLUDED.penalties,
                                penalty_yards = EXCLUDED.penalty_yards,
                                time_of_possession = EXCLUDED.time_of_possession,
                                third_down_conversions = EXCLUDED.third_down_conversions,
                                fourth_down_conversions = EXCLUDED.fourth_down_conversions
                        """, (
                            stat.boxscore_id, stat.team, stat.first_downs, stat.total_yards,
                            stat.passing_yards, stat.rushing_yards, stat.turnovers,
                            stat.penalties, stat.penalty_yards, stat.time_of_possession,
                            stat.third_down_conversions, stat.fourth_down_conversions
                        ))
                    
                    # Save scoring events
                    for event in scoring_events:
                        cursor.execute("""
                            INSERT INTO nfl.boxscore_scoring (
                                boxscore_id, quarter, time_remaining, team, description,
                                score_home, score_away
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            event.boxscore_id, event.quarter, event.time_remaining,
                            event.team, event.description, event.score_home, event.score_away
                        ))
                    
                    db._connection.commit()
            
            logger.info(f"💾 Saved boxscore data: {len(player_stats)} players, {len(team_stats)} teams, {len(scoring_events)} scores")
            
        except Exception as e:
            logger.error(f"❌ Error saving boxscore data for {boxscore_id}: {e}")
            raise
    
    def get_available_boxscore_ids(self, limit: int = 5, season: int = None) -> List[str]:
        """Get boxscore IDs from database that need detailed scraping."""
        try:
            with PostgreSQLManager() as db:
                with db._connection.cursor() as cursor:
                    # Get existing game log entries that have boxscore_ids but no detailed stats yet
                    season_filter = ""
                    params = [limit]
                    
                    if season:
                        season_filter = "AND gl.season = %s"
                        params = [season, limit]
                    
                    query = f"""
                        SELECT DISTINCT gl.boxscore_id 
                        FROM nfl.game_logs gl
                        LEFT JOIN nfl.boxscore_player_stats bps ON gl.boxscore_id = bps.boxscore_id
                        WHERE gl.boxscore_id IS NOT NULL 
                        AND gl.boxscore_id != ''
                        AND bps.boxscore_id IS NULL
                        {season_filter}
                        ORDER BY gl.boxscore_id DESC
                        LIMIT %s
                    """
                    
                    if season:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query, (limit,))
                    
                    results = cursor.fetchall()
                    boxscore_ids = [row[0] for row in results]
                    
                    if boxscore_ids:
                        logger.info(f"📋 Found {len(boxscore_ids)} boxscore IDs needing detailed scraping")
                        for bid in boxscore_ids:
                            logger.info(f"   - {bid}")
                    else:
                        logger.info("📋 No boxscore IDs found that need detailed scraping")
                    
                    return boxscore_ids
                    
        except Exception as e:
            logger.error(f"❌ Error getting boxscore IDs: {e}")
            return []
    
    def scrape_boxscore_details(self, boxscore_id: str) -> bool:
        """Scrape detailed statistics for a single boxscore"""
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
            
            # Save to database
            self.save_boxscore_data(boxscore_id, player_stats, team_stats, scoring_events)
            
            logger.info(f"✅ Successfully scraped boxscore: {boxscore_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error scraping boxscore {boxscore_id}: {e}")
            return False

def main():
    """Main function for testing the boxscore scraper"""
    import sys
    
    # Check for season argument
    season = None
    if len(sys.argv) > 1:
        try:
            season = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Invalid season argument: {sys.argv[1]}. Using default.")
    
    logger.info("🏈 NFL Advanced Boxscore Detail Scraper")
    logger.info("=" * 50)
    if season:
        logger.info(f"📅 Processing season: {season}")
    
    scraper = NFLBoxscoreScraper()
    
    try:
        # Create database tables
        scraper.create_database_tables()
        
        # Get available boxscore IDs for the specified season
        boxscore_ids = scraper.get_available_boxscore_ids(limit=20, season=season)  # Process up to 20 games
        
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
            if i < len(boxscore_ids) - 1:  # Don't delay after the last request
                time.sleep(random.uniform(2, 4))
        
        logger.info(f"🎯 Scraping completed: {successful_scrapes}/{len(boxscore_ids)} successful")
        
        # Export to CSV files
        logger.info("\n📤 Exporting data to CSV files...")
        export_csv_data()
        
        # Show some sample results
        logger.info("\n📊 Sample advanced data:")
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                cursor.execute("""
                    SELECT boxscore_id, COUNT(*) as player_count
                    FROM nfl.boxscore_player_stats 
                    GROUP BY boxscore_id 
                    ORDER BY boxscore_id 
                    LIMIT 5
                """)
                results = cursor.fetchall()
                for boxscore_id, count in results:
                    logger.info(f"   📋 {boxscore_id}: {count} player records")
                    
                # Show some scoring data
                cursor.execute("""
                    SELECT COUNT(*) as total_scoring_events,
                           COUNT(DISTINCT boxscore_id) as games_with_scoring
                    FROM nfl.boxscore_scoring
                """)
                scoring_result = cursor.fetchone()
                logger.info(f"   🏆 Total scoring events: {scoring_result[0]} across {scoring_result[1]} games")
        
    except Exception as e:
        logger.error(f"❌ Scraping failed: {e}")
        raise

def export_csv_data():
    """Export all advanced boxscore data to CSV files"""
    import pandas as pd
    from datetime import datetime
    
    try:
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                
                # Export team stats
                cursor.execute("SELECT * FROM nfl.boxscore_team_stats ORDER BY boxscore_id, team")
                team_data = cursor.fetchall()
                
                if team_data:
                    # Get column names
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'nfl' AND table_name = 'boxscore_team_stats'
                        ORDER BY ordinal_position
                    """)
                    team_columns = [row[0] for row in cursor.fetchall()]
                    
                    team_df = pd.DataFrame(team_data, columns=team_columns)
                    export_dataframe_to_csv(
                        team_df, 
                        sport="NFL",
                        data_type="boxscore_team_stats",
                        season=datetime.now().year
                    )
                    logger.info(f"✅ Exported {len(team_df)} team stat records to CSV")
                
                # Export player stats  
                cursor.execute("SELECT * FROM nfl.boxscore_player_stats ORDER BY boxscore_id, team, player_name")
                player_data = cursor.fetchall()
                
                if player_data:
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'nfl' AND table_name = 'boxscore_player_stats'
                        ORDER BY ordinal_position
                    """)
                    player_columns = [row[0] for row in cursor.fetchall()]
                    
                    player_df = pd.DataFrame(player_data, columns=player_columns)
                    export_dataframe_to_csv(
                        player_df,
                        sport="NFL", 
                        data_type="boxscore_player_stats",
                        season=datetime.now().year
                    )
                    logger.info(f"✅ Exported {len(player_df)} player stat records to CSV")
                
                # Export scoring events
                cursor.execute("SELECT * FROM nfl.boxscore_scoring ORDER BY boxscore_id, quarter, time_remaining")
                scoring_data = cursor.fetchall()
                
                if scoring_data:
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'nfl' AND table_name = 'boxscore_scoring'
                        ORDER BY ordinal_position
                    """)
                    scoring_columns = [row[0] for row in cursor.fetchall()]
                    
                    scoring_df = pd.DataFrame(scoring_data, columns=scoring_columns)
                    export_dataframe_to_csv(
                        scoring_df,
                        sport="NFL",
                        data_type="boxscore_scoring", 
                        season=datetime.now().year
                    )
                    logger.info(f"✅ Exported {len(scoring_df)} scoring event records to CSV")
                    
    except Exception as e:
        logger.error(f"❌ Error exporting CSV data: {e}")

if __name__ == "__main__":
    main()
