```python
import copy
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime


# ============================================================
# CONFIGURATION
# ============================================================

# Consilium: Latest Council documents
# PUBLIC + NON-PUBLIC documents
SOURCE_RSS = (
    "https://www.consilium.europa.eu/en/register/rss/LD.xml"
)

# Match AOB as a separate word, case-insensitive.
KEYWORD = "AOB"

# Maximum number of matching documents to keep.
MAX_ITEMS = 100

# Generated RSS filename.
OUTPUT_FILE = "aob.xml"

# IMPORTANT:
# Change this to your actual GitHub Pages URL.
FEED_URL = (
    "https://YOUR-USERNAME.github.io/"
    "YOUR-REPOSITORY/aob.xml"
)

FEED_TITLE = "Consilium Council Documents — AOB"

FEED_DESCRIPTION = (
    "Latest public and non-public Council documents "
    "from Consilium whose title contains AOB."
)


# ============================================================
# DOWNLOAD SOURCE RSS
# ============================================================

def download_feed():

    request = urllib.request.Request(
        SOURCE_RSS,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(compatible; Consilium-AOB-RSS/1.0)"
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
# FIND TITLE
# ============================================================

def get_title(item):

    # Normal RSS title
    title = item.find("title")

    if title is not None and title.text:
        return title.text.strip()

    # Handle namespaced title, just in case.
    for child in item:

        if child.tag.endswith("}title"):

            if child.text:
                return child.text.strip()

    return ""


# ============================================================
# AOB MATCHING
# ============================================================

def title_contains_keyword(title):

    # Match AOB as a separate word.
    #
    # Matches:
    #   "ST 12345 2026 INIT - AOB"
    #   "AOB - Draft conclusions"
    #   "aob"
    #
    # Does NOT match:
    #   "AOBXYZ"
    #   "MYAOBDOCUMENT"

    pattern = r"\b" + re.escape(KEYWORD) + r"\b"

    return bool(
        re.search(
            pattern,
            title,
            flags=re.IGNORECASE
        )
    )


# ============================================================
# DATE PARSING
# ============================================================

def get_pub_date(item):

    for tag in (
        "pubDate",
        "date",
        "published",
        "updated",
    ):

        element = item.find(tag)

        if element is not None and element.text:
            return element.text.strip()

    return ""


def sort_key(item):

    value = get_pub_date(item)

    if not value:
        return datetime.min.replace(
            tzinfo=timezone.utc
        )

    # RSS dates normally look like:
    # Wed, 16 Sep 2026 12:00:00 GMT

    try:
        from email.utils import parsedate_to_datetime

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
# FILTER
# ============================================================

def filter_items(source_xml):

    root = ET.fromstring(source_xml)

    channel = root.find("channel")

    if channel is None:
        raise RuntimeError(
            "Consilium RSS does not contain <channel>."
        )

    source_items = channel.findall("item")

    matching = []

    for item in source_items:

        title = get_title(item)

        if title_contains_keyword(title):
            matching.append(item)

    # Newest first.
    matching.sort(
        key=sort_key,
        reverse=True
    )

    # Keep only the latest 100.
    matching = matching[:MAX_ITEMS]

    print(
        f"Source items: {len(source_items)}"
    )

    print(
        f"AOB matches: {len(matching)}"
    )

    for item in matching[:10]:
        print(
            "  ",
            get_title(item)
        )

    return matching


# ============================================================
# BUILD RSS
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
    ).text = (
        "https://www.consilium.europa.eu/"
        "en/documents/public-register/"
    )

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
        "GitHub Actions — Consilium AOB RSS"
    )

    # Self URL for RSS readers.
    atom_link = ET.SubElement(
        channel,
        "{http://www.w3.org/2005/Atom}link",
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

    ET.SubElement(
        channel,
        "lastBuildDate"
    ).text = format_datetime(
        datetime.now(timezone.utc)
    )

    # Copy the original Consilium <item> completely.
    #
    # This preserves:
    # - title
    # - link
    # - GUID
    # - publication date
    # - description
    # - categories
    # - namespaces
    # - any additional fields Consilium adds
    #
    for original_item in items:

        channel.append(
            copy.deepcopy(original_item)
        )

    return ET.ElementTree(rss)


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Downloading Consilium "
        "public + non-public RSS..."
    )

    source_xml = download_feed()

    items = filter_items(
        source_xml
    )

    feed = build_feed(
        items
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
    print(
        f"Created {OUTPUT_FILE}"
    )

    print(
        f"Number of items: {len(items)}"
    )


if __name__ == "__main__":
    main()
```
