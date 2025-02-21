import requests
from bs4 import BeautifulSoup
from openai import OpenAI

client = OpenAI(api_key="OPENAI_API_KEY")
import time
import json

# Set your OpenAI API key

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
            for part in text.split(";"):
                if "Acts" in part:
                    acts.append((part.strip(), None))
    return acts

def summarize_act_details(act_text, act_href, chapter):
    """
    Calls ChatGPT API (gpt-3.5-turbo) to generate a JSON summary for the act.
    The JSON includes:
      - act_name
      - consumer_product_taxed
      - tax_rate (or tax amount)
      - taxpayer (who pays the tax)
      - enforcement (how it is enforced)
      - source_links (URLs where this info is found)
    """
    # Build a prompt that instructs ChatGPT to return the summary in JSON format.
    prompt = (
        f"Act Reference: {act_text}\n"
        f"Chapter: {chapter}\n"
        f"URL: {act_href if act_href else 'N/A'}\n\n"
        "Please provide a one-sentence summary of the following details about this act in JSON format: \n"
        "1. What consumer product is being taxed.\n"
        "2. How much it is taxed (or tax rate/amount).\n"
        "3. Who pays the tax.\n"
        "4. How it is enforced.\n"
        "5. Provide links where the information was found.\n\n"
        "Return a JSON object with the following keys: \n"
        "act_name, consumer_product_taxed, tax_rate, taxpayer, enforcement, source_links.\n"
        "For example:\n"
        '{\n'
        '  "act_name": "Tax Code Chapter 151",\n'
        '  "consumer_product_taxed": "Limited sales items such as tobacco",\n'
        '  "tax_rate": "X%",\n'
        '  "taxpayer": "Retailers/consumers",\n'
        '  "enforcement": "By state comptroller and law enforcement",\n'
        '  "source_links": ["https://statutes.capitol.texas.gov/Docs/TX/htm/TX.151.htm", "https://..."]\n'
        '}\n'
        "Ensure the output is a valid JSON."
    )

    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=150)
        # Extract the JSON response text and try to parse it.
        summary_text = response.choices[0].message.content.strip()
        # If the response is not valid JSON, you might need to fix it.
        summary_json = json.loads(summary_text)
        return summary_json
    except Exception as e:
        print(f"Error summarizing act '{act_text}': {e}")
        return {
            "act_name": act_text,
            "consumer_product_taxed": "Summary not available",
            "tax_rate": "Summary not available",
            "taxpayer": "Summary not available",
            "enforcement": "Summary not available",
            "source_links": []
        }

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

# For each act reference, call ChatGPT API to get a summary
summaries = []
for chapter, acts in all_acts.items():
    for act_text, act_href in acts:
        print(f"Summarizing: {act_text}")
        summary = summarize_act_details(act_text, act_href, chapter)
        summaries.append(summary)
        # Pause briefly to avoid hitting rate limits
        time.sleep(1)

# Save the summaries as a JSON file
with open("act_summaries.json", "w") as f:
    json.dump(summaries, f, indent=2)

print("JSON summaries saved to act_summaries.json")
