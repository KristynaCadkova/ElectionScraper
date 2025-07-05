import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import os
import pandas as pd
import time
from scraper import get_page_content, init_district_data, extract_district_units, get_district_turnout_summary, get_district_party_results, merge_two_tables, validate_user_input


if len(sys.argv) != 3:
    print("Error: Invalid number of arguments.")
    print("Usage: python main.py <URL> \"<output_file.csv>\"")
    sys.exit(1)


url = sys.argv[1]
output_file = sys.argv[2]

# 1. Load the list of all districts for validation
home_url = "https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ"
soup_home = get_page_content(home_url)
districts = init_district_data(soup_home)

validate_user_input(url, output_file, districts)



# 2. Verify that the URL exists in the list

district_url_list = [district for district in districts.values()]
if url not in district_url_list:
    print("Error: The provided URL does not match any district.")
    # print("Available URL:")
    # for u in district_url_list:
    #     print(u)
    sys.exit(1)



# 3. Loading list of district units
print("Loading list of district units...Please wait, processing may take several seconds.")
soup_district = get_page_content(url)
district_units_dict = extract_district_units(soup_district, url)


# 4. getting election data from the district
headers1, rows1 = get_district_turnout_summary(district_units_dict)
headers2, rows2 = get_district_party_results(district_units_dict)

# 5. Merge and save
merge_two_tables(headers1, rows1, headers2, rows2, output_file)



