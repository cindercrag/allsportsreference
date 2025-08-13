# Sports Reference Scraping Guidelines

## HTTP Library Requirements

**ALWAYS use pycurl for scraping from sports-reference sites**

Sports-reference.com sites (including pro-football-reference.com, basketball-reference.com, etc.) have anti-scraping measures that block requests from the Python `requests` library and other common HTTP libraries.

### Required Approach

✅ **USE**: `_curl_page()` function from `src.utils.common`
- This function uses pycurl with proper headers to mimic curl behavior
- Successfully bypasses anti-scraping measures
- Already implemented and tested

❌ **DO NOT USE**:
- `requests.get()`
- `urllib.request`
- `httpx`
- `aiohttp`
- Any other HTTP library

### Example Usage

```python
from src.utils.common import _curl_page

# Correct way to fetch sports-reference data
html_content = _curl_page(url="https://www.pro-football-reference.com/years/2023/")
soup = BeautifulSoup(html_content, 'html.parser')
```

### Why This Matters

- Sports-reference sites return 403 Forbidden errors for requests library
- pycurl successfully mimics command-line curl behavior
- Maintains respectful scraping practices with proper delays
- Ensures reliable data collection for all sports modules

### Current Implementation Status

✅ **Already Using pycurl**:
- NFL team data (`_retrieve_all_teams`)
- NFL schedule data 
- Advanced boxscore scraper (`nfl_boxscore_scraper.py`)

⚠️ **Needs Update**:
- URL validation function (`_url_exists` in common.py)

## Best Practices

1. Always add random delays between requests (1-3 seconds)
2. Use proper user-agent headers (handled by `_curl_page`)
3. Handle gzip/deflate compression (handled by `_curl_page`)
4. Parse HTML comments for hidden data tables
5. Implement error handling for network failures
