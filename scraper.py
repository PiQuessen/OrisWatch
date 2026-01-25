import json
import os
import datetime
import time
import re
import requests
import feedparser
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
DATA_FILE = "data/news.json"

# Robust User Agent handling
try:
    from fake_useragent import UserAgent
    ua = UserAgent()
    def get_random_header():
        return {'User-Agent': ua.random}
except Exception:
    print("[!] 'fake_useragent' failed to initialize. Using fallback.")
    def get_random_header():
        return {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

# --- CURATED DENTISTRY SOURCE LIST (STRICTLY VERIFIED WORKING RSS) ---
SOURCE_LIST = [
    # 1. Top Global News
    "https://www.dental-tribune.com/feed/",
    "https://www.dentistrytoday.com/feed/",
    "https://dentistry.co.uk/feed/",
    "https://www.nature.com/bdj/news.rss",
    "https://groupdentistrynow.com/feed/",
    "https://www.beckersdental.com/rss",
    "https://www.dentalproductsreport.com/rss",
    
    # 2. Specialties & Industry
    "https://www.perio.org/feed",
    "https://www.aae.org/specialty/feed/",
    "https://www.orthodonticproductsonline.com/feed/",
    "https://www.sleepreviewmag.com/feed/",
    
    # 3. High Impact Journals
    "https://jada.ada.org/current.rss",
    "https://www.jendodon.com/current.rss",
    "https://www.ajodo.org/current.rss",
    "https://www.joms.org/current.rss",
    "https://www.jpd.org/current.rss",
    "https://onlinelibrary.wiley.com/feed/1600051x/most-recent", # J Clinical Periodontology

    # 4. India / Regional Context (Verified Working)
    "https://in.dental-tribune.com/feed/",
    "https://health.economictimes.indiatimes.com/rss/dental",
    "https://clovedental.in/blog/feed/"
]

def clean_summary(html_content):
    """Strips HTML tags and truncates summary."""
    if not html_content:
        return "No summary available."
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator=" ")
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:300] + "..." if len(text) > 300 else text
    except Exception:
        return str(html_content)[:300]

def extract_image(entry):
    """Attempts to extract an image URL from an RSS entry."""
    image_url = None
    
    # 1. media:content / media:thumbnail (Standard RSS extensions)
    if 'media_content' in entry:
        for media in entry.media_content:
            if 'image' in media.get('type', '') or 'medium' in media: 
                image_url = media.get('url')
                if image_url: break
    
    if not image_url and 'media_thumbnail' in entry:
        for media in entry.media_thumbnail:
            image_url = media.get('url')
            if image_url: break

    # 2. Enclosures (Podcasts/Standard attachments)
    if not image_url and 'links' in entry:
        for link in entry.links:
            if link.get('rel') == 'enclosure':
                 href = link.get('href', '')
                 # Basic check if it looks like an image
                 if any(ext in href.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                     image_url = href
                     break

    # 3. Description/Content HTML parsing (Fall back to scraping the HTML)
    if not image_url:
        html_content = ''
        if 'content' in entry:
             html_content = entry.content[0].value
        elif 'summary' in entry: 
             html_content = entry.summary
        
        if html_content:
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                img = soup.find('img')
                if img and img.get('src'):
                    image_url = img.get('src')
            except:
                pass
                
    return image_url

def is_india_context(entry, url):
    """Heuristic to determine if news is Indian."""
    keywords = ["india", "delhi", "mumbai", "ida", "dci", "bengaluru", "chennai", ".in/"]
    
    if ".in" in url and "dental-tribune.com" in url: return True
    if url.endswith(".in") or ".in/" in url: return True
    if "indiatimes" in url: return True
        
    content = (entry.get('title', '') + entry.get('summary', '')).lower()
    for kw in keywords:
        if kw in content:
            return True
    return False

def scrape_feed(url):
    """Scrapes a single RSS feed."""
    print(f"Scraping: {url}")
    try:
        response = requests.get(url, headers=get_random_header(), timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to fetch {url}: Status {response.status_code}")
            return []

        feed = feedparser.parse(response.content)
        
        extracted_data = []
        source_name = feed.feed.get('title', url.split('//')[-1].split('/')[0])
        
        for entry in feed.entries:
            link = entry.get('link', '')
            if not link: continue
            
            title = entry.get('title', 'No Title')
            
            raw_summary = entry.get('description', '')
            if 'content' in entry and len(entry.content) > 0:
                 raw_summary = entry.content[0].get('value', raw_summary)
            
            pub_date = entry.get('published', entry.get('updated', datetime.datetime.now().isoformat()))
            
            is_india = is_india_context(entry, link)
            image_url = extract_image(entry)
            
            extracted_data.append({
                "id": link,
                "title": title,
                "link": link,
                "summary": clean_summary(raw_summary),
                "source": source_name,
                "date": pub_date,
                "image": image_url,
                "category": "INDIA_TRANSMISSION" if is_india else "GLOBAL_FEED",
                "scraped_at": datetime.datetime.now().isoformat()
            })
            
            # RESTRICTION: Only take the latest item per source
            break
            
        return extracted_data
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

def main():
    existing_data = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                content = f.read()
                if content.strip():
                    existing_data = json.loads(content)
        except json.JSONDecodeError:
            print(f"[!] Warning: {DATA_FILE} corrupted, starting fresh.")
            existing_data = []
    
    existing_ids = {item['id'] for item in existing_data}
    
    # Use only the strict list
    full_source_list = SOURCE_LIST
    
    new_items = []
    
    print(f"[*] Starting scrape job for {len(full_source_list)} sources...")
    for source in full_source_list:
        feed_items = scrape_feed(source)
        for item in feed_items:
            if item['id'] not in existing_ids:
                new_items.append(item)
                existing_ids.add(item['id'])
    
    print(f"[*] Scraped {len(new_items)} new items.")
    
    all_data = new_items + existing_data
    all_data = all_data[:2000]
    
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(all_data, f, indent=2)
        print("[*] Data saved successfully.")
    except Exception as e:
        print(f"[!] Critical Error saving data: {e}")

if __name__ == "__main__":
    main()
