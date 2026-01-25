import json
import os
import datetime
import time
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urlparse

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

# --- EXTENDED SOURCE LIST (200+ SOURCES) ---
SOURCE_LIST = [
    # GLOBAL NEWS & MAGAZINES
    "https://www.ada.org/en/publications/ada-news/rss", "https://www.dental-tribune.com/feed/",
    "https://www.dentistrytoday.com/feed/", "https://www.drbicuspid.com/rss",
    "https://dentistry.co.uk/feed/", "https://www.nature.com/bdj/news.rss",
    "https://www.oralhealthgroup.com/feed/", "https://groupdentistrynow.com/feed/",
    "https://www.beckersdental.com/rss", "https://www.dental-practice.biz/feed/",
    "https://www.the-dentist.co.uk/rss", "https://www.dentalreview.news/feed/",
    "https://www.dentaleconomics.com/rss", "https://www.rdhmag.com/rss",
    "https://www.perio.org/feed", "https://www.aae.org/specialty/feed/",
    "https://www.acp-prosthodontist.org/rss", "https://www.aacd.com/news",
    "https://www.speareducation.com/spear-review/rss", "https://www.pankey.org/blog/feed/",
    "https://dawsonacademy.com/blog/feed/", "https://www.fdiworlddental.org/news",
    "https://www.iadr.org/news", "https://www.bda.org/news-centre/rss",
    "https://www.cda-adc.ca/en/rss/news.xml", "https://www.dha.gov.ae/en/rss",
    "https://www.dental-update.co.uk/feed", "https://www.implantdentistry.com/feed",
    "https://www.orthodonticproductsonline.com/feed/", "https://www.sleepreviewmag.com/feed/",
    "https://www.insidedentistry.net/rss", "https://www.compendiumlive.com/rss",
    "https://www.dentistssalary.com/feed/", "https://www.dentalproductsreport.com/rss",
    "https://www.dentalplans.com/blog/feed/", "https://www.1800dentist.com/blog/feed/",
    "https://www.aspendental.com/blog/rss", "https://www.heartland.com/blog/rss",
    "https://www.pacificdental.com/news/rss", "https://www.smilebrands.com/news/rss",
    "https://www.clearchoice.com/blog/feed/", "https://www.westerndental.com/blog/feed/",
    "https://www.interdent.com/blog/feed/", "https://www.decadental.com/blog/feed/",
    "https://www.greatexpressions.com/blog/feed/", "https://www.dentalcare.com/en-us/rss",
    "https://www.colgateprofessional.com/rss", "https://www.listerine.com/rss",

    # INDIA NEWS & PORTALS
    "https://in.dental-tribune.com/feed/", "https://dentalreach.today/feed/",
    "https://www.guident.net/feed", "https://dentistchannel.online/feed/",
    "https://famdent.com/blog/feed/", "https://www.ida.org.in/News",
    "https://www.dental-practice.biz/xml/rss.php", "https://www.biospectrumindia.com/rss/dental",
    "https://health.economictimes.indiatimes.com/rss/dental", "https://www.expresshealthcare.in/tag/dental/feed",
    "https://www.medgatetoday.com/category/dental/feed", "https://www.cims.co.in/category/dental/feed",
    "https://www.practo.com/healthfeed/dental/feed", "https://www.lybrate.com/topic/dental-health/feed",
    "https://pharmeasy.in/blog/category/dental-care/feed/", "https://www.1mg.com/articles/category/dental-care/feed",
    "https://www.apollo247.com/blog/category/dental/feed", "https://clovedental.in/blog/feed/",
    "https://sabkadentist.com/blog/feed/", "https://parthadental.com/blog/feed/",
    "https://www.myclove.in/feed", "https://www.smilesfiles.com/feed",
    "https://www.dentallife.in/feed", "https://www.indianhealthguru.com/dental-feed",
    "https://www.medindia.net/rss/dental.xml", "https://www.webmd.com/oral-health/rss",
    "https://www.onlymyhealth.com/rss/dental-health", "https://www.thehealthsite.com/diseases-conditions/dental-health/feed",
    "https://timesofindia.indiatimes.com/rssfeeds/11368686.cms",
    "https://www.news18.com/rss/health-wellness.xml", "https://www.hindustantimes.com/rss/lifestyle/health",
    "https://www.dnaindia.com/feeds/health.xml", "https://www.firstpost.com/rss/health.xml",
    "https://www.deccanherald.com/rss/lifestyle/health-and-well-being", "https://www.tribuneindia.com/rss/feed/health",
    
    # GLOBAL JOURNALS
    "https://jada.ada.org/current.rss", "https://www.jendodon.com/current.rss",
    "https://www.ajodo.org/current.rss", "https://www.joms.org/current.rss",
    "https://www.jprosth.org/current.rss", "https://www.jpd.org/current.rss",
    "https://www.jdent.org/current.rss", "https://www.jdr.org/current.rss",
    "https://www.jperiodontol.org/current.rss", "https://www.jco-online.com/rss",
    "https://www.angle.org/rss", "https://www.aapd.org/rss",
    "https://www.quintessence-publishing.com/rss", "https://www.cochrane.org/rss/oral-health",
    "https://onlinelibrary.wiley.com/feed/1600051x/most-recent",
    "https://onlinelibrary.wiley.com/feed/16000757/most-recent",
    "https://onlinelibrary.wiley.com/feed/16009657/most-recent",
    "https://onlinelibrary.wiley.com/feed/1399302x/most-recent",
    "https://onlinelibrary.wiley.com/feed/16000722/most-recent",
    "https://onlinelibrary.wiley.com/feed/16016343/most-recent",
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

    # INDIAN INSTITUTIONS (Direct links - Scraper handles HTML fallback if supported or adds RSS patterns)
    "https://maids.ac.in/news", "https://manipal.edu/mcods-manipal/news-events.html",
    "https://saveetha.com/dental/news", "https://www.kgmu.org/news",
    "https://bapujidental.edu/events", "https://absmids.nitte.edu.in/events",
    "https://sdmcds.org/news", "https://amrita.edu/school/dentistry/news",
    "https://srmdental.ac.in/news", "https://jssuni.edu.in/JSSWeb/Dental/News",
    "https://klesdentalb.edu.in/news", "https://yenepoya.edu.in/news",
    "https://mgmch.org/news", "https://www.sriramachandra.edu.in/news",
    "https://vspmdcrc.edu.in/news", "https://gdcmumbai.org/news",
    "https://gdcchennai.ac.in/news", "https://gdckolkata.ac.in/news",
    "https://gdcahmedabad.org/news", "https://gdcindore.mp.gov.in/news",
    "https://gdcjammu.org/news", "https://gdcpatna.org/news",
    "https://gdchyd.telangana.gov.in/news", "https://gdcsm.org/news",
    "https://www.its.edu.in/dental/news", "https://www.saraswathidental.com/news",
    "https://www.santosh.ac.in/dental-college/news", "https://www.subharti.org/dental/news",
    "https://www.sharda.ac.in/schools/dental-sciences/news", "https://www.tmudental.edu.in/news",
    "https://www.bhu.ac.in/ims/dental/news", "https://www.amu.ac.in/department/dental/news",
    "https://www.jmi.ac.in/dentistry/news", "https://www.du.ac.in/index.php?page=dental-sciences",
    "https://www.pu.ac.in/dental/news", "https://www.bfuhs.ac.in/dental/news",
    "https://www.uhsr.ac.in/dental/news", "https://www.ruhsraj.org/dental/news",
    "https://www.muhs.ac.in/dental/news", "https://www.nqr.gov.in/dental/news",
    "https://dciindia.gov.in/News", "https://www.mohfw.gov.in/dental/news",
    "https://main.mohfw.gov.in/dental/news", "https://www.nhp.gov.in/dental/news",
    "https://www.india.gov.in/dental/news", "https://www.mygov.in/dental/news"
]

# Base domains for discovery algorithm (Extracted from Institution list)
COLLEGE_DOMAINS = [
    "https://maids.ac.in", "https://manipal.edu", "https://saveetha.com",
    "https://www.kgmu.org", "https://bapujidental.edu", "https://absmids.nitte.edu.in",
    "https://sdmcds.org", "https://amrita.edu", "https://srmdental.ac.in",
    "https://jssuni.edu.in", "https://klesdentalb.edu.in", "https://yenepoya.edu.in",
    "https://mgmch.org", "https://www.sriramachandra.edu.in", "https://vspmdcrc.edu.in",
    "https://gdcmumbai.org", "https://gdcchennai.ac.in", "https://gdckolkata.ac.in",
    "https://gdcahmedabad.org", "https://gdcindore.mp.gov.in", "https://gdcjammu.org",
    "https://gdcpatna.org", "https://gdchyd.telangana.gov.in", "https://gdcsm.org",
    "https://www.its.edu.in", "https://www.saraswathidental.com", "https://www.santosh.ac.in",
    "https://www.subharti.org", "https://www.sharda.ac.in", "https://www.tmudental.edu.in",
    "https://www.bhu.ac.in", "https://www.amu.ac.in", "https://www.jmi.ac.in",
    "https://www.du.ac.in", "https://www.pu.ac.in", "https://www.bfuhs.ac.in",
    "https://www.uhsr.ac.in", "https://www.ruhsraj.org", "https://www.muhs.ac.in",
    "https://www.nqr.gov.in", "https://dciindia.gov.in", "https://www.mohfw.gov.in",
    "https://main.mohfw.gov.in", "https://www.nhp.gov.in", "https://www.india.gov.in",
    "https://www.mygov.in"
]

def discover_new_sources():
    """
    Programmatically generates potential news URLs from college domains
    and adds them to the source list if they haven't been checked recently.
    """
    discovery_patterns = ["/news", "/events", "/press-release", "/rss.xml", "/feed", "/blog/feed"]
    new_sources = []
    
    print(f"[*] Running Source Discovery on {len(COLLEGE_DOMAINS)} domains...")
    
    for domain in COLLEGE_DOMAINS:
        for pattern in discovery_patterns:
            url = f"{domain.rstrip('/')}{pattern}"
            if url not in SOURCE_LIST:
                new_sources.append(url)
    
    return new_sources

def clean_summary(html_content):
    """Strips HTML tags and truncates summary."""
    if not html_content:
        return "No summary available."
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator=" ")
        text = re.sub(r'\s+', ' ', text).strip() # Clean extra whitespace
        return text[:300] + "..." if len(text) > 300 else text
    except Exception:
        return str(html_content)[:300]

def is_india_context(entry, url):
    """Heuristic to determine if news is Indian."""
    keywords = ["india", "delhi", "mumbai", "ida", "dci", "bengaluru", "chennai", ".in/"]
    
    # Check TLD
    if ".in" in url and "dental-tribune.com" in url: return True # Explicit check
    if url.endswith(".in") or ".in/" in url:
        return True
        
    # Check content
    content = (entry.get('title', '') + entry.get('summary', '')).lower()
    for kw in keywords:
        if kw in content:
            return True
    return False

def scrape_feed(url):
    """Scrapes a single RSS feed."""
    print(f"Scraping: {url}")
    try:
        # Using the robust header getter
        response = requests.get(url, headers=get_random_header(), timeout=10)
        
        # Simple fix for feeds that might return 403 without user agent
        if response.status_code != 200:
            print(f"Failed to fetch {url}: Status {response.status_code}")
            return []

        # Feedparser can parse the XML string directly
        feed = feedparser.parse(response.content)
        
        # Basic check if it's a valid feed
        if not feed.entries and feed.bozo:
             print(f"Bozo exception (invalid XML?) for {url}: {feed.bozo_exception}")
             # In a real expanded version, we might fall back to soup here for HTML pages
             return []

        extracted_data = []
        source_name = feed.feed.get('title', url.split('//')[-1].split('/')[0])
        
        for entry in feed.entries:
            link = entry.get('link', '')
            if not link: continue
            
            title = entry.get('title', 'No Title')
            
            # Robust summary extraction
            raw_summary = entry.get('description', '')
            if 'content' in entry and len(entry.content) > 0:
                 raw_summary = entry.content[0].get('value', raw_summary)
            
            pub_date = entry.get('published', entry.get('updated', datetime.datetime.now().isoformat()))
            
            is_india = is_india_context(entry, link)
            
            extracted_data.append({
                "id": link, # Use link as unique ID
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
    # 1. Load existing data
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
    
    # Create a set of existing IDs for fast deduplication
    existing_ids = {item['id'] for item in existing_data}
    
    # 2. Prepare Source List
    full_source_list = SOURCE_LIST + discover_new_sources()
    
    new_items = []
    
    # 3. Scrape Loop
    print(f"[*] Starting scrape job for {len(full_source_list)} sources...")
    for source in full_source_list:
        feed_items = scrape_feed(source)
        for item in feed_items:
            if item['id'] not in existing_ids:
                new_items.append(item)
                existing_ids.add(item['id'])
    
    print(f"[*] Scraped {len(new_items)} new items.")
    
    # 4. Merge and Sort
    # Put new items at the top
    all_data = new_items + existing_data
    
    # Limit total size to keep JSON manageable (e.g., last 2000 items)
    all_data = all_data[:2000]
    
    # 5. Save
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(all_data, f, indent=2)
        print("[*] Data saved successfully.")
    except Exception as e:
        print(f"[!] Critical Error saving data: {e}")

if __name__ == "__main__":
    main()