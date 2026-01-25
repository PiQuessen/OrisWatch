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

# --- CURATED DENTISTRY SOURCE LIST (STRICTLY RSS) ---
SOURCE_LIST = [
    # GLOBAL NEWS & MAGAZINES
    "https://www.ada.org/en/publications/ada-news/rss",
    "https://www.dental-tribune.com/feed/",
    "https://www.dentistrytoday.com/feed/",
    "https://www.drbicuspid.com/rss",
    "https://dentistry.co.uk/feed/",
    "https://www.nature.com/bdj/news.rss",
    "https://www.oralhealthgroup.com/feed/",
    "https://groupdentistrynow.com/feed/",
    "https://www.beckersdental.com/rss",
    "https://www.dental-practice.biz/feed/",
    "https://www.the-dentist.co.uk/rss",
    "https://www.dentalreview.news/feed/",
    "https://www.dentaleconomics.com/rss",
    "https://www.rdhmag.com/rss",
    "https://www.perio.org/feed",
    "https://www.aae.org/specialty/feed/",
    "https://www.acp-prosthodontist.org/rss",
    "https://www.aacd.com/news",
    "https://www.speareducation.com/spear-review/rss",
    "https://www.pankey.org/blog/feed/",
    "https://dawsonacademy.com/blog/feed/",
    "https://www.fdiworlddental.org/news",
    "https://www.iadr.org/news",
    "https://www.bda.org/news-centre/rss",
    "https://www.cda-adc.ca/en/rss/news.xml",
    "https://www.dental-update.co.uk/feed",
    "https://www.implantdentistry.com/feed",
    "https://www.orthodonticproductsonline.com/feed/",
    "https://www.sleepreviewmag.com/feed/",
    "https://www.insidedentistry.net/rss",
    "https://www.compendiumlive.com/rss",
    "https://www.dentalproductsreport.com/rss",
    "https://www.dentalcare.com/en-us/rss",
    "https://www.colgateprofessional.com/rss",
    
    # INDIA SPECIFIC (Verified or likely RSS)
    "https://in.dental-tribune.com/feed/",
    "https://dentalreach.today/feed/",
    "https://www.guident.net/feed",
    "https://dentistchannel.online/feed/",
    "https://famdent.com/blog/feed/",
    "https://clovedental.in/blog/feed/",
    "https://sabkadentist.com/blog/feed/",
    "https://parthadental.com/blog/feed/",
    "https://www.dentallife.in/feed",

    # JOURNALS (Elsevier/Wiley/Highwire - Reliable)
    "https://jada.ada.org/current.rss",
    "https://www.jendodon.com/current.rss",
    "https://www.ajodo.org/current.rss",
    "https://www.joms.org/current.rss",
    "https://www.jprosth.org/current.rss",
    "https://www.jpd.org/current.rss",
    "https://www.jdent.org/current.rss",
    "https://www.jdr.org/current.rss",
    "https://www.jperiodontol.org/current.rss",
    "https://www.jco-online.com/rss",
    "https://www.angle.org/rss",
    "https://www.aapd.org/rss",
    "https://www.quintessence-publishing.com/rss",
    "https://www.cochrane.org/rss/oral-health",
    "https://onlinelibrary.wiley.com/feed/1600051x/most-recent", # J Clinical Perio
    "https://onlinelibrary.wiley.com/feed/16000757/most-recent", # Periodontology 2000
    "https://onlinelibrary.wiley.com/feed/16009657/most-recent", # Endodontics
    "https://onlinelibrary.wiley.com/feed/1399302x/most-recent", # Oral Pathology
    "https://onlinelibrary.wiley.com/feed/16000722/most-recent", # Oral Rehab
    "https://onlinelibrary.wiley.com/feed/16016343/most-recent", # Orthodontics
    "https://www.sciencedirect.com/journal/dental-materials/rss",
    "https://www.sciencedirect.com/journal/journal-of-dentistry/rss",
    "https://www.sciencedirect.com/journal/oral-oncology/rss",
    "https://www.sciencedirect.com/journal/archives-of-oral-biology/rss",
    "https://www.sciencedirect.com/journal/international-journal-of-oral-and-maxillofacial-surgery/rss",
    "https://www.sciencedirect.com/journal/journal-of-stomatology-oral-and-maxillofacial-surgery/rss",
    "https://www.sciencedirect.com/journal/operative-dentistry/rss",
    "https://www.sciencedirect.com/journal/journal-of-prosthodontics/rss",
    "https://www.sciencedirect.com/journal/journal-of-public-health-dentistry/rss",
    "https://www.sciencedirect.com/journal/special-care-in-dentistry/rss",
    
    # INDUSTRY & BLOGS
    "https://www.offthecusp.com/feed/",
    "https://teethtalkgirl.com/rss",
    "https://askthedentist.com/feed/",
    "https://www.todaysrdh.com/feed/",
    "https://www.dentalbuzz.com/feed/",
    "https://blog.ultradent.com/rss.xml",
    "https://www.ivoclar.com/en_us/blog/rss",
    "https://www.glidewelldental.com/blog/feed/",
    "https://www.authoritydental.org/feed",
    "https://www.carestack.com/feed/",
    "https://www.planetdds.com/blog/feed/",
    "https://www.benco.com/incisal-edge/feed/",
    "https://www.newmouth.com/feed/",
    "https://www.dentaly.org/us/feed/",
    "https://www.dentalgameplan.com/feed/",
    "https://marketing.dental/feed/",
    "https://www.curvehero.com/blog/rss",
    "https://www.pattersondental.com/blog/feed/"
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

def is_india_context(entry, url):
    """Heuristic to determine if news is Indian."""
    keywords = ["india", "delhi", "mumbai", "ida", "dci", "bengaluru", "chennai", ".in/"]
    
    if ".in" in url and "dental-tribune.com" in url: return True
    if url.endswith(".in") or ".in/" in url: return True
        
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
            
            extracted_data.append({
                "id": link,
                "title": title,
                "link": link,
                "summary": clean_summary(raw_summary),
                "source": source_name,
                "date": pub_date,
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
