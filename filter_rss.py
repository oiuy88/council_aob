import copy
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime


# ============================================================
# CONFIGURATION
# ============================================================

# Consilium "Latest Council documents":
# PUBLIC + NON-PUBLIC documents
SOURCE_RSS = (
    "https://www.consilium.europa.eu/en/register/rss/LD.xml"
)

# Only titles containing AOB as a separate word are included.
KEYWORD = "AOB"

# Maximum number of AOB documents kept in the custom feed.
MAX_ITEMS = 100

# Output file.
OUTPUT_FILE = "feed.xml"

# Your GitHub Pages RSS URL.
FEED_URL = (
    "https://oiuy88.github.io/council_aob/feed.xml"
)

FEED_TITLE = "Consilium Council Documents — AOB"

FEED_DESCRIPTION = (
    "Latest public and non-public Council documents "
    "from the Consilium RSS feed whose title contains AOB."
)

FEED_LINK = (
    "https://www.consilium.europa.eu/"
    "en/documents/public-register/"
)


# ============================================================
# DOWNLOAD CONSILIUM RSS
# ============================================================

def download_feed():
    request = urllib.request.Request(
        SOURCE_RSS,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(compatible; Council-AOB-RSS/1.0)"
            ),
            "Accept": (
                "application/rss+xml, "
                "application/xml, "
                "text/xml, */*"
            ),
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=60
    ) as response:
        return response.read()


# ============================================================
# XML HELPERS
# ============================================================

def get_element_text(item, tag):
    element = item.find(tag)

    if element is not None and element.text:
        return element.text.strip()

    return ""


def get_title(item):
    return get_element_text(item, "title")


def get_pub_date(item):
    return get_element_text(item, "pubDate")


# ============================================================
# AOB FILTER
# ============================================================

def title_contains_keyword(title):
    """
    Match AOB as a separate word.

    Included:
        "ST 12345 2026 INIT - AOB"
        "AOB - Draft conclusions"
        "aob"

    Not included:
        "AOBXYZ"
        "MYAOBDOCUMENT"
    """

    pattern = r"\b" + re.escape(KEYWORD) + r"\b"

    return bool(
        re.search(
            pattern,
            title,
            flags=re.IGNORECASE
        )
    )


# ============================================================
# DATE SORTING
# ============================================================

def get_sort_date(item):

    value = get_pub_date(item)

    if not value:
        return datetime.min.replace(
            tzinfo=timezone.utc
        )

    try:
        date = parsedate_to_datetime(value)

        if date.tzinfo is None:
            date = date.replace(
                tzinfo=timezone.utc
            )

        return date

    except Exception:
        return datetime.min.replace(
            tzinfo=timezone.utc
        )


# ============================================================
# FILTER SOURCE FEED
# ============================================================

def filter_items(source_xml):

    root = ET.fromstring(source_xml)

    channel = root.find("channel")

    if channel is None:
        raise RuntimeError(
            "The Consilium RSS feed does not contain "
            "a <channel> element."
        )

    source_items = channel.findall("item")

    matching_items = []

    for item in source_items:

        title = get_title(item)

        if title_contains_keyword(title):
            matching_items.append(item)

    # Newest first.
    matching_items.sort(
        key=get_sort_date,
        reverse=True
    )

    # Keep only the newest 100.
    matching_items = matching_items[:MAX_ITEMS]

    print(
        f"Consilium items received: "
        f"{len(source_items)}"
    )

    print(
        f"AOB items found: "
        f"{len(matching_items)}"
    )

    print("\nLatest matching documents:")

    for item in matching_items[:10]:
        print(
            " -",
            get_title(item)
        )

    return matching_items


# ============================================================
# CREATE CUSTOM RSS
# ============================================================

def build_feed(items):

    rss = ET.Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": (
                "http://www.w3.org/2005/Atom"
            ),
        },
    )

    channel = ET.SubElement(
        rss,
        "channel"
    )

    ET.SubElement(
        channel,
        "title"
    ).text = FEED_TITLE

    ET.SubElement(
        channel,
        "link"
    ).text = FEED_LINK

    ET.SubElement(
        channel,
        "description"
    ).text = FEED_DESCRIPTION

    ET.SubElement(
        channel,
        "language"
    ).text = "en"

    ET.SubElement(
        channel,
        "generator"
    ).text = (
        "GitHub Actions — Council AOB RSS"
    )

    # RSS self-reference.
    atom_link = ET.SubElement(
        channel,
        "{http://www.w3.org/2005/Atom}link"
    )

    atom_link.set(
        "rel",
        "self"
    )

    atom_link.set(
        "type",
        "application/rss+xml"
    )

    atom_link.set(
        "href",
        FEED_URL
    )

    # Feed generation time.
    ET.SubElement(
        channel,
        "lastBuildDate"
    ).text = format_datetime(
        datetime.now(timezone.utc)
    )

    # Copy each original Consilium RSS item exactly.
    #
    # This preserves the original:
    #   title
    #   link
    #   guid
    #   pubDate
    #   description
    #   categories
    #   and any other fields supplied by Consilium.
    for original_item in items:

        channel.append(
            copy.deepcopy(original_item)
        )

    return ET.ElementTree(rss)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("Consilium AOB RSS generator")
    print("=" * 60)

    print("\nDownloading:")
    print(SOURCE_RSS)

    source_xml = download_feed()

    print("Download successful.")

    matching_items = filter_items(
        source_xml
    )

    feed = build_feed(
        matching_items
    )

    ET.indent(
        feed,
        space="  "
    )

    feed.write(
        OUTPUT_FILE,
        encoding="utf-8",
        xml_declaration=True
    )

    print()
    print("=" * 60)
    print(f"Created: {OUTPUT_FILE}")
    print(f"Items:   {len(matching_items)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
