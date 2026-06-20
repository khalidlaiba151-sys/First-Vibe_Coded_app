"""
BigQuery Release Log
---------------------
A tiny Flask app that fetches Google's official BigQuery release-notes
Atom feed, breaks each day's entry into individual updates (Feature /
Change / Announcement / Breaking / Issue), and serves them to a plain
HTML/CSS/JS frontend.

Run with:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""

import re
import xml.etree.ElementTree as ET

import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__)

FEED_URL = "https://docs.cloud.google.com/static/feeds/bigquery-release-notes.xml"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
REQUEST_TIMEOUT = 10


def strip_html(html_text: str) -> str:
    """Collapse an HTML snippet down to plain text (used for the tweet
    composer's default text, not for on-screen rendering)."""
    text = re.sub(r"<[^>]+>", " ", html_text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_entry_into_updates(entry_id, date_label, updated_iso, link, content_html):
    """
    Each <entry> in the feed covers one calendar day and can bundle several
    unrelated updates together, each introduced by an <h3>Category</h3>
    heading (Feature, Change, Announcement, Breaking, Issue). We split on
    those headings so the UI can offer one row per *update* rather than per
    day, which is what makes "select one update and tweet about it" make
    sense.
    """
    pieces = re.split(r"(<h3>.*?</h3>)", content_html, flags=re.DOTALL)

    updates = []
    category = None
    buffer_html = ""
    seq = 0

    def flush():
        nonlocal seq
        if category is not None and buffer_html.strip():
            summary = strip_html(buffer_html)
            updates.append(
                {
                    "id": f"{entry_id}-{seq}",
                    "date": date_label,
                    "updated": updated_iso,
                    "link": link,
                    "category": category,
                    "html": buffer_html.strip(),
                    "summary": summary,
                }
            )
            seq += 1

    for piece in pieces:
        heading_match = re.match(r"<h3>(.*?)</h3>", piece, flags=re.DOTALL)
        if heading_match:
            flush()
            category = heading_match.group(1).strip()
            buffer_html = ""
        else:
            buffer_html += piece
    flush()

    if not updates:
        # Defensive fallback for the rare entry with no <h3> headings at all.
        updates.append(
            {
                "id": f"{entry_id}-0",
                "date": date_label,
                "updated": updated_iso,
                "link": link,
                "category": "Update",
                "html": content_html.strip(),
                "summary": strip_html(content_html),
            }
        )

    return updates


def fetch_updates():
    resp = requests.get(
        FEED_URL,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": "bq-release-log/1.0 (+local Flask app)"},
    )
    resp.raise_for_status()

    root = ET.fromstring(resp.content)

    all_updates = []
    for entry in root.findall("atom:entry", ATOM_NS):
        entry_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
        date_label = entry.findtext("atom:title", default="", namespaces=ATOM_NS)
        updated_iso = entry.findtext("atom:updated", default="", namespaces=ATOM_NS)
        link_el = entry.find("atom:link", ATOM_NS)
        link = link_el.get("href") if link_el is not None else ""
        content_el = entry.find("atom:content", ATOM_NS)
        content_html = (content_el.text or "") if content_el is not None else ""

        all_updates.extend(
            split_entry_into_updates(entry_id, date_label, updated_iso, link, content_html)
        )

    return all_updates


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/release-notes")
def release_notes():
    try:
        updates = fetch_updates()
    except requests.RequestException as exc:
        return jsonify({"error": f"Could not reach the release notes feed ({exc})."}), 502
    except ET.ParseError as exc:
        return jsonify({"error": f"The release notes feed could not be read ({exc})."}), 502

    return jsonify({"updates": updates, "feed_url": FEED_URL, "count": len(updates)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
