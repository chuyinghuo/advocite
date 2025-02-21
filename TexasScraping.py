import requests
from bs4 import BeautifulSoup

# Define the four chapter URLs
chapter_urls = {
    "Alcoholic Beverage Code Chapter 11": "https://statutes.capitol.texas.gov/Docs/AL/htm/AL.11.htm",
    "Health and Safety Code Chapter 161": "https://statutes.capitol.texas.gov/Docs/HS/htm/HS.161.htm",
    "Tax Code Chapter 151": "https://statutes.capitol.texas.gov/Docs/TX/htm/TX.151.htm",
    "Tax Code Chapter 162": "https://statutes.capitol.texas.gov/Docs/TX/htm/TX.162.htm",
}

def extract_act_references(soup):
    # Try to find <a> tags whose visible text includes "Acts"
    act_links = soup.find_all("a", string=lambda text: text and "Acts" in text)
    acts = []
    if act_links:
        for link in act_links:
            act_text = link.get_text(strip=True)
            act_href = link.get("href")
            acts.append((act_text, act_href))
    else:
        # If no act links, search for paragraphs containing "Acts"
        paragraphs = soup.find_all("p")
        for p in paragraphs:
            text = p.get_text(separator=" ", strip=True)
            # A simple heuristic: split on semicolons and look for parts containing "Acts"
            for part in text.split(";"):
                if "Acts" in part:
                    acts.append((part.strip(), None))
    return acts

# Loop through each chapter and extract act references
all_acts = {}

for chapter, url in chapter_urls.items():
    print(f"\nProcessing: {chapter}")
    print(f"URL: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve page; status code: {response.status_code}")
        continue

    soup = BeautifulSoup(response.text, "html.parser")
    acts = extract_act_references(soup)
    if acts:
        all_acts[chapter] = acts
    else:
        print("No act references found on this page.")

# Print the final list of act references for each chapter
for chapter, acts in all_acts.items():
    print(f"\n--- {chapter} ---")
    for act_text, act_href in acts:
        if act_href:
            print(f"{act_text} - {act_href}")
        else:
            print(f"{act_text}")
