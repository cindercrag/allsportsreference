-- PostgreSQL Database Setup Script
-- Run this script to set up the sports database structure

-- Create the main database (run this as postgres superuser)
-- CREATE DATABASE sportsdb;

-- Connect to sportsdb and run the following:

-- Create schemas for different sports
CREATE SCHEMA IF NOT EXISTS nfl;
CREATE SCHEMA IF NOT EXISTS nba;
CREATE SCHEMA IF NOT EXISTS ncaaf;  -- College Football
CREATE SCHEMA IF NOT EXISTS ncaab;  -- College Basketball (Men's and Women's)
CREATE SCHEMA IF NOT EXISTS nhl;    -- National Hockey League
CREATE SCHEMA IF NOT EXISTS mlb;    -- For future expansion

-- Example: Create a partitioned schedule table for NFL
CREATE TABLE IF NOT EXISTS nfl.schedule (
    season INTEGER NOT NULL,
    week INTEGER,
    date DATE,
    team VARCHAR(10),
    opponent VARCHAR(10),
    home_away VARCHAR(1),
    result VARCHAR(50),
    points_scored INTEGER,
    points_allowed INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (season);

-- Create partitions for specific seasons
CREATE TABLE IF NOT EXISTS nfl.schedule_2024
    PARTITION OF nfl.schedule
    FOR VALUES FROM (2024) TO (2025);

CREATE TABLE IF NOT EXISTS nfl.schedule_2025
    PARTITION OF nfl.schedule
    FOR VALUES FROM (2025) TO (2026);

-- Example: Create a partitioned roster table for NFL
CREATE TABLE IF NOT EXISTS nfl.roster (
    season INTEGER NOT NULL,
    team VARCHAR(10),
    player VARCHAR(100),
    position VARCHAR(10),
    number INTEGER,
    height VARCHAR(10),
    weight INTEGER,
    age INTEGER,
    experience INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (season);

-- Create partitions for specific seasons
CREATE TABLE IF NOT EXISTS nfl.roster_2024
    PARTITION OF nfl.roster
    FOR VALUES FROM (2024) TO (2025);

CREATE TABLE IF NOT EXISTS nfl.roster_2025
    PARTITION OF nfl.roster
    FOR VALUES FROM (2025) TO (2026);

-- Example: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_nfl_schedule_team_season 
    ON nfl.schedule (team, season);

CREATE INDEX IF NOT EXISTS idx_nfl_schedule_date 
    ON nfl.schedule (date);

CREATE INDEX IF NOT EXISTS idx_nfl_roster_team_season 
    ON nfl.roster (team, season);

-- Create indexes for NCAAF
CREATE INDEX IF NOT EXISTS idx_ncaaf_schedule_team_season 
    ON ncaaf.schedule (team, season);

CREATE INDEX IF NOT EXISTS idx_ncaaf_schedule_date 
    ON ncaaf.schedule (date);

CREATE INDEX IF NOT EXISTS idx_ncaaf_schedule_conference 
    ON ncaaf.schedule (conference, season);

-- Create indexes for NCAAB (both men's and women's)
CREATE INDEX IF NOT EXISTS idx_ncaab_schedule_team_season_league 
    ON ncaab.schedule (team, season, league);

CREATE INDEX IF NOT EXISTS idx_ncaab_schedule_date 
    ON ncaab.schedule (date);

CREATE INDEX IF NOT EXISTS idx_ncaab_schedule_conference_league 
    ON ncaab.schedule (conference, season, league);

CREATE INDEX IF NOT EXISTS idx_ncaab_schedule_tournament_league 
    ON ncaab.schedule (tournament, season, league);

-- Create indexes for NHL
CREATE INDEX IF NOT EXISTS idx_nhl_schedule_team_season 
    ON nhl.schedule (team, season);

CREATE INDEX IF NOT EXISTS idx_nhl_schedule_date 
    ON nhl.schedule (date);

-- Example: Create similar structure for NBA
CREATE TABLE IF NOT EXISTS nba.schedule (
    season INTEGER NOT NULL,
    date DATE,
    team VARCHAR(10),
    opponent VARCHAR(10),
    home_away VARCHAR(1),
    result VARCHAR(50),
    points_scored INTEGER,
    points_allowed INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (season);

CREATE TABLE IF NOT EXISTS nba.schedule_2024
    PARTITION OF nba.schedule
    FOR VALUES FROM (2024) TO (2025);

-- Example: Create similar structure for NCAAF
CREATE TABLE IF NOT EXISTS ncaaf.schedule (
    season INTEGER NOT NULL,
    week INTEGER,
    date DATE,
    team VARCHAR(50),     -- College team names can be longer
    opponent VARCHAR(50),
    home_away VARCHAR(1),
    result VARCHAR(50),
    points_scored INTEGER,
    points_allowed INTEGER,
    conference VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (season);

CREATE TABLE IF NOT EXISTS ncaaf.schedule_2024
    PARTITION OF ncaaf.schedule
    FOR VALUES FROM (2024) TO (2025);

-- Example: Create similar structure for NCAAB (supports both men's and women's)
CREATE TABLE IF NOT EXISTS ncaab.schedule (
    season INTEGER NOT NULL,
    league VARCHAR(10) NOT NULL,  -- 'men' or 'women'
    date DATE,
    team VARCHAR(50),
    opponent VARCHAR(50),
    home_away VARCHAR(1),
    result VARCHAR(50),
    points_scored INTEGER,
    points_allowed INTEGER,
    conference VARCHAR(50),
    tournament BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (season);

CREATE TABLE IF NOT EXISTS ncaab.schedule_2024
    PARTITION OF ncaab.schedule
    FOR VALUES FROM (2024) TO (2025);

-- Example: Create similar structure for NHL
CREATE TABLE IF NOT EXISTS nhl.schedule (
    season INTEGER NOT NULL,
    date DATE,
    team VARCHAR(10),
    opponent VARCHAR(10),
    home_away VARCHAR(1),
    result VARCHAR(50),
    goals_scored INTEGER,
    goals_allowed INTEGER,
    overtime VARCHAR(10),
    shootout BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (season);

CREATE TABLE IF NOT EXISTS nhl.schedule_2024
    PARTITION OF nhl.schedule
    FOR VALUES FROM (2024) TO (2025);

-- Create a user for the application (optional)
-- CREATE USER sportsapp WITH PASSWORD 'your_secure_password';
-- GRANT USAGE ON SCHEMA nfl, nba, ncaaf, ncaab, nhl TO sportsapp;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA nfl TO sportsapp;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA nba TO sportsapp;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ncaaf TO sportsapp;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ncaab TO sportsapp;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA nhl TO sportsapp;

-- Show the created structure
\dn  -- List schemas
\dt nfl.*    -- List tables in nfl schema
\dt nba.*    -- List tables in nba schema
\dt ncaaf.*  -- List tables in ncaaf schema
\dt ncaab.*  -- List tables in ncaab schema
\dt nhl.*    -- List tables in nhl schema
