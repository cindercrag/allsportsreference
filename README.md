# All Sports Reference

A Python application for scraping and analyzing sports data from reference websites. Currently supports NFL, NBA, NCAAF, NCAAB (Men's & Women's), and NHL data with teams, schedules, and statistics.

## Features

- 🏈 **Multi-Sport Support**: NFL, NBA, NCAAF (College Football), NCAAB (Men's & Women's College Basketball), and NHL data scraping
- 📊 **Data Export**: Automated CSV export with organized file structure
- 📖 **Documentation**: Column glossaries for all exported data
- 🗄️ **Database Integration**: PostgreSQL support with schema organization
- 📝 **Comprehensive Logging**: Structured logging with rotation and retention
- ⚙️ **Configuration Management**: Environment-based configuration with .env support
- 🔒 **Security**: Proper credential management and validation

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd allsportsreference
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and preferences
   ```

3. **Run Application**
   ```bash
   python app/main.py
   ```

## Configuration

The application uses environment variables for configuration. See [CONFIGURATION.md](CONFIGURATION.md) for detailed setup instructions.

### Quick Configuration
Create a `.env` file:
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sportsdb
DB_USER=postgres
DB_PASSWORD=your_password

# Logging
LOG_LEVEL=INFO
DEBUG=false

# Directories
DATA_DIR=data
LOGS_DIR=logs
```

## Project Structure

```
allsportsreference/
├── app/
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   └── src/
│       ├── nfl/             # NFL-specific constants and utilities
│       ├── nba/             # NBA-specific constants and utilities
│       ├── ncaaf/           # NCAAF (College Football) constants and utilities
│       ├── ncaab/           # NCAAB (Men's & Women's College Basketball) constants and utilities
│       ├── nhl/             # NHL-specific constants and utilities
│       └── utils/           # Shared utilities
│           ├── common.py    # CSV parsing and export functions
│           └── database.py  # PostgreSQL integration
├── data/                    # Exported CSV files (auto-organized)
├── logs/                    # Application logs
├── .env                     # Environment configuration
├── .env.example             # Configuration template
├── requirements.txt         # Python dependencies
└── CONFIGURATION.md         # Detailed configuration guide
```

## Usage Examples

### Database Operations
```python
from app.src.utils.database import SportsDatabase

# Use configuration from .env
db = SportsDatabase.from_config()

# Create schemas and tables
db.create_schema('nfl')
db.create_partitioned_table('nfl', 'schedule', columns)

# Load CSV data
db.load_csv_to_table('data/nfl/2024/schedule.csv', 'nfl', 'schedule', '2024')
```

### NCAAB Dual-League Support
```python
from app.src.ncaab import constants as ncaab

# Men's basketball URLs
mens_season = ncaab.get_url('season_page', league='men', year=2024)
mens_stats = ncaab.get_url('basic_stats', league='men', year=2024)

# Women's basketball URLs  
womens_season = ncaab.get_url('season_page', league='women', year=2024)
womens_stats = ncaab.get_url('basic_stats', league='women', year=2024)

# Convenience functions
mens_tournament = ncaab.get_mens_url('tournament', year=2024)
womens_tournament = ncaab.get_womens_url('tournament', year=2024)

# League-specific configuration
mens_config = ncaab.get_league_config('men')
womens_config = ncaab.get_league_config('women')
```

### Data Export
```python
from app.src.utils.common import export_dataframe_to_csv

# Export with automatic organization
export_dataframe_to_csv(
    df, 
    sport='nfl', 
    data_type='schedule', 
    season=2024, 
    team='NE'
)
# Saves to: data/nfl/2024/teams/NE/NE_2024_schedule.csv
```

## Dependencies

- **Web Scraping**: requests, lxml, pyquery, beautifulsoup4
- **Data Processing**: pandas
- **Database**: psycopg2-binary, sqlalchemy
- **Logging**: loguru
- **Configuration**: python-dotenv

## Development

### Debug Mode
Enable debug mode in `.env`:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

This will:
- Show detailed configuration on startup
- Enable debug-level logging
- Display additional diagnostic information

### Testing Configuration
```bash
python app/config.py
```

## Sports Supported

### NFL (National Football League)
- Team schedules and game logs
- Season statistics
- Player information
- Boxscores

### NBA (National Basketball Association)  
- Team schedules and game logs
- Season statistics
- Player information
- Boxscores

### NCAAF (College Football)
- Team schedules and game logs
- Conference standings
- Rankings and polls
- Player information
- Boxscores

### NCAAB (College Basketball - Men's & Women's)
- Team schedules and game logs (both leagues)
- Conference standings (men's and women's divisions)
- Rankings and polls
- Player information
- Boxscores
- Tournament brackets (NCAA men's and women's tournaments)
- League-specific URL generation with `league='men'` or `league='women'` parameter

### NHL (National Hockey League)
- Team schedules and game logs
- Season statistics
- Player information
- Boxscores

## File Organization

Data is automatically organized in a hierarchical structure:
```
data/
├── nfl/
│   └── 2024/
│       ├── teams/
│       │   ├── NE/
│       │   │   ├── NE_2024_schedule.csv
│       │   │   └── NE_2024_roster.csv
│       │   └── ...
│       └── weeks/
│           ├── week_1_boxscores.csv
│           └── ...
├── nba/
│   └── 2024/
│       └── teams/
│           ├── LAL/
│           │   ├── LAL_2024_schedule.csv
│           │   └── LAL_2024_roster.csv
│           └── ...
├── ncaaf/
│   └── 2024/
│       └── teams/
│           ├── alabama/
│           │   ├── alabama_2024_schedule.csv
│           │   └── alabama_2024_roster.csv
│           └── ...
├── ncaab/
│   └── 2024/
│       └── teams/
│           ├── duke/
│           │   ├── duke_2024_schedule.csv
│           │   └── duke_2024_roster.csv
│           └── ...
└── nhl/
    └── 2024/
        └── teams/
            ├── BOS/
            │   ├── BOS_2024_schedule.csv
            │   └── BOS_2024_roster.csv
            └── ...
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

## License

[Add your license here]

## Support

For questions or issues:
1. Check [CONFIGURATION.md](CONFIGURATION.md) for configuration help
2. Review the logs in the `logs/` directory
3. Open an issue on GitHub
