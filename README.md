# Election Results Scraper

This project is named Election Scraper and was created as part of an Engeto Python course. The goal is to scrape the election results from the Czech 2017 parliamentary elections website for a selected district and output the results in a structured CSV file.

## Features

- User provides a URL of a district and a name for the output file (both as arguments).
- The script scrapes all municipalities (obce) within the given district.
- Outputs a CSV with the following columns:
  - Municipality code
  - Municipality name
  - Number of registered voters
  - Envelopes issued
  - Valid votes
  - One column for each party with the number of votes received
- Includes input validation and user feedback during scraping.
- Automatically deletes temporary files after execution.

## How to use

1. Clone the repository and navigate into the folder.
2. Create a virtual environment and activate it.
3. Install required libraries:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the script from terminal with:
   ```bash
   python main.py "<URL>" "<output_filename.csv>"
   ```
   Example:
   ```bash
   python main.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=4&xnumnuts=3207" "vysledky_tachov.csv"
   ```

⚠️ The URL must be taken from the "Výběr oobce" column on the main election results page. Right-click the `X` symbol for a district and copy the link! Only those URLs will work.

## Output

Each row in the output CSV contains data for one municipality in the selected district. The file will be saved in the same folder where you ran the script.

## Requirements

See `requirements.txt` for the list of libraries and versions used.

## Example Output

See the sample file `vysledky_praha.csv` for a real output example.

---
"""
main.py: third project for Engeto Online Python Academy  
author: Kristýna Čadková  
email: kristyna.posingerova@seznam.cz
discord:kristyna_90682
"""
