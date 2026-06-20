# BigQuery Release Log

A small local web app that pulls Google's official BigQuery release-notes
feed and shows each individual update (Feature / Change / Announcement /
Breaking / Issue) as its own row. Refresh on demand, click any update to
open a pre-filled tweet composer for it.

## What it does

- Fetches `https://docs.cloud.google.com/static/feeds/bigquery-release-notes.xml`
  (Google's official Atom feed for BigQuery release notes) from the Flask
  backend.
- Splits each day's entry into individual updates, since Google often
  bundles several unrelated changes under one date.
- Renders them in a simple, readable list with a manual refresh button
  (spinner while loading).
- Click any update to select it. A composer panel slides up at the bottom
  with a ready-to-edit tweet (under 280 characters, including a link back
  to the official release notes page). "Post to X / Twitter" opens
  Twitter/X's tweet-compose page in a new tab with your text pre-filled —
  no API keys or login required from the app itself, you just review and
  post it yourself.

## Setup

```bash
cd bq-release-app
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## Project structure

```
bq-release-app/
├── app.py                 # Flask backend: fetches + parses the feed
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    └── js/app.js
```

## Notes

- No database, no auth, no API keys needed — it's a single-process local
  app intended to run on your own machine.
- The "Post to X / Twitter" button uses Twitter/X's public tweet-intent
  URL (`twitter.com/intent/tweet?text=...`), which opens a normal compose
  window in your browser. It does not post on your behalf automatically.

## App ScreenShot
<img width="1905" height="927" alt="image" src="https://github.com/user-attachments/assets/b149a941-6f34-4d84-870b-fef3d7ae6a65" />

