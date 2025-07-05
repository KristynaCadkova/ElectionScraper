import requests
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urlparse, parse_qs
import os
import pandas as pd
import sys
import time


def get_page_content(url):
    """
        Fetches and parses the HTML content of a given URL.

        Parameters:
            url (str): The URL of the webpage to be fetched.

        Returns:
            BeautifulSoup object: Parsed HTML content if the request is successful.
            None: If the request fails or an exception is raised.
        """
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup

    except requests.exceptions.RequestException as e:
        print(f"Unable to process the request for this page:\n{e}")
        return None


def init_district_data(soup):
    """
    Extracts a dictionary of district names and their corresponding URLs from the main election page.

    Parameters:
        soup (BeautifulSoup): Parsed HTML content of the main election page.

    Returns:
        dict: A dictionary where the keys are lowercase district names (str) and the values are full URLs (str) to the district-specific pages.
    """
    base_url = "https://www.volby.cz/pls/ps2017nss/"
    districts = {}

    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            tds = row.find_all("td")
            links = row.find_all("a")

            if len(links) >= 3 and len(tds) >= 2:
                district_name = tds[1].text.strip()
                href = links[2].get("href")
                if district_name and href:
                    district_url = urllib.parse.urljoin(base_url, href)
                    districts[district_name.lower()] = district_url

    return districts



def extract_district_units(soup, base_url) -> dict:
    """
    Extracts a dictionary of municipalities with their full URLs and municipality codes.

    Parameters:
        soup (BeautifulSoup): Parsed HTML content of the district page.
        base_url (str): Base URL used to construct full links.

    Returns:
        dict: A dictionary where keys are municipality names (str),
              and values are dictionaries with:
                  - 'url' (str): full URL to the municipality's page,
                  - 'district_units_number' (str or None): municipality code from the URL query string (parameter "xobec").
    """
    district_units = {}
    rows = soup.find_all("tr")

    for row in rows:
        td = row.find("td", class_="overflow_name")
        a_tag = row.find("a")

        if td and a_tag:
            name = td.text.strip()
            href = a_tag.get("href")
            full_url = urllib.parse.urljoin(base_url, href)

            # Extract the district unit code (xobec) from the URL
            parsed = urlparse(full_url)
            query = parse_qs(parsed.query)
            district_units_number = query.get("xobec", [None])[0]

            district_units[name] = {
                "url": full_url,
                "číslo obce": district_units_number
            }

    return district_units


def get_district_turnout_summary(district_units_dict):
    """"
    Downloads the first summary table of voter turnout from all municipalities in a district.

    Parameters:
        district_units_dict (dict): A dictionary with municipality names as keys,
                          and a nested dictionary as values containing:
                            - 'url' (str): full URL to the municipality's page
                            - 'cislo_obce' (str or None): municipality code

    Returns:
        headers (list of str): Column names, including "Obec" and "Číslo obce"
        rows (list of lists): Each sublist represents a row of values from one municipality
    """
    headers = None
    rows = []
    for i, (district_unit, data) in enumerate(district_units_dict.items()):
        url = data["url"]
        district_unit_number = data["číslo obce"]

        soup = get_page_content(url)
        time.sleep(1)

        if soup is None:
            print(f"Skipping district unit '{district_unit}' due to a loading error.")
            continue
        table = soup.find("table")
        if not table:
            continue

        if headers is None:
            columns = table.find_all("th", attrs={"rowspan": "2"})
            headers = ["Číslo obce", "Obec"] + [column.text.strip() for column in columns]

        numbers = table.find_all("td", class_="cislo")[3:]
        data_row = [td.text.strip() for td in numbers]
        rows.append([district_unit, district_unit_number] + data_row)

    return headers, rows

def get_district_party_results(district_units_dict):
    """
    Downloads election results for all political parties from all municipalities in a district.

    Parameters:
        district_units_dict (dict): A dictionary with municipality names as keys,
                          and a nested dictionary as values containing:
                            - 'url' (str): full URL to the municipality's results page

    Returns:
        headers (list of str): Column names – starting with "Obec", followed by sorted party names
        rows (list of lists): Each sublist represents one municipality's vote counts for each party
    """
    party_list = []  # list of (party_number, party_name)
    seen_parties = set()
    district_units_data = {}

    for i, (district_unit, data) in enumerate(district_units_dict.items()):
        print(f"Processing district unit {i + 1} z {len(district_units_dict)}: {district_unit}")
        url = data["url"]

        soup = get_page_content(url)
        time.sleep(1)  # Pause after loading the page

        if soup is None:
            print(f"Skipping error '{district_unit}' due to a loading error.")
            continue

        tables = soup.find_all("table")[1:]
        if not tables:
            continue

        results = {}
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cell = row.find_all("td")
                if len(cell) >= 3:
                    party_number = cell[0].text.strip()
                    party_name = cell[1].text.strip()
                    votes = cell[2].text.strip()

                    if party_name in ["", "-"] or votes in ["", "-"]:
                        continue

                    results[party_name] = votes

                    if party_number not in seen_parties:
                        party_list.append((int(party_number), party_name))
                        seen_parties.add(party_number)

        district_units_data[district_unit] = results

    # Sort by party number and extract just the names
    party_list_sorted = sorted(party_list, key=lambda x: x[0])
    party_names_ordered = [name for _, name in party_list_sorted]

    # Header
    header = ["Obec"] + party_names_ordered

    # Assemble the rows
    rows = []
    for district_unit, votes in district_units_data.items():
        row = [district_unit] + [votes.get(name, "0") for name in party_names_ordered]
        rows.append(row)

    return header, rows



def merge_two_tables(headers1, rows1, headers2, rows2, output_name="vysledny_okres.csv"):
    """
    Merges two tables by municipality name and saves the result as a CSV file.

    Parameters:
        headers1 (list of str): Column names for the first table (e.g., voter turnout).
        rows1 (list of lists): Rows of data for the first table.
        headers2 (list of str): Column names for the second table (e.g., party results).
        rows2 (list of lists): Rows of data for the second table.
        output_name (str): Output CSV file name. Default is "vysledny_okres.csv".

    Returns:
        DataFrame: The merged DataFrame containing all combined data.
    """
    df1 = pd.DataFrame(rows1, columns=headers1)
    df2 = pd.DataFrame(rows2, columns=headers2)

    # Replace inconsistent column names in the first table
    df1 = df1.rename(columns={
        "Voličiv seznamu": "Voliči v seznamu",
        "Vydanéobálky": "Vydané obálky",
        "Volebníúčast v %": "Volební účast v %",
        "Odevzdanéobálky": "Odevzdané obálky",
        "Platnéhlasy": "Platné hlasy",
        "% platnýchhlasů": "% platných hlasů"
    })

    # Merge
    df_merged = pd.merge(df1, df2, on="Obec", how="outer")

    # Save
    df_merged.to_csv(output_name, index=False, encoding="utf-8")
    abs_path = os.path.abspath(output_name)
    print(f"File has been saved successfully as:\n {abs_path}")

    return df_merged



def validate_user_input(user_url: str, output_filename: str, districts: dict):
    """
    Validates that the provided URL matches the district name extracted from the output filename.

    Parameters:
        user_url (str): The URL provided by the user.
        output_filename (str): The desired name of the output CSV file.
        districts (dict): Dictionary of {district_name: url} for validation.

    Raises:
        SystemExit: If the URL does not match any district, or if the district name does not match the filename.
    """
    if not output_filename.lower().endswith(".csv") or '"' in output_filename or "'" in output_filename:
        print("Error: Invalid output filename. It must end with .csv and not contain quotes.")
        sys.exit(1)

    # Extract district name from filename
    district_from_filename = output_filename.lower().replace(".csv", "").replace("vysledky_", "").strip()

    # Find the district
    district_from_url = None
    for name, url in districts.items():
        if user_url.strip() == url.strip():
            district_from_url = name.lower()
            break


    if district_from_url is None:
        print("Error: No matching district found for the provided URL.")

        sys.exit(1)

    if district_from_filename not in district_from_url:
        print(f"Error: The URL doesn’t match the district name in the filename '{district_from_filename.title()}' in the output file.")
        print("Please verify the URL and filename.")
        sys.exit(1)





