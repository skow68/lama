import re
def remove_datetime(text):
    # Define the regular expression patterns to match different date and time formats
    patterns = [
        r'\b\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+',  # Matches "Nov  5 09:06:02"
        r'\b\w{3}\s+\d{1,2}\s+\d{4}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\w{3}:',  # Matches "Nov  5 2024 08:06:01.626 UTC:"
        r'\d{2}:\d{2}:\d{2}\s+\w{3}\s+\w{3}',  # Matches "09:06:01 CET Tue"
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}\+\d{2}:\d{2}',# Matches "2024-11-05T15:21:45.775+01:00"
        r'\d{2}-\w{3}-\d{4}\s+\d{2}:\d{2}:\d{2}\.\d{3}',# Matches "20-Dec-2024 10:58:24.259"
        r'\d{2}:\d{2}:\d{2}\s+\w{4}\s+\w{3}\s+\d{1,2}\s+\d{4}',  # Matches "23:59:00 CEDT Sep 4 2021"
        r'\d{4}\/\d{2}\/\d{2}\s+\d{2}:\d{2}:\d{2}', #2024/12/05 21:20:35
        r'\d{4}\s+\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\w{3}:',  #2024 Dec  6 15:57:05 CET:
        r'\d{2}:\d{2}:\d{2}\s+\w{3}\s+\w{3}\s+\w{3}\s+\d{1,2}\s+\d{4}',  # Matches "03:33:09 CET Fri Nov 8 2024"
    ]
 
    # Compile all patterns into a single regex
    combined_pattern = re.compile('|'.join(patterns))
 
    # Substitute occurrences of the date/time patterns with an empty string
    cleaned_text = re.sub(combined_pattern, '', text)
 
    return cleaned_text
