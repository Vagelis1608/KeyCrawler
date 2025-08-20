import hashlib
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from lxml import etree

# from check import keybox_check

session = requests.Session()

# Load environment variables from .env file
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN is not set in the .env file")

# Search query
search_query = "<AndroidAttestation>"
search_url = f"https://api.github.com/search/code?q={search_query}+NOT+repo%3Apperez39%2Fgoogle-keys"

# Headers for the API request
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

save = Path(__file__).resolve().parent / "keys"
cache_file = Path(__file__).resolve().parent / "cache.txt"
cached_urls = set(open(cache_file, "r").readlines()) if cache_file.exists() else set()


# Function to fetch and print search results
def fetch_and_process_results(page: int) -> bool:
    params = {"per_page": 100, "page": page}
    response = session.get(search_url, headers=headers, params=params)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to retrieve search results: {response.status_code}")
    search_results = response.json()
    if "items" in search_results:
        for item in search_results["items"]:
            file_name = item["name"]
            # Process only XML files
            if file_name.lower().endswith(".xml"):
                raw_url: str = (
                    item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                )
                # check if the file exists in cache
                if raw_url + "\n" in cached_urls:
                    continue
                else:
                    cached_urls.add(raw_url + "\n")
                # Fetch the file content
                file_content = fetch_file_content(raw_url)
                # Parse the XML
                try:
                    root = etree.fromstring(file_content)
                except etree.XMLSyntaxError:
                    continue
                # Get the canonical form (C14N)
                canonical_xml = etree.tostring(root, method="c14n")
                # Hash the canonical XML
                hash_value = hashlib.sha256(canonical_xml).hexdigest()
                file_name_save = save / (hash_value + ".xml")
                if not file_name_save.exists() and file_content: # and keybox_check(file_content):
                    print(f"{raw_url} is new")
                    with open(file_name_save, "wb") as f:
                        f.write(file_content)
    return len(search_results["items"]) > 0  # Return True if there could be more results


# Function to fetch file content
def fetch_file_content(url: str) -> bytes:
    response = session.get(url)
    if response.status_code == 200:
        return response.content
    else:
        raise RuntimeError(f"Failed to download {url}")


# Create directory for storing keys
os.makedirs(save, exist_ok=True)

# Fetch all pages
page = 1
while fetch_and_process_results(page):
    page += 1

# update cache
open(cache_file, "w").writelines(cached_urls)

# for file_path in save.glob("*.xml"):
#    file_content = file_path.read_bytes()  # Read file content as bytes
    # Run CheckValid to determine if the file is still valid
#    if not keybox_check(file_content):
        # Prompt user for deletion
#        user_input = input(f"File '{file_path.name}' is no longer valid. Do you want to delete it? (y/N): ")
#        if user_input.lower() == "y":
#            try:
#                file_path.unlink()  # Delete the file
#                print(f"Deleted file: {file_path.name}")
#            except OSError as e:
#                print(f"Error deleting file {file_path.name}: {e}")
#        else:
#            print(f"Kept file: {file_path.name}")
