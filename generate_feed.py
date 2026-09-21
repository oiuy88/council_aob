import datetime
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

SEARCH_URL = (
    "https://www.consilium.europa.eu/en/documents/public-register/"
    "public-register-search/?WordsInSubject=aob&DocumentLanguage=EN&OrderBy=DOCUMENT_DATE+DESC"
)
BASE_URL = "https://www.consilium.europa.eu"

def fetch_and_generate():
    # 1. Fetch Search Results
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(SEARCH_URL, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    # 2. Configure RSS Feed Metadata
    fg = FeedGenerator()
    fg.id(SEARCH_URL)
    fg.title("Consilium Public Register - AOB Search Feed")
    fg.author({"name": "Consilium Search Bot"})
    fg.link(href=SEARCH_URL, rel="alternate")
    fg.description("Automated RSS feed for Council Public Register documents with 'aob' in subject.")
    fg.language("en")

    # 3. Extract Document Cards/Items
    # Note: Consilium uses list/card elements for document search results
    items = soup.find_all("li", class_="c-search-result") or soup.select(".c-document-card, article, .c-list-item")

    for item in items:
        title_tag = item.find("a") or item.find("h3")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = title_tag.get("href", "")
        if link and not link.startswith("http"):
            link = BASE_URL + link

        # Extract snippet or additional metadata if available
        desc_tag = item.find("p") or item.find("div", class_="c-search-result__description")
        description = desc_tag.get_text(strip=True) if desc_tag else title

        # Create RSS Entry
        fe = fg.add_entry()
        fe.id(link if link else title)
        fe.title(title)
        fe.link(href=link if link else SEARCH_URL)
        fe.description(description)
        fe.pubdate(datetime.datetime.now(datetime.timezone.utc))

    # 4. Save to feed.xml
    fg.rss_file("feed.xml")

if __name__ == "__main__":
    fetch_and_generate()
