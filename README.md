# Telegram channel scraper in Python: scrape Telegram posts, views, reactions and media from public channels to JSON/CSV (no API ID, no login)

A short tutorial for pulling **public Telegram channel posts** into Python with the [Telegram Channel Scraper](https://apify.com/rel8ble/telegram-channel-scraper) actor on Apify. Give it channel usernames or `t.me` links and get back every post's text, date, view count, reactions, photos, videos, files, polls, link previews, forwards and replies, plus one channel-info row (subscribers, description, verified badge). No Telegram account, phone number, API ID or Telethon session needed. Useful for media monitoring, crypto and signals research, channel vetting, and NLP / sentiment datasets.

> Disclosure: I built this actor; it's a paid tool on Apify ($1.50 per 1,000 results). The code in this repo is MIT-licensed.

## How it works

Every public channel has a web preview at `https://t.me/s/<channel>`. The actor reads that page over plain HTTP (no headless browser), parses each post, and pages back from the newest post to the oldest until it hits your post limit, your date cutoff, or the start of the channel. In test runs 250 posts took about 7 seconds. Failed or rate-limited pages are retried on a fresh proxy session.

## Quick start (Python)

```bash
pip install apify-client
```

```python
from apify_client import ApifyClient

client = ApifyClient("<YOUR_APIFY_TOKEN>")

run = client.actor("rel8ble/telegram-channel-scraper").call(run_input={
    "channels": ["durov", "@bloomberg", "https://t.me/designers"],
    "maxPostsPerChannel": 50,          # newest first; 0 = whole history
    "onlyPostsNewerThan": "30 days",   # or a date like "2026-09-01"
    # "searchQuery": "bitcoin",        # optional: Telegram's in-channel search
})

for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    if item["type"] == "post":
        print(item["date"], item["channel"], item["views"], item["reactionsTotal"], item["url"])
```

[`example.py`](example.py) is the runnable version: it saves the last 30 days of posts from the channels you pass to `telegram_posts.csv`, then prints an engagement benchmark per channel (median views, views per subscriber, reactions per 1,000 views) and each channel's top post.

```bash
pip install -r requirements.txt
export APIFY_TOKEN=<YOUR_APIFY_TOKEN>
python example.py durov bloomberg designers
```

## Quick start (Node.js)

```js
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: '<YOUR_APIFY_TOKEN>' });
const run = await client.actor('rel8ble/telegram-channel-scraper').call({
    channels: ['bloomberg'], searchQuery: 'AI', maxPostsPerChannel: 20,
});
const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(items.filter((i) => i.type === 'post').map((p) => `${p.views} ${p.url}`));
```

## Input

| Field | Default | What it does |
|---|---|---|
| `channels` | `["durov"]` | Usernames or links in any form: `durov`, `@durov`, `https://t.me/durov`, `https://t.me/s/durov` |
| `maxPostsPerChannel` | 100 | Newest posts first; `0` = the whole channel history |
| `onlyPostsNewerThan` | - | A date (`2026-09-01`) or a period (`7 days`, `2 weeks`, `3 months`); paging stops at the cutoff |
| `searchQuery` | - | Only posts matching this keyword (Telegram's own channel search) |
| `includeChannelInfo` | true | Adds one `type: "channel"` row per channel |
| `maxConcurrency` | 5 | Channels scraped in parallel (1-20) |

## Output sample (real rows, run of 24 Sep 2026)

One post (long CDN URL shortened, 5 of its 8 reactions left out):

```json
{
  "type": "post",
  "channel": "bloomberg",
  "channelId": "1488156064",
  "channelTitle": "Bloomberg",
  "postId": 3225,
  "url": "https://t.me/bloomberg/3225",
  "date": "2026-09-22T03:26:17.000Z",
  "edited": false,
  "text": "Alibaba unveils new AI chip it says is China's most powerful and targets 20 gigawatts of data center capacity by 2032. https://bloom.bg/4ydroys\n\n📷: Qilai Shen/Bloomberg",
  "views": 13400,
  "viewsText": "13.4K",
  "reactionsTotal": 173,
  "reactions": [
    { "emoji": "🔥", "customEmojiId": null, "isPaid": false, "count": 62, "countText": "62" },
    { "emoji": "❤", "customEmojiId": null, "isPaid": false, "count": 33, "countText": "33" },
    { "emoji": "👏", "customEmojiId": null, "isPaid": false, "count": 27, "countText": "27" }
  ],
  "mediaType": "photo",
  "mediaUrls": ["https://cdn5.telesco.pe/file/B-Vjm-tufLB1ZSrW02mb...R7w.jpg"],
  "links": ["https://bloom.bg/4ydroys"],
  "hashtags": [],
  "forwardedFrom": null,
  "replyTo": null
}
```

One channel-info row:

```json
{
  "type": "channel",
  "username": "bloomberg",
  "title": "Bloomberg",
  "description": "The first word in business news.",
  "subscribers": 175000,
  "photos": 800,
  "videos": 49,
  "links": 3180,
  "verified": true,
  "url": "https://t.me/bloomberg",
  "previewAvailable": true
}
```

Posts also carry `photos`, `videos` (URL, thumbnail, duration), `documents` (file name and size), `poll` (question, voters, option percentages), `linkPreview`, `mentions` and `author` when present.

### What the benchmark looks like on that sample

The same 24 Sep 2026 run (last 25 posts per channel), put through the maths in `example.py`:

| Channel | Subscribers | Median views | Views / subscriber | Reactions per 1k views |
|---|---|---|---|---|
| durov | 10,700,000 | 5,720,000 | 53.5% | 17.3 |
| designers | 71,400 | 82,300 | 115.3% | 29.0 |
| bloomberg | 175,000 | 68,300 | 39.0% | 5.6 |
| python_books_archive | 12,400 | 2,660 | 21.5% | 0.6 |

`wallstreetbets` came back with only its channel row and `previewAvailable: false`: it has no public web preview, so there is no post history to read.

## Pricing

Pay per result: **$1.50 per 1,000 results** (a result = one post or one channel-info row). 10,000 posts cost $15. Failed requests and duplicates are not charged. The Apify free plan's $5 monthly credit covers a few thousand posts.

## Limits

- Only **public channels with a web preview**. Private channels, invite links (`t.me/+...`), groups and bots return just the channel row (`previewAvailable: false`).
- **Comments are not included**; Telegram doesn't show discussion-group replies in the preview.
- Custom (premium) emoji reactions come back as a `customEmojiId` with no emoji character; their counts are still right.
- Counts are rounded the way Telegram shows them (`13.4K` -> `13400`); the raw text is kept in `viewsText` / `countText`.
- Very large videos have no direct file URL (`tooLargeForPreview: true`), only thumbnail, duration and post link.
- Media URLs are signed CDN links that expire; download files soon after the run if you need them.

## Daily monitoring tip

Schedule the actor on Apify with `"onlyPostsNewerThan": "1 day"` and deduplicate on `url` (or `channel` + `postId`) to collect only new posts each day.

## Links

- Actor on the Apify Store: https://apify.com/rel8ble/telegram-channel-scraper
- Apify Python client: https://docs.apify.com/api/client/python

## License

MIT (this example code). The actor itself is a paid Apify tool.
