# NFL PostgreSQL Integration

This module provides seamless integration between Pydantic NFL data models and PostgreSQL database storage.

## Features

- **Automatic Table Creation**: Generate PostgreSQL tables directly from Pydantic model schemas
- **Type-Safe Data Operations**: Full validation on insert, update, and query operations
- **Smart Type Mapping**: Automatic conversion between Python/Pydantic types and PostgreSQL types
- **Performance Optimization**: Automatic indexing and query optimization
- **Data Integrity**: Constraints, triggers, and validation ensure data quality

## Quick Start

### 1. Database Setup

```bash
# Set environment variables for database connection
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=sportsdb
export DB_USER=postgres
export DB_PASSWORD=your_password
```

### 2. Create Table and Load Data

```bash
# Full setup: create table and load current season
python nfl_db_util.py setup 2024

# Or step by step:
python nfl_db_util.py create-table
python nfl_db_util.py load-data 2024
```

### 3. Query Data

```bash
# View all teams
python nfl_db_util.py query

# Filter by criteria
python nfl_db_util.py query --where "wins >= 13"
python nfl_db_util.py query --where "conference = 'AFC'"

# Export as CSV
python nfl_db_util.py query --format csv > nfl_teams.csv
```

## Generated Table Schema

The table is automatically generated from the `NFLTeamData` Pydantic model:

```sql
CREATE TABLE IF NOT EXISTS public.nfl_teams (
    id SERIAL PRIMARY KEY,
    team TEXT NOT NULL,
    abbrev TEXT NOT NULL,
    conference VARCHAR(10) CHECK (conference IN ('AFC', 'NFC')) NOT NULL,
    wins INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    win_loss_percentage DECIMAL(10,3) NOT NULL,
    points_for INTEGER NOT NULL,
    points_allowed INTEGER NOT NULL,
    points_differential INTEGER NOT NULL,
    margin_of_victory DECIMAL(10,3) NOT NULL,
    strength_of_schedule DECIMAL(10,3) NOT NULL,
    simple_rating_system DECIMAL(10,3) NOT NULL,
    offensive_srs DECIMAL(10,3) NOT NULL,
    defensive_srs DECIMAL(10,3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Key Features:
- **Primary Key**: Auto-incrementing `id` field
- **Data Types**: Proper PostgreSQL types (TEXT, INTEGER, DECIMAL, VARCHAR)
- **Constraints**: NOT NULL for required fields, CHECK constraints for enums
- **Indexes**: Automatic indexing on `abbrev`, `conference`, and `wins`
- **Timestamps**: Automatic `created_at` and `updated_at` tracking
- **Triggers**: Auto-update `updated_at` on record modification

## Type Mapping

| Pydantic Type | PostgreSQL Type | Notes |
|---------------|-----------------|-------|
| `str` | `TEXT` | Or `VARCHAR(n)` with length constraints |
| `int` | `INTEGER` | |
| `float` | `DECIMAL(10,3)` | Good precision for sports statistics |
| `bool` | `BOOLEAN` | |
| `Enum` | `VARCHAR(n) CHECK(...)` | With validation constraint |
| Required fields | `NOT NULL` | Enforced at database level |

## Programmatic Usage

### Basic Operations

```python
from app.src.nfl.database import (
    create_nfl_teams_table,
    insert_nfl_teams, 
    query_nfl_teams
)
from app.src.nfl.teams import Teams

# Create table
create_nfl_teams_table(drop_if_exists=True)

# Load and insert data
teams = Teams('2024')
models = teams.to_models()
insert_nfl_teams(models, on_conflict="UPDATE")

# Query data
all_teams = query_nfl_teams()
afc_teams = query_nfl_teams("conference = 'AFC'")
contenders = query_nfl_teams("wins >= 13")
```

### Advanced Database Operations

```python
from app.src.nfl.database import PostgreSQLManager

with PostgreSQLManager() as db:
    # Custom queries
    cursor = db._connection.cursor()
    cursor.execute("""
        SELECT conference, AVG(wins) as avg_wins 
        FROM nfl_teams 
        GROUP BY conference
    """)
    results = cursor.fetchall()
    
    # Convert results back to Pydantic models
    teams = db.query_to_models(
        model_class=NFLTeamData,
        table_name="nfl_teams",
        where_clause="simple_rating_system > 5.0"
    )
```

## Data Validation

All data goes through Pydantic validation before database insertion:

- **Type Checking**: Automatic type conversion and validation
- **Range Validation**: Wins/losses must be 0-17, percentages 0.0-1.0
- **Enum Validation**: Conference must be 'AFC' or 'NFC'
- **Data Consistency**: Points differential = Points For - Points Allowed
- **Clean Data**: Automatic removal of asterisks and formatting characters

## Performance Features

- **Indexing**: Automatic indexes on frequently queried fields
- **Batch Operations**: Efficient bulk insert and update operations
- **Connection Pooling**: Context managers for proper connection handling
- **Query Optimization**: Proper use of prepared statements and typed queries

## Error Handling

- **Connection Errors**: Graceful handling of database connectivity issues
- **Validation Errors**: Clear error messages for data validation failures
- **Conflict Resolution**: Configurable handling of duplicate records
- **Transaction Safety**: Automatic rollback on errors

## Dependencies

- `psycopg2-binary`: PostgreSQL adapter for Python
- `pydantic`: Data validation and settings management

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `5432` | Database port |
| `DB_NAME` | `sportsdb` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | `""` | Database password |
