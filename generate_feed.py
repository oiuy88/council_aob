import os
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

# Target search URL
TARGET_URL = (
    "https://www.consilium.europa.eu/en/documents/public-register/"
    "public-register-search/?WordsInSubject=aob&WordsInText=&DocumentNumber="
    "&InterinstitutionalFiles=&DocumentTypes=&DateFrom=&DateTo="
    "&MeetingDateFrom=&MeetingDateTo=&DocumentLanguage=EN&OrderBy=DOCUMENT_DATE+DESC"
)

def fetch_search_results():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(TARGET_URL, headers=headers)
    response.raise_for_status()
    return response.text

def parse_and_generate_rss():
    html_content = fetch_search_results()
    soup = BeautifulSoup(html_content, "html.parser")

    fg = FeedGenerator()
    fg.id(TARGET_URL)
    fg.title("Consilium EU Public Register - Search: AOB")
    fg.author({'name': 'Consilium EU Search Feed'})
    fg.link(href=TARGET_URL, rel='alternate')
    fg.description("Automated RSS Feed for Consilium Public Register search (WordsInSubject=aob).")
    fg.language('en')

    # Adjust CSS selectors based on Consilium search page layout
    items = soup.select(".c-search-result__item, .m-document-item, li.c-list-item")

    for item in items:
        title_tag = item.select_one("a.c-title, .title a, h3 a")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = title_tag.get('href', '')
        if link.startswith('/'):
            link = f"https://www.consilium.europa.eu{link}"

        # Extract summary or date if available
        desc_tag = item.select_one(".c-description, .abstract, p")
        description = desc_tag.get_text(strip=True) if desc_tag else title

        fe = fg.add_entry()
        fe.id(link if link else title)
        fe.title(title)
        fe.link(href=link)
        fe.description(description)

    fg.rss_str(pretty=True)
    fg.rss_file("feed.xml")

if __name__ == "__main__":
    parse_and_generate_rss()
