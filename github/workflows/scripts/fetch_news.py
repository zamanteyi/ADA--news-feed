import os
import feedparser
import requests
import re
from datetime import datetime, timezone
from supabase import create_client

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

FEEDS = [
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "source": "TechCrunch"},
    {"url": "https://www.technologyreview.com/feed/", "source": "MIT Technology Review"},
    {"url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml", "source": "The Verge"},
    {"url": "https://wired.com/feed/category/artificial-intelligence/latest/rss", "source": "Wired"},
    {"url": "https://feeds.feedburner.com/venturebeat/SZYF", "source": "VentureBeat"},
    {"url": "https://www.artificialintelligence-news.com/feed/", "source": "AI News"},
]

def fetch_and_store():
    stored = 0
    errors = 0

    existing = supabase.table('ada_news').select('url').execute()
    existing_urls = {row['url'] for row in (existing.data or [])}

    for feed_info in FEEDS:
        try:
            feed = feedparser.parse(feed_info['url'])
            for entry in feed.entries[:5]:
                url = entry.get('link', '')
                if not url or url in existing_urls:
                    continue

                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()

                summary = entry.get('summary', '')
                if summary:
                    summary = re.sub('<[^<]+?>', '', summary)
                    summary = summary[:500].strip()

                row = {
                    'title': entry.get('title', '')[:300],
                    'summary': summary,
                    'source': feed_info['source'],
                    'url': url,
                    'published_at': published,
                    'category': 'AI & Tech'
                }

                supabase.table('ada_news').insert(row).execute()
                existing_urls.add(url)
                stored += 1
                print(f"✅ Stored: {row['title'][:60]}...")

        except Exception as e:
            print(f"❌ Error fetching {feed_info['source']}: {e}")
            errors += 1

    try:
        all_rows = supabase.table('ada_news').select('id').order('created_at', desc=True).execute()
        if all_rows.data and len(all_rows.data) > 200:
            old_ids = [r['id'] for r in all_rows.data[200:]]
            supabase.table('ada_news').delete().in_('id', old_ids).execute()
            print(f"🗑️ Cleaned up {len(old_ids)} old entries")
    except Exception as e:
        print(f"Cleanup error: {e}")

    print(f"\n✅ Done! Stored {stored} new articles. Errors: {errors}")

if __name__ == '__main__':
    fetch_and_store()
