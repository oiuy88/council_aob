import json
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

# Consilium Public Register URL
TARGET_URL = (
    "https://www.consilium.europa.eu/en/documents/public-register/"
    "public-register-search/?WordsInSubject=aob&WordsInText=&DocumentNumber="
    "&InterinstitutionalFiles=&DocumentTypes=&DateFrom=&DateTo="
    "&MeetingDateFrom=&MeetingDateTo=&DocumentLanguage=EN&OrderBy=DOCUMENT_DATE+DESC"
)

def parse_and_generate_rss():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    session = requests.Session()
    response = session.get(TARGET_URL, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    fg = FeedGenerator()
    fg.id(TARGET_URL)
    fg.title("Consilium EU Public Register - AOB")
    fg.author({'name': 'Consilium Feed'})
    fg.link(href=TARGET_URL, rel='alternate')
    fg.description("Automated RSS Feed for Consilium Public Register search (WordsInSubject=aob).")
    fg.language('en')

    # Parse result cards
    results = soup.find_all("li", class_=lambda c: c and "c-result" in c) or soup.select(".c-search-results article, table tbody tr, .c-document-card")

    for item in results:
        title_elem = item.find("a")
        if not title_elem or not title_elem.get_text(strip=True):
            continue

        title = title_elem.get_text(strip=True)
        link = title_elem.get("href", "")
        if link.startswith("/"):
            link = f"https://www.consilium.europa.eu{link}"

        fe = fg.add_entry()
        fe.id(link if link else title)
        fe.title(title)
        fe.link(href=link)
        fe.description(title)

    fg.rss_file("feed.xml")

if __name__ == "__main__":
    parse_and_generate_rss()
