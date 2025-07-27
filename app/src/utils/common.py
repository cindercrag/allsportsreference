import re
import requests
from datetime import datetime
from lxml.etree import ParserError, XMLSyntaxError
from pyquery import PyQuery as pq
import pycurl
from io import BytesIO
import gzip
import zlib
import pandas as pd
from bs4 import BeautifulSoup
import sys
from pathlib import Path

# Import configuration
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import config


def _todays_date():
    """
    Get today's date.

    Returns the current date and time. In a standalone function to easily be
    mocked in unit tests.

    Returns
    -------
    datetime.datetime
        The current date and time as a datetime object.
    """
    return datetime.now()


def _url_exists(url):
    """
    Determine if a URL is valid and exists.

    Not every URL that is provided is valid and exists, such as requesting
    stats for a season that hasn't yet begun. In this case, the URL needs to be
    validated prior to continuing any code to ensure no unhandled exceptions
    occur.

    Parameters
    ----------
    url : string
        A string representation of the url to check.

    Returns
    -------
    bool
        Evaluates to True when the URL exists and is valid, otherwise returns
        False.
    """
    try:
        response = requests.head(url)
        if response.status_code == 301:
            response = requests.get(url)
            if response.status_code < 400:
                return True
            else:
                return False
        elif response.status_code < 400:
            return True
        else:
            return False
    except Exception:
        return False



def _parse_abbreviation(uri_link):
    """
    Returns a team's abbreviation.

    A school or team's abbreviation is generally embedded in a URI link which
    contains other relative link information. For example, the URI for the
    New England Patriots for the 2017 season is "/teams/nwe/2017.htm". This
    function strips all of the contents before and after "nwe" and converts it
    to uppercase and returns "NWE".

    Parameters
    ----------
    uri_link : string
        A URI link which contains a team's abbreviation within other link
        contents.

    Returns
    -------
    string
        The shortened uppercase abbreviation for a given team.
    """
    abbr = re.sub(r'/[0-9]+\..*htm.*', '', uri_link('a').attr('href'))
    abbr = re.sub(r'/.*/schools/', '', abbr)
    abbr = re.sub(r'/teams/', '', abbr)
    return abbr.upper()


def _parse_field(parsing_scheme, html_data, field, index=0, strip=False,
                 secondary_index=None):
    """
    Parse an HTML table to find the requested field's value.

    All of the values are passed in an HTML table row instead of as individual
    items. The values need to be parsed by matching the requested attribute
    with a parsing scheme that sports-reference uses to differentiate stats.
    This function returns a single value for the given attribute.

    Parameters
    ----------
    parsing_scheme : dict
        A dictionary of the parsing scheme to be used to find the desired
        field. The key corresponds to the attribute name to parse, and the
        value is a PyQuery-readable parsing scheme as a string (such as
        'td[data-stat="wins"]').
    html_data : string
        A string containing all of the rows of stats for a given team. If
        multiple tables are being referenced, this will be comprised of
        multiple rows in a single string.
    field : string
        The name of the attribute to match. Field must be a key in
        parsing_scheme.
    index : int (optional)
        An optional index if multiple fields have the same attribute name. For
        example, 'HR' may stand for the number of home runs a baseball team has
        hit, or the number of home runs a pitcher has given up. The index
        aligns with the order in which the attributes are recevied in the
        html_data parameter.
    strip : boolean (optional)
        An optional boolean value which will remove any empty or invalid
        elements which might show up during list comprehensions. Specify True
        if the invalid elements should be removed from lists, which can help
        with reverse indexing.
    secondary_index : int (optional)
        An optional index if multiple fields have the same attribute, but the
        original index specified above doesn't work. This happens if a page
        doesn't have all of the intended information, and the requested index
        isn't valid, causing the value to be None. Instead, a secondary index
        could be checked prior to returning None.

    Returns
    -------
    string
        The value at the specified index for the requested field. If no value
        could be found, returns None.
    """
    if field == 'abbreviation':
        return _parse_abbreviation(html_data)
    scheme = parsing_scheme[field]
    if strip:
        items = [i.text() for i in html_data(scheme).items() if i.text()]
    else:
        items = [i.text() for i in html_data(scheme).items()]
    # Stats can be added and removed on a yearly basis. If not stats are found,
    # return None and have the be the value.
    if len(items) == 0:
        return None
    # Default to returning the first element. Optionally return another element
    # if multiple fields have the same tag attribute.
    try:
        return items[index]
    except IndexError:
        if secondary_index:
            try:
                return items[secondary_index]
            except IndexError:
                return None
        return None


def _remove_html_comment_tags(html):
    """
    Returns the passed HTML contents with all comment tags removed while
    keeping the contents within the tags.

    Some pages embed the HTML contents in comments. Since the HTML contents are
    valid, removing the content tags (but not the actual code within the
    comments) will return the desired contents.

    Parameters
    ----------
    html : PyQuery object
        A PyQuery object which contains the requested HTML page contents.

    Returns
    -------
    string
        The passed HTML contents with all comment tags removed.
    """
    return str(html).replace('<!--', '').replace('-->', '')




def _no_data_found():
    """
    Print a message that no data could be found on the page.

    Occasionally, such as right before the beginning of a season, a page will
    return a valid response but will have no data outside of the default
    HTML and CSS template. With no data present on the page, sportsipy
    can't parse any information and should indicate the lack of data and return
    safely.
    """
    print('The requested page returned a valid response, but no data could be '
          'found. Has the season begun, and is the data available on '
          'www.sports-reference.com?')
    return


def _curl_page(url=None, local_file=None):
    """
    Pull data from a local file if it exists, or download data from the website.

    Parameters
    ----------
    url : string (optional)
        A URL to fetch.
    local_file : string (optional)
        Path to a local HTML file to read instead of downloading.

    Returns
    -------
    PyQuery
        A PyQuery object representing the parsed HTML.

    Raises
    ------
    ValueError
        If neither `url` nor `local_file` is provided.
    """

    # Serve from disk if a local file is provided
    if local_file:
        with open(local_file, "r", encoding="utf-8") as fh:
            return fh.read()

    if url:
        buffer = BytesIO()
        c = pycurl.Curl()
        try:
            # Basic request configuration
            c.setopt(c.URL, url)
            c.setopt(c.WRITEDATA, buffer)
            # Imitate command‑line curl and accept compressed responses
            c.setopt(pycurl.USERAGENT, "curl/7.88.1")
            c.setopt(pycurl.HTTPHEADER, [
                "Accept: */*",
                "Accept-Language: en-US,en;q=0.5",
            ])
            c.setopt(pycurl.ACCEPT_ENCODING, "gzip, deflate")

            # Perform the request
            c.perform()
        finally:
            # Always clean up the Curl handle
            c.close()

        # Retrieve the response body
        raw = buffer.getvalue()

        # Attempt to decompress if gzip or deflate encoding was used
        try:
            if raw.startswith(b"\x1f\x8b"):  # gzip magic number
                html = gzip.decompress(raw).decode("utf-8")
            else:
                # zlib.decompress will raise if data isn't compressed
                html = zlib.decompress(raw, 16+zlib.MAX_WBITS).decode("utf-8")
        except Exception:
            html = raw.decode("utf-8", errors="replace")

        return html

    raise ValueError("Expected either a URL or a local data file!")


def generate_export_filename(sport, data_type, season=None, team=None, week=None, 
                           file_format="csv", base_dir=None):
    """
    Generate a standardized filename for exported sports data.
    Uses configuration-based data directory if base_dir is not provided.
    
    Parameters
    ----------
    sport : str
        The sport (e.g., 'nfl', 'nba', 'mlb')
    data_type : str
        The type of data (e.g., 'schedule', 'roster', 'boxscore')
    season : str, optional
        The season/year (e.g., '2024')
    team : str, optional
        The team abbreviation (e.g., 'NE', 'LAL')
    week : str or int, optional
        The week number for weekly data
    file_format : str
        The file format extension (default: 'csv')
    base_dir : str, optional
        Base directory for exports (uses config.data_dir if None)
        
    Returns
    -------
    str
        Full path to the export file
    """
    import os
    from datetime import datetime
    
    # Use config data directory if base_dir not provided
    if base_dir is None:
        base_dir = str(config.data_dir)
    
    # Create base path components
    path_parts = [base_dir, sport.lower()]
    
    # Add season to path if provided
    if season:
        path_parts.append(str(season))
    
    # Build filename components
    filename_parts = []
    
    if team:
        # Team-specific data
        path_parts.extend(['teams', team.upper()])
        filename_parts.extend([team.upper(), str(season) if season else ''])
    elif week:
        # Week-specific data
        path_parts.append('weeks')
        filename_parts.append(f"week_{week}")
    elif season:
        # Season-wide data
        filename_parts.append(str(season))
    
    # Add data type and timestamp
    filename_parts.append(data_type)
    
    # Create directory path
    dir_path = os.path.join(*path_parts)
    
    # Create filename
    filename_base = '_'.join(filter(None, filename_parts))
    filename = f"{filename_base}.{file_format}"
    
    # Full path
    full_path = os.path.join(dir_path, filename)
    
    return full_path


def export_dataframe_to_csv(df, filename=None, sport=None, data_type=None, 
                           season=None, team=None, week=None, include_index=False, 
                           create_dirs=True, base_dir=None):
    """
    Export a pandas DataFrame to a CSV file with automatic filename generation.
    Uses configuration-based data directory if base_dir is not provided.
    
    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to export
    filename : str, optional
        Explicit filename to use. If not provided, will auto-generate based on other params
    sport : str, optional
        The sport (for auto-generation)
    data_type : str, optional  
        Type of data (for auto-generation)
    season : str or int, optional
        The season year (for auto-generation)
    team : str, optional
        Team abbreviation (for auto-generation)
    week : str or int, optional
        Week number (for auto-generation)
    include_index : bool, optional
        Whether to include the DataFrame index in the CSV (default: False)
    create_dirs : bool, optional
        Whether to create directories if they don't exist (default: True)
    base_dir : str, optional
        Base directory for exports (uses config.data_dir if None)
    
    Returns
    -------
    str
        The filename of the exported CSV file
        
    Examples
    --------
    # Explicit filename
    export_dataframe_to_csv(df, filename="my_data.csv")
    
    # Auto-generated filename for team schedule
    export_dataframe_to_csv(df, sport='nfl', data_type='schedule', 
                           season=2024, team='NE')
    
    # Auto-generated filename for weekly boxscores
    export_dataframe_to_csv(df, sport='nfl', data_type='boxscores', 
                           season=2024, week=1)
    """
    import os
    
    # Generate filename if not provided
    if filename is None:
        if not all([sport, data_type]):
            raise ValueError("Must provide either 'filename' or both 'sport' and 'data_type'")
        filename = generate_export_filename(sport, data_type, season, team, week, base_dir=base_dir)
    
    # Create directories if needed
    if create_dirs:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Export the DataFrame
    df.to_csv(filename, index=include_index)
    print(f"DataFrame exported to '{filename}'")
    
    return filename


def export_multiple_dataframes(dataframes_dict, sport, season, team=None, base_dir=None):
    """
    Export multiple DataFrames with consistent naming and organization.
    
    Parameters
    ----------
    dataframes_dict : dict
        Dictionary where keys are data_types and values are DataFrames
        Example: {'schedule': schedule_df, 'roster': roster_df}
    sport : str
        The sport (e.g., 'nfl', 'nba')
    season : str or int
        The season year
    team : str, optional
        Team abbreviation for team-specific exports
    base_dir : str, optional
        Base directory for exports (default: 'data')
    
    Returns
    -------
    dict
        Dictionary mapping data_type to exported filename
        
    Example
    -------
    exported_files = export_multiple_dataframes({
        'schedule': schedule_df,
        'roster': roster_df,
        'stats': stats_df
    }, sport='nfl', season=2024, team='NE')
    """
    exported_files = {}
    
    for data_type, df in dataframes_dict.items():
        if df is not None and not df.empty:
            filename = export_dataframe_to_csv(
                df, 
                sport=sport, 
                data_type=data_type, 
                season=season, 
                team=team
            )
            exported_files[data_type] = filename
        else:
            print(f"Warning: No data to export for {data_type}")
            
    return exported_files


def create_export_summary(exported_files, sport, season, team=None):
    """
    Create a summary report of exported files.
    
    Parameters
    ----------
    exported_files : dict
        Dictionary of data_type -> filename mappings
    sport : str
        The sport
    season : str or int  
        The season year
    team : str, optional
        Team abbreviation
        
    Returns
    -------
    str
        Path to the summary file
    """
    from datetime import datetime
    import os
    
    # Generate summary filename
    summary_filename = generate_export_filename(
        sport, 'export_summary', season, team, file_format='txt'
    )
    
    # Create summary content
    summary_content = f"# Export Summary\n"
    summary_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    summary_content += f"Sport: {sport.upper()}\n"
    summary_content += f"Season: {season}\n"
    if team:
        summary_content += f"Team: {team}\n"
    summary_content += f"\n## Exported Files ({len(exported_files)}):\n\n"
    
    for data_type, filepath in exported_files.items():
        file_size = "Unknown"
        if os.path.exists(filepath):
            file_size = f"{os.path.getsize(filepath):,} bytes"
        summary_content += f"- {data_type}: {filepath} ({file_size})\n"
    
    # Create directory and write summary
    os.makedirs(os.path.dirname(summary_filename), exist_ok=True)
    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print(f"Export summary saved to '{summary_filename}'")
    return summary_filename


def save_glossary(glossary, headers, sport="NFL", season=None, team=None, 
                 filename=None, data_type="glossary", base_dir=None):
    """
    Save column glossary to a markdown file using the same organization as CSV exports.
    
    Parameters
    ----------
    glossary : dict
        Dictionary of column names and their definitions
    headers : list
        List of all column headers
    sport : str, optional
        The sport (default: "NFL")
    season : str or int, optional
        The season year (for organized file placement)
    team : str, optional
        Team abbreviation (for team-specific glossaries)
    filename : str, optional
        Explicit filename to use. If not provided, will auto-generate
    data_type : str, optional
        Type of data for the glossary (default: "glossary")
        
    Returns
    -------
    tuple
        (defined_count, undefined_count, filename) - Counts and saved filename
    """
    import os
    
    # Generate filename using the same system as CSV exports
    if filename is None:
        filename = generate_export_filename(
            sport.lower(), data_type, season, team, file_format='md', base_dir=base_dir
        )
    
    # Create directory if needed
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Save glossary to a file
    glossary_content = f"# {sport.upper()} Column Glossary\n\n"
    if season:
        glossary_content += f"**Season:** {season}\n"
    if team:
        glossary_content += f"**Team:** {team}\n"
    glossary_content += f"\nThis file contains definitions for the columns in the {sport.upper()} data.\n\n"

    for col, definition in sorted(glossary.items()):
        glossary_content += f"**{col}**: {definition}\n\n"

    # Also add any columns without definitions
    undefined_cols = [col for col in headers if col not in glossary and col]
    if undefined_cols:
        glossary_content += "## Columns without definitions:\n\n"
        for col in undefined_cols:
            glossary_content += f"**{col}**: (Definition not available)\n\n"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(glossary_content)
    
    print(f"Glossary saved to '{filename}'")
    return len(glossary), len(undefined_cols), filename


def parse_table(html_content, table_id, output_filename=None, sport=None, 
               data_type=None, season=None, team=None, week=None, 
               save_glossary_file=True):
    """
    Parse a table from HTML content and return a pandas DataFrame.
    
    Parameters
    ----------
    html_content : str
        The HTML content containing the table
    table_id : str
        The ID of the table to parse
    output_filename : str, optional
        Explicit filename to use for export
    sport : str, optional
        The sport (for auto-generated filename)
    data_type : str, optional
        Type of data (for auto-generated filename)
    season : str or int, optional
        The season year (for auto-generated filename)
    team : str, optional
        Team abbreviation (for auto-generated filename)
    week : str or int, optional
        Week number (for auto-generated filename)
    save_glossary_file : bool, optional
        Whether to save the glossary to a file when exporting (default: True)
    
    Returns
    -------
    tuple
        (DataFrame, glossary_dict) - The parsed data and column definitions
        
    Examples
    --------
    # Basic usage
    df, glossary = parse_table(html, 'game-log')
    
    # With auto-generated export and glossary
    df, glossary = parse_table(html, 'game-log', sport='nfl', 
                              data_type='schedule', season=2024, team='NE')
    """
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, "lxml")
    
    # Find the specified table by its id
    table = soup.find("table", id=table_id)
    if not table:
        raise ValueError(f"Table with id '{table_id}' not found")
    
    # Extract the rows from the table body
    rows = table.find("tbody").find_all("tr")
    
    # Get all header rows to handle multi-level headers
    thead = table.find("thead")
    header_rows = thead.find_all("tr")
    
    # Build column names from multi-level headers and extract tooltips
    headers = []
    glossary = {}
    
    if len(header_rows) >= 2:
        # Get both header rows for group titles and specific column names
        group_headers = header_rows[0].find_all(["th", "td"])
        detailed_headers = header_rows[1].find_all(["th", "td"])
        
        # Build a mapping of column positions to group names
        group_mapping = []
        
        for group_th in group_headers:
            group_text = group_th.get_text(strip=True).lower()
            colspan = int(group_th.get('colspan', 1))
            
            # Add this group name to the mapping for each column it spans
            for _ in range(colspan):
                group_mapping.append(group_text)
        
        # Now build column names using group prefixes
        for i, th in enumerate(detailed_headers):
            header_text = th.get_text(strip=True)
            
            # Extract tooltip/title attribute for glossary
            tooltip = th.get('title', '') or th.get('data-tip', '') or th.get('aria-label', '')
            
            # Get the group prefix for this column
            group_prefix = group_mapping[i] if i < len(group_mapping) else ""
            
            if header_text:
                # Create prefixed column name if we have a meaningful group
                if group_prefix and group_prefix not in ['', 'unnamed: 0_level_0']:
                    column_name = f"{group_prefix}_{header_text.lower()}"
                else:
                    column_name = header_text
                
                headers.append(column_name)
                if tooltip:
                    glossary[column_name] = tooltip
            else:
                # Handle special case for location column (position 5 in game logs)
                if i == 5 and 'game-log' in table_id:  
                    col_name = "home_away"
                    headers.append(col_name)
                    glossary[col_name] = "Game location: empty string ('') indicates home game, '@' indicates away game"
                else:
                    col_name = f"Col_{len(headers)}"
                    headers.append(col_name)
                    if tooltip:
                        glossary[col_name] = tooltip
    else:
        # Fallback to first row
        header_row = header_rows[0]
        for th in header_row.find_all(["th", "td"]):
            header_text = th.get_text(strip=True)
            tooltip = th.get('title', '') or th.get('data-tip', '') or th.get('aria-label', '')
            
            headers.append(header_text)
            if tooltip:
                glossary[header_text] = tooltip
    
    # Convert each row into a list of text values
    data = []
    for row in rows:
        cells = [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
        if cells and not all(cell == '' for cell in cells):  # Skip empty rows
            data.append(cells)
    
    # Make sure headers and data have same number of columns
    if data and len(headers) != len(data[0]):
        if len(headers) < len(data[0]):
            # Add generic column names for extra data columns
            for i in range(len(headers), len(data[0])):
                headers.append(f"Col_{i+1}")
        else:
            # Truncate headers if there are too many
            headers = headers[:len(data[0])]
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=headers)
    
    # Export to CSV if any export parameters provided
    if output_filename or any([sport, data_type]):
        if output_filename:
            export_dataframe_to_csv(df, filename=output_filename)
            # Save glossary to same directory if we have definitions
            if save_glossary_file and glossary:
                import os
                base_dir = os.path.dirname(output_filename)
                base_name = os.path.splitext(os.path.basename(output_filename))[0]
                glossary_filename = os.path.join(base_dir, f"{base_name}_glossary.md")
                save_glossary(glossary, headers, sport or "Unknown", filename=glossary_filename)
        else:
            export_dataframe_to_csv(df, sport=sport, data_type=data_type, 
                                  season=season, team=team, week=week)
            # Save glossary using the same organizational structure
            if save_glossary_file and glossary:
                save_glossary(glossary, headers, sport, season, team, 
                            data_type=f"{data_type}_glossary")
    
    return df, glossary