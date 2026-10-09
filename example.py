"""Telegram channel engagement report with the Telegram Channel Scraper actor on Apify.

1. Scrapes the last 30 days of posts from a few public channels (no login, no API ID).
2. Writes every post to telegram_posts.csv (date, views, reactions, media, links).
3. Prints a per-channel benchmark: subscribers, posts, median views,
   views per subscriber and reactions per 1,000 views, plus each channel's top post.

Usage:
    pip install -r requirements.txt
    set APIFY_TOKEN=...   (or export APIFY_TOKEN=... on macOS/Linux)
    python example.py durov bloomberg designers
"""
import csv
import os
import statistics
import sys

from apify_client import ApifyClient

TOKEN = os.environ.get("APIFY_TOKEN", "<YOUR_APIFY_TOKEN>")
CHANNELS = sys.argv[1:] or ["durov", "bloomberg", "designers"]

client = ApifyClient(TOKEN)
run = client.actor("rel8ble/telegram-channel-scraper").call(run_input={
    "channels": CHANNELS,
    "maxPostsPerChannel": 200,        # hard cap per channel (you pay per row)
    "onlyPostsNewerThan": "30 days",  # stop paging once posts get older
    "includeChannelInfo": True,
})
items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

channels = {i["username"]: i for i in items if i["type"] == "channel"}
posts = [i for i in items if i["type"] == "post"]

with open("telegram_posts.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["channel", "date", "url", "views", "reactions", "mediaType", "links", "text"])
    for p in posts:
        w.writerow([
            p["channel"], p["date"], p["url"], p["views"], p["reactionsTotal"],
            p["mediaType"], " ".join(p["links"]), (p["text"] or "").replace("\n", " ")[:300],
        ])
print(f"Saved {len(posts)} posts to telegram_posts.csv\n")

print(f"{'channel':<20}{'subs':>12}{'posts':>7}{'med views':>11}{'views/sub':>11}{'react/1k':>10}")
for name, info in channels.items():
    mine = [p for p in posts if p["channel"] == name and p["views"]]
    if not info.get("previewAvailable"):
        print(f"{name:<20}  no public web preview (group or preview turned off)")
        continue
    if not mine:
        print(f"{name:<20}  no posts in the last 30 days")
        continue
    subs = info.get("subscribers") or 0
    med = statistics.median(p["views"] for p in mine)
    react = sum(p["reactionsTotal"] or 0 for p in mine) / sum(p["views"] for p in mine) * 1000
    ratio = f"{med / subs:.1%}" if subs else "-"
    print(f"{name:<20}{subs:>12,}{len(mine):>7}{med:>11,.0f}{ratio:>11}{react:>10.1f}")

print("\nTop post per channel (by views):")
for name in channels:
    mine = [p for p in posts if p["channel"] == name and p["views"]]
    if mine:
        top = max(mine, key=lambda p: p["views"])
        snippet = (top["text"] or "[media only]").split("\n")[0][:80]
        print(f"  {name}: {top['views']:,} views  {top['url']}  {snippet}")
