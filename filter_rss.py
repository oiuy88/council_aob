```python
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime


# ============================================================
# CONFIGURATION
# ============================================================

# Consilium's "Latest Council documents — Public and non-public"
SOURCE_RSS = (
    "https://www.consilium.europa.eu/en/register/rss/LD.xml"
)

# Only items whose title contains this text are included.
KEYWORD = "AOB"

# Output file
OUTPUT_FILE = "aob.xml"

# Change these to your GitHub Pages URL
FEED_URL = (
    "https://YOUR-USERNAME.github.io/"
    "YOUR-REPOSITORY/aob.xml"
)

FEED_TITLE = "Consilium Council Documents — AOB"

FEED_DESCRIPTION = (
    "Public and non-public Council documents from the "
    "Consilium RSS feed whose title contains AOB."
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
# FILTER ITEMS
# ============================================================

def filter_items(source_xml):

    root = ET.fromstring(source_xml)

    channel = root.find("channel")

    if channel is None:
        raise RuntimeError(
            "The Consilium RSS feed has no channel element."
        )

    items = channel.findall("item")

    matching = []

    for item in items:

        title_element = item.find("title")

        if title_element is None:
            continue

        title = (
            title_element.text or ""
        ).strip()

        # Case-insensitive title matching.
        if KEYWORD.casefold() in title.casefold():
            matching.append(item)

    print(f"Items received: {len(items)}")
    print(
        f"Items containing '{KEYWORD}': "
        f"{len(matching)}"
    )

    return matching


# ============================================================
# CREATE CUSTOM RSS
# ============================================================

def create_feed(items):

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

    ET.SubElement(
        channel,
        "atom:link"
    )

    atom_link = channel[-1]

    atom_link.tag = (
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

    ET.SubElement(
        channel,
        "lastBuildDate"
    ).text = format_datetime(
        datetime.now(timezone.utc)
    )

    # Copy the original Consilium items.
    for original_item in items:

        new_item = ET.SubElement(
            channel,
            "item"
        )

        for element in original_item:

            new_element = ET.SubElement(
                new_item,
                element.tag,
                element.attrib
            )

            new_element.text = element.text
            new_element.tail = element.tail

            # Preserve nested elements.
            for child in element:

                new_child = ET.SubElement(
                    new_element,
                    child.tag,
                    child.attrib
                )

                new_child.text = child.text
                new_child.tail = child.tail

    return ET.ElementTree(rss)


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Downloading Consilium public + non-public RSS..."
    )

    source_xml = download_feed()

    matching_items = filter_items(
        source_xml
    )

    feed = create_feed(
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

    print(
        f"Created {OUTPUT_FILE} "
        f"with {len(matching_items)} items."
    )


if __name__ == "__main__":
    main()
```
