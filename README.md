# GSUP-File-Downloader
GTSW Downloader is a Python-based script designed to automate the process of downloading stories from a specific [REDACTED] website. I may expose the website in the future. It provides functionality for extracting stories, saving them in PDF format, and optionally exporting story links in CSV format. Users can utilize several command-line arguments to customize their download preferences.

## Features

- Parse cookies from Netscape HTTP cookie files (Currently Redunant Feature)
- Download stories from specified authors, users' favourites, or individual stories.
- Save stories as PDFs or export printable links to CSV.
- Handle large story collections by carefully managing which stories overwrite (based on file sizes and word count).
- Built-in error handling and logging for skipped or failed downloads.

## Prerequisites

- Python 3.x
- [wkhtmltopdf](https://wkhtmltopdf.org/downloads.html)
- All libraries in `requirements.txt`

## Installation

1. Clone this repository

2. Next, install the required packages with:
   ```bash
   pip install -r requirements.txt
   ```
3.  Download and ensure `wkhtmltopdf.exe` is present in the script directory
   
## Usage

This script currently uses rudimentary `argv` command-line argument options to manage various download scenarios.

### Command-Line Arguments

- `--favStories [user_id]`
  
    Downloads favourite stories for the specified user ID. If no ID is provided, a default ID (12345) is used.
  
    Example:
  
       python GTSW-dl.py --favStories 12345

- `--favAuth [user_id]`
  
    Downloads stories from authors listed in the user's favorites. If no user ID is provided, a default ID (12345) is used.
    
    Example:
    
       python GTSW-dl.py --favAuth 12345

- `--archiveAuth (--file [path] | individual user_ids)`
  
    Downloads stories by authors specified in a file or provided directly separated by spaces.
    
    Example:
    
       python GTSW-dl.py --archiveAuth --file authors.txt
       python GTSW-dl.py --archiveAuth 12345 67890

- `--archiveStories (--file [path] | individual story_ids)`
  
    Downloads individual stories by IDs specified in a file or provided directly.
    
    Example:
  
        python GTSW-dl.py --archiveStories --file stories.txt
        python GTSW-dl.py --archiveStories 98765 43210

### Interactive Mode

If no arguments are provided, the script will enter an interactive mode where users can input the some desired options, including the download directory, mode (`individual` or `file`), and IDs for authors or stories.

Example:

   `python GTSW-dl.py`


### Logging

- A log file (`log.txt`) records any skipped downloads with details like word count, file size, mode, and timestamp.

### Todo

- Replace the rudimentary `argv` command-line argument options with the `argparse` library, making the script more user-friendly and easier to maintain. Integration with `argparse` will provide better help documentation, input validation, and optional/required argument handling, similar to other popular downloader tools.

## Important Notes

Make sure to replace the [REDACTED] placeholder in the code URL with the actual website domain. (IYKYK)


## License

This project is licensed under the GPL License. See the LICENSE file for details.
